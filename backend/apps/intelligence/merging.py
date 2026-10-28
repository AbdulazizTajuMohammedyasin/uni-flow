"""Step 5 of the pipeline (docs/12-intelligence.md): merge duplicates.

The same announcement is often forwarded to many groups. Before a new insight is saved,
it is compared with the insights of the same kind from the last RECENT_DAYS:
- timetable changes: the same course, sections, date and the same new day/time/room
  (so "moved to 2 PM" and "moved to 3 PM" stay separate: a conflict is never hidden);
- other information: the same link, or else the same date and a similar title.
A match gets the new message as extra evidence (and the higher of the two confidences)
instead of a second insight, so students see it once.
"""

import re
from datetime import date, timedelta

from django.utils import timezone

from apps.publishing.models import Status
from apps.timetable.models import ClassChange

from .delivery import deliver
from .models import UNSURE, Insight, InsightEvidence, Message
from .services import publish_insight

RECENT_DAYS = 14
SIMILAR = 0.6  # share of title words in common (two dated items)
SIMILAR_UNDATED = 0.75  # stricter when neither has a date
SMALL_WORDS = {"the", "and", "for", "with", "your", "you", "are", "all", "has", "will", "from"}


def timetable_key(kind: str, data: dict) -> str:
    """Everything that makes a timetable change the same change."""
    parts = [
        kind,
        data.get("course_code", ""),
        ",".join(str(i) for i in sorted(data.get("section_ids") or [])),
        data.get("date", ""),
        data.get("new_date", ""),
        data.get("new_start", ""),
        data.get("new_end", ""),
        data.get("new_room", "").casefold(),
    ]
    return "|".join(parts)[:200]


def is_held(data: dict) -> bool:
    """A timetable change that waits for an admin: its course is unknown, or the message
    names a section the course doesn't have this term."""
    return data.get("course_id") is None or bool(
        data.get("section") and not data.get("section_ids")
    )


def link_key(kind: str, link: str) -> str:
    """The same link means the same opportunity or notice (blank without a link)."""
    if not link:
        return ""
    return f"{kind}|{link.strip().rstrip('/').casefold()}"[:200]


def _title_words(title: str) -> set[str]:
    words = re.sub(r"[^\w\s]", " ", title.casefold()).split()
    return {word for word in words if len(word) > 2 and word not in SMALL_WORDS}


def similar_titles(first: str, second: str, needed: float = SIMILAR) -> bool:
    """Most of the words are the same ("Petronas internship" / "Petronas Internship Offer")."""
    a, b = _title_words(first), _title_words(second)
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= needed


def _day(insight: Insight) -> date | None:
    moment = insight.deadline_at or insight.starts_at
    return timezone.localtime(moment).date() if moment else None


def _plain_names(names) -> set[str]:
    return {" ".join(re.sub(r"[^\w\s]", " ", str(n).casefold()).split()) for n in names} - {""}


def _same_who(candidate: Insight, names: list[str], course_ids: set[int]) -> bool:
    """Two requests are the same only when they name the same students, and items for
    different courses are never the same (Assignment 1 of two courses, due the same day)."""
    if candidate.kind == Insight.Kind.DIRECT_REQUEST:
        if _plain_names(candidate.data.get("names") or []) != _plain_names(names):
            return False
    theirs = set(candidate.audience.courses.values_list("id", flat=True))
    return not (theirs and course_ids and not theirs & course_ids)


def find_duplicate(
    *,
    kind: str,
    merge_key: str,
    title: str,
    day: date | None,
    names: list[str] = (),
    course_ids: set[int] = frozenset(),
) -> Insight | None:
    """The recent insight this one repeats, or None. `names` (a request's students) and
    `course_ids` (the courses it is for) must not differ from the insight's."""
    recent = Insight.objects.filter(
        origin=Insight.Origin.AI,
        kind=kind,
        created_at__gte=timezone.now() - timedelta(days=RECENT_DAYS),
    ).exclude(status=Status.ARCHIVED)  # a retracted insight isn't brought back this way
    if kind in ClassChange.Kind.values:  # timetable changes only ever merge on the exact key
        return (
            recent.filter(merge_key=merge_key).order_by("created_at").first() if merge_key else None
        )
    if merge_key:
        for candidate in recent.filter(merge_key=merge_key).order_by("created_at"):
            if _same_who(candidate, names, course_ids):
                return candidate
        recent = recent.filter(merge_key="")  # a different link is different information
    needed = SIMILAR if day else SIMILAR_UNDATED
    for candidate in recent.order_by("created_at"):
        if (
            _day(candidate) == day
            and similar_titles(candidate.title, title, needed)
            and _same_who(candidate, names, course_ids)
        ):
            return candidate
    return None


def add_evidence(
    insight: Insight,
    evidence: list[tuple[Message, str]],
    confidence: float,
    *,
    merge_key: str = "",
    link: str = "",
) -> Insight:
    """The forwarded copy becomes more proof for the insight UniFlow already has. If the
    copy has a link the insight lacked, the insight takes it (so an announcement with a
    different link is then never merged into it)."""
    for message, quote in evidence:
        InsightEvidence.objects.get_or_create(
            insight=insight, message=message, defaults={"quote": quote[:500]}
        )
    insight.confidence = max(insight.confidence, confidence)
    if merge_key and not insight.merge_key:
        insight.merge_key, insight.link = merge_key, link or insight.link
    insight.save(update_fields=["confidence", "merge_key", "link", "updated_at"])
    # A draft that was only too unsure is published once another group confirms it. A
    # timetable change whose course is unknown keeps waiting for an admin.
    held = insight.kind in ClassChange.Kind.values and is_held(insight.data)
    if insight.status == Status.DRAFT and insight.confidence >= UNSURE and not held:
        publish_insight(insight, None)
    else:
        # The copy's group members get it in their feed, but no alert: a forwarded copy
        # is the same information, not news (docs/07).
        before = set(insight.deliveries.values_list("id", flat=True))
        deliver(insight)
        insight.deliveries.exclude(id__in=before).update(notified_at=timezone.now())
    return insight
