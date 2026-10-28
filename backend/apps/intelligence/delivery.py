"""Step 6 of the pipeline (docs/12-intelligence.md): who gets an insight, how relevant it is
to each of them, which level of their feed it goes in, and why. Plain code, no AI.

1. Who can get it at all:
   - the students named in it (mentions);
   - a request to named students: those students only. It is about them, so nobody else
     sees it, not even in the digest (and nobody at all if no name could be matched);
   - a timetable change: the students of the affected sections or course;
   - anything else: the students it is for (its audience) and the members of the groups
     it came from. An AI insight for "nobody in particular" goes to those members only,
     never to every student; a staff post for "all students" does reach everyone.
2. Relevance 0-100 for each of them, from the strongest reason (named 100, your section
   90, your course 85, your group 80, your programme 65, intake 60, school 55, …), then
   +10 for a matching interest, +10 for a kind of information they asked for, and -40
   for a kind they switched off.
3. The level (tier): named -> Direct attention; a change to your own class -> Important;
   an unsure AI insight -> Digest only; must act -> Action required; importance 70+ ->
   Important; otherwise Digest. Below DIGEST relevance it isn't shown to that student.
Running it again (more evidence, a new mention) updates the score but never undoes
"read" or "dismissed".
4. Alerts (M8.2): Direct attention, Action required and Important alert right away (once
   per student and insight); the Digest waits for the daily digest (M8.3): one alert
   each evening per student who has new Digest items.
"""

from collections import defaultdict
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.academics.models import Term
from apps.accounts import semesters
from apps.accounts.models import Interest, User, UserRole
from apps.audiences.selectors import students_matching
from apps.notifications.models import Notification, NotificationKind
from apps.notifications.services import send
from apps.publishing.models import Status
from apps.timetable.models import ClassChange, SectionEnrollment

from .models import Delivery, Insight, SourceMember

RELEVANT = 50  # needed for "Action required" and "Important update"
DIGEST = 30  # below this the student doesn't see it
IMPORTANT = 70  # importance needed for "Important update"


@dataclass
class Facts:
    """What is known about an insight, loaded once for all its students."""

    mentioned: set[int]
    in_section: dict[int, str]  # student id -> "CDE2313 Section A"
    takes_course: dict[int, str]  # student id -> "CDE2313"
    group_member: dict[int, str]  # student id -> group title
    in_audience: set[int]
    schools: set[int]
    programmes: set[int]
    intakes: set[int]
    has_semesters: bool
    for_everyone: bool


def _current_term_ids() -> list[int]:
    today = semesters.today()
    terms = [Term.current(calendar, today) for calendar in Term.Calendar.values]
    return [term.id for term in terms if term]


def _facts(insight: Insight) -> Facts:
    audience = insight.audience
    sections = SectionEnrollment.objects.filter(section__in=audience.sections.all())
    courses = SectionEnrollment.objects.filter(
        section__course__in=audience.courses.all(), section__term_id__in=_current_term_ids()
    )
    groups = {e.message.source for e in insight.evidence.select_related("message__source")}
    if insight.publisher_source_id:
        groups.add(insight.publisher_source)
    members = SourceMember.objects.filter(source__in=groups).select_related("source")
    lists = {
        name: set(getattr(audience, name).values_list("id", flat=True))
        for name in ("schools", "programmes", "intakes", "courses", "sections")
    }
    has_semesters = audience.semester_min is not None or audience.semester_max is not None
    for_everyone = not any(lists.values()) and not has_semesters
    return Facts(
        mentioned=set(insight.mentions.values_list("user_id", flat=True)),
        in_section={
            e.user_id: f"{e.section.course.code} Section {e.section.code}"
            for e in sections.select_related("section__course")
        },
        takes_course={
            e.user_id: e.section.course.code for e in courses.select_related("section__course")
        },
        group_member={m.user_id: m.source.title for m in members},
        in_audience=set()
        if for_everyone
        else set(students_matching(audience).values_list("id", flat=True)),
        schools=lists["schools"],
        programmes=lists["programmes"],
        intakes=lists["intakes"],
        has_semesters=has_semesters,
        for_everyone=for_everyone,
    )


def is_timetable(insight: Insight) -> bool:
    return insight.kind in ClassChange.Kind.values


def candidates(insight: Insight, facts: Facts):
    """The students who can get this insight at all."""
    students = User.objects.filter(role=UserRole.STUDENT, is_active=True, is_suspended=False)
    if insight.kind == Insight.Kind.DIRECT_REQUEST:
        ids = set()  # only the named students (added below)
    elif is_timetable(insight):
        ids = set(facts.in_section) | set(facts.takes_course) | facts.in_audience
    elif facts.for_everyone and insight.origin == Insight.Origin.AI:
        ids = set(facts.group_member)  # "nobody in particular": only the group's members
    elif facts.for_everyone:
        return students.select_related("student_profile")  # a staff post for everyone
    else:
        ids = facts.in_audience | set(facts.group_member)
    return students.filter(pk__in=ids | facts.mentioned).select_related(
        "student_profile__school", "student_profile__programme", "student_profile__intake"
    )


def relevance(insight: Insight, user: User, facts: Facts) -> tuple[int, str]:
    """(score 0-100, the reason shown to the student)."""
    if user.id in facts.mentioned:
        return 100, "You were named in this message"
    profile = user.student_profile
    reasons = [(40, "For all students")] if facts.for_everyone else []
    if user.id in facts.in_section:
        reasons.append((90, f"You are in {facts.in_section[user.id]}"))
    if user.id in facts.takes_course:
        reasons.append((85, f"You take {facts.takes_course[user.id]}"))
    if user.id in facts.group_member:
        reasons.append((80, f'You are in the group "{facts.group_member[user.id]}"'))
    if user.id in facts.in_audience:
        if profile.programme_id in facts.programmes:
            reasons.append((65, f"For {profile.programme.name} students"))
        if profile.intake_id in facts.intakes:
            reasons.append((60, f"For the {profile.intake.name} intake"))
        if profile.school_id in facts.schools:
            reasons.append((55, f"For {profile.school.name} students"))
        if facts.has_semesters:
            reasons.append((55, "For students in your semester"))
    score, reason = max(reasons, default=(0, ""))

    shared = [topic for topic in insight.topics if topic in profile.interests]
    if shared:
        score += 10
        if score < 60 or not reason:
            reason = f"Matches your interest: {Interest(shared[0]).label}"
    if insight.info_type and profile.info_types:  # empty preferences mean "everything"
        score += 10 if insight.info_type in profile.info_types else -40
    return max(0, min(score, 100)), reason


def tier(insight: Insight, user: User, score: int, facts: Facts) -> str | None:
    """The level of the student's feed, or None (not shown to this student)."""
    if user.id in facts.mentioned:
        return Delivery.Tier.DIRECT
    if is_timetable(insight) and (user.id in facts.in_section or user.id in facts.takes_course):
        return Delivery.Tier.IMPORTANT  # a change to your own class always matters
    if score < DIGEST:
        return None
    if insight.is_unconfirmed and not is_timetable(insight):
        return Delivery.Tier.DIGEST  # the AI wasn't sure: digest only, "Not confirmed"
    if insight.action_required and score >= RELEVANT:
        return Delivery.Tier.ACTION
    if insight.importance >= IMPORTANT and score >= RELEVANT:
        return Delivery.Tier.IMPORTANT
    return Delivery.Tier.DIGEST


def deliver(insight: Insight) -> int:
    """Create or update the deliveries of a published insight. Returns how many students
    get it. Safe to run again: read and dismissed stay as they were."""
    if insight.status != Status.PUBLISHED:
        return 0
    facts = _facts(insight)
    delivered = 0
    for user in candidates(insight, facts):
        score, reason = relevance(insight, user, facts)
        level = tier(insight, user, score, facts)
        if level is None:
            continue
        Delivery.objects.update_or_create(
            insight=insight,
            user=user,
            defaults={"relevance": score, "tier": level, "reason": reason[:200]},
        )
        delivered += 1
    return delivered


# --- Alerts (M8.2, docs/07-notifications.md) ---------------------------------------------

# Levels that alert right away; the Digest waits for the daily digest (M8.3).
IMMEDIATE = {
    Delivery.Tier.DIRECT: NotificationKind.DIRECT_ATTENTION,
    Delivery.Tier.ACTION: NotificationKind.ACTION_REQUIRED,
    Delivery.Tier.IMPORTANT: NotificationKind.IMPORTANT_UPDATE,
}


def notify_deliveries(insight: Insight) -> int:
    """Alert the students whose delivery is Direct attention, Action required or Important
    and who haven't been alerted about this insight yet. A class change to confirm gets
    its own kind. Each delivery is claimed (notified_at) so it never alerts twice."""
    if insight.status != Status.PUBLISHED:
        return 0
    with transaction.atomic():
        waiting = list(
            Delivery.objects.select_for_update().filter(
                insight=insight, notified_at__isnull=True, tier__in=list(IMMEDIATE)
            )
        )
        if not waiting:
            return 0
        alerts = [
            Notification(
                recipient_id=delivery.user_id,
                kind=NotificationKind.TIMETABLE_CHANGE_PROPOSED
                if is_timetable(insight) and delivery.tier == Delivery.Tier.IMPORTANT
                else IMMEDIATE[delivery.tier],
                title=insight.title[:200],
                body=insight.summary[:500],
                target_type="insight",
                target_id=insight.id,
                dedupe_key=f"ins:{insight.id}:u:{delivery.user_id}",
            )
            for delivery in waiting
        ]
        send(alerts)
        Delivery.objects.filter(pk__in=[d.pk for d in waiting]).update(notified_at=timezone.now())
    return len(alerts)


def notify_retraction(insight: Insight) -> int:
    """A class change was taken back: tell the students who were alerted about it."""
    if not is_timetable(insight):
        return 0
    alerted = Delivery.objects.filter(insight=insight, notified_at__isnull=False)
    send(
        [
            Notification(
                recipient_id=delivery.user_id,
                kind=NotificationKind.TIMETABLE_CHANGE_RETRACTED,
                title=f"Taken back: {insight.title}"[:200],
                body="This class change was taken back. Your timetable is as before.",
                target_type="insight",
                target_id=insight.id,
                dedupe_key=f"ins:{insight.id}:retract:u:{delivery.user_id}",
            )
            for delivery in alerted
        ]
    )
    return alerted.count()


def queue_notifications(insight: Insight) -> None:
    """Send the alerts in the background, once the current save is committed."""
    from .functions import INSIGHT_DELIVERED, send  # functions imports this module

    transaction.on_commit(lambda: send(INSIGHT_DELIVERED, insight_id=insight.id))


# --- The daily digest (M8.3) ----------------------------------------------------------------


def _digest_title(count: int) -> str:
    return f"Your daily digest: {count} new item" + ("s" if count > 1 else "")


def send_daily_digests(now=None) -> int:
    """Every evening: one alert per student summing up their new Digest items (only if
    there are any), then those items are marked as included (digested_at). Returns how
    many students got a digest. At most one per student per day (dedupe key)."""
    now = now or timezone.now()
    day = timezone.localdate(now)
    with transaction.atomic():
        waiting = list(
            Delivery.objects.select_for_update()
            .filter(
                Q(insight__expires_at__isnull=True) | Q(insight__expires_at__gt=now),
                tier=Delivery.Tier.DIGEST,
                digested_at__isnull=True,
                dismissed_at__isnull=True,
                feedback="",
                insight__status=Status.PUBLISHED,
            )
            .select_related("insight")
            .order_by("user_id", "-insight__importance", "-id")
        )
        by_student: dict[int, list[Delivery]] = defaultdict(list)
        for delivery in waiting:
            by_student[delivery.user_id].append(delivery)
        send(
            [
                Notification(
                    recipient_id=user_id,
                    kind=NotificationKind.DIGEST,
                    title=_digest_title(len(items)),
                    body=" · ".join(item.insight.title for item in items[:3])[:500],
                    target_type="digest",
                    target_id=int(day.strftime("%Y%m%d")),  # opens /digest?date=...
                    dedupe_key=f"dig:{day.isoformat()}:u:{user_id}",
                )
                for user_id, items in by_student.items()
            ]
        )
        Delivery.objects.filter(pk__in=[d.pk for d in waiting]).update(digested_at=now)
    return len(by_student)
