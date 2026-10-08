"""The same information forwarded to many groups becomes one insight (M7.3)."""

from datetime import UTC, datetime, timedelta
from itertools import count

import pytest
from django.utils import timezone

from apps.intelligence.extraction import extract_source
from apps.intelligence.merging import similar_titles
from apps.intelligence.models import Insight, Message, Source
from apps.intelligence.providers import fake_provider
from apps.intelligence.services import retract_insight
from apps.publishing.models import Status

pytestmark = pytest.mark.django_db

SENT = datetime(2026, 10, 5, 1, 0, tzinfo=UTC)
NUMBERS = count(1)


def group(title):
    return Source.objects.create(platform="manual", title=title)


def post(source, text):
    return Message.objects.create(
        source=source,
        external_id=f"m{next(NUMBERS)}",
        sender_name="Career Office",
        text=text,
        sent_at=SENT,
        triage=Message.Triage.RELEVANT,
    )


def item(message, **fields):
    return {
        "kind": "competition",
        "title": "Hackathon registration closes Friday",
        "summary": "Register for the AIU hackathon by Friday.",
        "importance": 60,
        "deadline": "2026-10-09",
        "link": "",
        "confidence": 0.9,
        "evidence": [{"message_id": message.id, "quote": message.text}],
    } | fields


def change(message, **fields):
    return {
        "kind": "class_cancelled",
        "course_code": "CDE2313",
        "date": "2026-10-06",
        "title": "Class cancelled",
        "summary": "No CDE2313 class tomorrow.",
        "confidence": 0.9,
        "evidence": [{"message_id": message.id, "quote": message.text}],
    } | fields


def found(source, *items, changes=()):
    fake_provider().answers.append({"changes": list(changes), "items": list(items)})
    extract_source(source)


def test_a_forwarded_copy_adds_evidence_not_a_new_insight():
    first, second = group("SCI Year 1"), group("SCI Year 2")
    original = post(first, "Hackathon registration closes Friday!")
    forwarded = post(second, "Fwd: Hackathon registration closes Friday!")

    found(first, item(original))
    found(second, item(forwarded, title="Hackathon Registration Closing Friday", confidence=0.95))

    insight = Insight.objects.get()
    assert {e.message for e in insight.evidence.all()} == {original, forwarded}
    assert insight.confidence == 0.95  # the higher of the two


def test_the_same_link_is_the_same_opportunity():
    first, second = group("A"), group("B")
    link = "https://careers.example.com/petronas/"
    found(
        first,
        item(post(first, "Petronas internship"), kind="internship", title="Petronas", link=link),
    )
    found(
        second,
        item(
            post(second, "Internship!"), kind="internship", title="Apply now", link=link.rstrip("/")
        ),
    )
    assert Insight.objects.count() == 1


def test_different_information_stays_separate():
    source = group("SCI")
    found(
        source,
        item(post(source, "Hackathon closes Friday")),
        item(post(source, "Hackathon closes Monday"), deadline="2026-10-12"),  # another date
        item(post(source, "Debate contest Friday"), title="Debate competition registration"),
        item(post(source, "Hackathon (link)"), link="https://a.example/x"),
        item(post(source, "Other hackathon (link)"), link="https://b.example/y"),
    )
    # The first item takes link A from its copy; link B is then different information.
    assert Insight.objects.count() == 4
    assert Insight.objects.filter(link="https://a.example/x").count() == 1


def test_a_conflicting_timetable_change_is_never_hidden():
    first, second = group("CDE2313 A"), group("CDE2313 B")
    found(
        first,
        changes=[change(post(first, "Class moved to 2pm"), kind="class_moved", new_start="14:00")],
    )
    found(
        second,
        changes=[change(post(second, "Class moved to 2pm"), kind="class_moved", new_start="14:00")],
    )
    found(
        second,
        changes=[change(post(second, "Moved to 3pm"), kind="class_moved", new_start="15:00")],
    )

    starts = sorted(Insight.objects.values_list("data__new_start", flat=True))
    assert starts == ["14:00", "15:00"]  # 2pm twice = one insight; 3pm stays separate


def test_a_second_group_confirms_an_unsure_draft():
    first, second = group("A"), group("B")
    found(first, item(post(first, "hackathon maybe friday?"), confidence=0.3))
    assert Insight.objects.get().status == Status.DRAFT

    found(second, item(post(second, "Hackathon closes Friday, confirmed."), confidence=0.85))

    insight = Insight.objects.get()
    assert (insight.status, insight.confidence) == (Status.PUBLISHED, 0.85)


def test_old_or_retracted_insights_are_not_reused():
    first, second = group("A"), group("B")
    found(first, item(post(first, "Hackathon closes Friday")))
    old = Insight.objects.get()
    Insight.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=15))
    found(second, item(post(second, "Hackathon closes Friday again")))
    assert Insight.objects.count() == 2

    retract_insight(Insight.objects.latest("created_at"), None)
    third = group("C")
    found(third, item(post(third, "Hackathon closes Friday!!")))
    assert Insight.objects.count() == 3


@pytest.mark.parametrize(
    ("first", "second", "same"),
    [
        ("Petronas internship", "Petronas Internship Offer", True),
        ("Hackathon registration closes Friday", "Registration for hackathon closes Friday", True),
        ("Hackathon registration", "Debate registration", False),
        ("", "Anything", False),
    ],
)
def test_similar_titles(first, second, same):
    assert similar_titles(first, second) is same
