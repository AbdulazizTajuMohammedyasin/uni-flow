"""Alerts for deliveries (M8.2): only immediate levels, never twice, not for merged copies."""

from datetime import UTC, date, datetime

import pytest
from django.utils import timezone

from apps.academics.models import Course, Intake, Programme, School, Term
from apps.accounts import semesters
from apps.accounts.services import create_user
from apps.intelligence import merging
from apps.intelligence.delivery import notify_deliveries
from apps.intelligence.mentions import record_mentions
from apps.intelligence.models import Delivery, Message, Source, SourceMember
from apps.intelligence.services import retract_insight, save_ai_insight
from apps.notifications.models import Notification
from apps.timetable.models import CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def today(monkeypatch):
    monkeypatch.setattr(semesters, "today", lambda: date(2026, 10, 5))


@pytest.fixture
def uni():
    term = Term.objects.create(
        name="T1",
        academic_session="2026/2027",
        number=1,
        starts_on=date(2026, 9, 28),
        ends_on=date(2027, 1, 29),
    )
    sci = School.objects.create(code="SCI", name="School of Computing")
    bcs = Programme.objects.create(
        code="BCS", school=sci, name="Computer Science", level="bachelor"
    )
    intake = Intake.objects.create(code="2025-OCT", name="Oct 2025", start_date=date(2025, 10, 1))
    course = Course.objects.create(school=sci, code="CDE2313", name="Data Structures")
    section = CourseSection.objects.create(course=course, term=term, code="A")
    group = Source.objects.create(platform="manual", title="SCI Year 2")
    people = {}
    for name in ("Ali Hassan", "Sara Lim"):
        user = create_user(
            f"{name.split()[0].lower()}@student.aiu.edu.my", "Str0ng-pass-99", full_name=name
        )
        profile = user.student_profile
        profile.school, profile.programme, profile.intake = sci, bcs, intake
        profile.save()
        people[name.split()[0].lower()] = user
    SourceMember.objects.create(source=group, user=people["ali"])
    SectionEnrollment.objects.create(user=people["ali"], section=section)
    return {"group": group, "bcs": bcs, "course": course, "section": section, **people}


def found(uni, capture, kind="academic_notice", confidence=0.9, **fields):
    message = Message.objects.create(
        source=uni["group"],
        external_id=f"m{Message.objects.count()}",
        sender_name="Office",
        text="…",
        sent_at=datetime(2026, 10, 5, 1, tzinfo=UTC),
    )
    with capture(execute=True):  # the alerts are sent once the save is committed
        return save_ai_insight(
            source=uni["group"],
            kind=kind,
            title="Title",
            summary="Summary.",
            confidence=confidence,
            evidence=[(message, "…")],
            **fields,
        )


def alerts():
    """{first name: kind}"""
    return {
        n.recipient.full_name.split()[0].lower(): n.kind
        for n in Notification.objects.select_related("recipient")
    }


def test_important_and_action_alert_right_away(uni, django_capture_on_commit_callbacks):
    important = found(
        uni,
        django_capture_on_commit_callbacks,
        audience={"programmes": [uni["bcs"]]},
        importance=80,
    )
    assert alerts() == {"ali": "important_update", "sara": "important_update"}
    alert = Notification.objects.get(recipient=uni["sara"])
    assert (alert.title, alert.body, alert.target_type, alert.target_id) == (
        "Title",
        "Summary.",
        "insight",
        important.id,
    )

    Notification.objects.all().delete()
    found(
        uni, django_capture_on_commit_callbacks, kind="deadline", importance=40,
        audience={"programmes": [uni["bcs"]]}, action_required=True,
    )  # fmt: skip
    assert alerts() == {"ali": "action_required", "sara": "action_required"}


def test_the_digest_waits(uni, django_capture_on_commit_callbacks):
    notice = found(
        uni,
        django_capture_on_commit_callbacks,
        audience={"programmes": [uni["bcs"]]},
        importance=30,
    )
    assert Delivery.objects.filter(insight=notice).count() == 2
    assert alerts() == {}
    assert not Delivery.objects.filter(notified_at__isnull=False).exists()


def test_never_twice(uni, django_capture_on_commit_callbacks):
    important = found(
        uni,
        django_capture_on_commit_callbacks,
        audience={"programmes": [uni["bcs"]]},
        importance=80,
    )
    assert notify_deliveries(important) == 0  # already claimed
    Delivery.objects.update(notified_at=None)  # even if the claim were lost…
    notify_deliveries(important)
    assert Notification.objects.count() == 2  # …the same alert isn't stored twice


def test_being_named_later_alerts(uni, django_capture_on_commit_callbacks):
    notice = found(uni, django_capture_on_commit_callbacks, importance=30)  # Ali's digest
    assert alerts() == {}
    with django_capture_on_commit_callbacks(execute=True):
        record_mentions(notice, ["Ali Hassan"], uni["group"])
    assert alerts() == {"ali": "direct_attention"}


def test_a_merged_copy_alerts_nobody(uni, django_capture_on_commit_callbacks):
    important = found(uni, django_capture_on_commit_callbacks, importance=80)  # Ali only
    other = Source.objects.create(platform="manual", title="Year 2 friends")
    SourceMember.objects.create(source=other, user=uni["sara"])
    copy = Message.objects.create(
        source=other, external_id="fwd", text="Fwd", sent_at=timezone.now()
    )

    with django_capture_on_commit_callbacks(execute=True):
        merging.add_evidence(important, [(copy, "Fwd")], 0.9)

    assert Delivery.objects.filter(insight=important, user=uni["sara"]).exists()  # in her feed
    assert alerts() == {"ali": "important_update"}  # but no alert for the copy


def test_a_class_change_to_confirm_and_its_retraction(uni, django_capture_on_commit_callbacks):
    change = found(
        uni,
        django_capture_on_commit_callbacks,
        kind="class_moved",
        audience={"sections": [uni["section"]]},
        importance=80,
        data={"section_ids": [uni["section"].id], "date": "2026-10-06", "new_start": "14:00"},
    )
    assert alerts() == {"ali": "timetable_change_proposed"}

    with django_capture_on_commit_callbacks(execute=True):
        retract_insight(change, None)

    kinds = sorted(Notification.objects.values_list("kind", flat=True))
    assert kinds == ["timetable_change_proposed", "timetable_change_retracted"]


def test_drafts_alert_nobody(uni, django_capture_on_commit_callbacks):
    found(
        uni, django_capture_on_commit_callbacks, confidence=0.3,
        audience={"programmes": [uni["bcs"]]}, importance=90,
    )  # fmt: skip
    assert alerts() == {}
