"""Other information found in messages (M7.1): opportunities, notices, requests."""

from datetime import UTC, datetime, timedelta

import pytest

from apps.academics.models import Programme, School
from apps.intelligence.extraction import INFO_KINDS, INFO_TYPE, extract_source
from apps.intelligence.models import Insight, Message, Source
from apps.intelligence.providers import fake_provider
from apps.publishing.models import Status

pytestmark = pytest.mark.django_db

SENT = datetime(2026, 10, 5, 1, 0, tzinfo=UTC)  # Monday 5 Oct 2026, 09:00 in Malaysia


@pytest.fixture
def group():
    return Source.objects.create(platform="manual", title="SCI Year 2")


def add(group, text, minutes=0, **fields):
    return Message.objects.create(
        source=group,
        external_id=f"{text[:20]}-{minutes}",
        sender_name="Career Office",
        text=text,
        sent_at=SENT + timedelta(minutes=minutes),
        triage=Message.Triage.RELEVANT,
        **fields,
    )


def item(message, **fields):
    return {
        "kind": "internship",
        "title": "Petronas internship",
        "summary": "Petronas is taking 3rd-year interns; apply by 20 Oct.",
        "importance": 70,
        "action_required": True,
        "action_text": "Apply online",
        "deadline": "2026-10-20",
        "starts_at": "",
        "location": "",
        "link": "https://careers.example.com/apply",
        "topics": ["software_engineering", "data_science"],
        "confidence": 0.9,
        "evidence": [{"message_id": message.id, "quote": message.text}],
    } | fields


def answer(*items):
    return {"changes": [], "items": list(items)}


def test_an_internship_with_its_details(group):
    school = School.objects.create(code="SCI", name="Computing")
    bcs = Programme.objects.create(code="BCS", school=school, name="CS", level="bachelor")
    posted = add(group, "Petronas internship for BCS Year 3, apply by 20 Oct: careers.example.com")
    fake_provider().answers.append(
        answer(item(posted, programme_codes=["bcs"], semester_min=7, semester_max=9))
    )

    assert extract_source(group) == 1

    found = Insight.objects.get()
    assert (found.kind, found.info_type) == ("internship", "internship")
    assert found.status == Status.PUBLISHED
    assert (found.importance, found.action_required) == (70, True)
    assert found.action_text == "Apply online"
    assert found.deadline_at == datetime(2026, 10, 19, 16, 0, tzinfo=UTC)  # 20 Oct, Malaysia
    assert found.link == "https://careers.example.com/apply"
    assert found.topics == ["software_engineering", "data_science"]
    assert list(found.audience.programmes.all()) == [bcs]
    assert (found.audience.semester_min, found.audience.semester_max) == (7, 9)
    assert [e.message for e in found.evidence.all()] == [posted]

    [asked] = fake_provider().calls
    assert "PART 2" in asked["instructions"]
    assert "Topics to choose from: ai, data_science" in asked["prompt"]
    assert set(asked["schema"]["required"]) == {"changes", "items"}


@pytest.mark.parametrize("kind", INFO_KINDS)
def test_every_kind_is_saved_with_its_info_type(group, kind):
    posted = add(group, f"A message about a {kind}")
    fake_provider().answers.append(answer(item(posted, kind=kind, title=f"A {kind}")))

    extract_source(group)

    found = Insight.objects.get()
    assert (found.kind, found.info_type) == (kind, INFO_TYPE[kind])


def test_a_request_to_named_students(group):
    posted = add(group, "Ali and Sara, please see me after class about your project.")
    fake_provider().answers.append(
        answer(item(posted, kind="direct_request", title="See Dr Lee", names=["Ali", "Sara"]))
    )

    extract_source(group)

    assert Insight.objects.get().data["names"] == ["Ali", "Sara"]


def test_without_an_audience_the_groups_own_scope_is_used(group):
    school = School.objects.create(code="SCI", name="Computing")
    group.school = school
    group.save()
    posted = add(group, "Hostel inspection on Friday 10am.")
    fake_provider().answers.append(
        answer(item(posted, kind="student_affairs", starts_at="2026-10-09 10:00"))
    )

    extract_source(group)

    found = Insight.objects.get()
    assert list(found.audience.schools.all()) == [school]
    assert found.starts_at == datetime(2026, 10, 9, 2, 0, tzinfo=UTC)


def test_unknown_codes_mean_no_audience_from_the_message(group):
    posted = add(group, "Talk for XYZ students")
    fake_provider().answers.append(answer(item(posted, school_codes=["XYZ"])))
    extract_source(group)
    audience = Insight.objects.get().audience
    assert not audience.schools.exists() and audience.semester_min is None  # everyone


def test_invalid_answers_are_rejected_or_cleaned(group):
    posted = add(group, "Scholarship open")
    fake_provider().answers.append(
        answer(
            item(posted, kind="party"),  # not a kind
            item(posted, evidence=[{"message_id": 999999, "quote": "made up"}]),
            item(posted, title=""),
            item(posted, confidence="very"),
            "not an item",
            item(
                posted,
                kind="scholarship",
                link="javascript:alert(1)",
                topics=["ai", "astrology"],
                importance=500,
                deadline="soon",
                semester_min=0,
                names=["Ali"],  # only kept for direct_request
            ),
        )
    )

    assert extract_source(group) == 1

    found = Insight.objects.get()
    assert (found.link, found.topics, found.importance) == ("", ["ai"], 100)
    assert found.deadline_at is None
    assert found.audience.semester_min is None
    assert found.data["names"] == []


def test_a_reply_to_an_older_message_is_shown_for_context(group):
    old = add(group, "Assignment 2 is due next week.", minutes=-3 * 24 * 60)
    Message.objects.filter(pk=old.pk).update(extracted_at=SENT)
    reply = add(group, "Extended to Friday!", reply_to=old)
    fake_provider().answers.append(answer())

    extract_source(group)

    [asked] = fake_provider().calls
    assert f"[{old.id}]" in asked["prompt"]  # older than the 24-hour window
    line = f"* [{reply.id}] Career Office (Mon 05/10/2026 09:00) (reply to [{old.id}])"
    assert line in asked["prompt"]


def test_timetable_changes_and_other_information_in_one_request(group):
    posted = add(group, "No CDE2313 class tomorrow. Also: hackathon registration closes Friday.")
    change = {
        "kind": "class_cancelled",
        "course_code": "XYZ999",  # unknown: kept as a draft
        "date": "2026-10-06",
        "title": "Class cancelled",
        "summary": "No class tomorrow.",
        "confidence": 0.9,
        "evidence": [{"message_id": posted.id, "quote": "No CDE2313 class tomorrow."}],
    }
    fake_provider().answers.append(
        {"changes": [change], "items": [item(posted, kind="competition", title="Hackathon")]}
    )

    assert extract_source(group) == 2
    assert len(fake_provider().calls) == 1
    kinds = sorted(Insight.objects.values_list("kind", flat=True))
    assert kinds == ["class_cancelled", "competition"]
