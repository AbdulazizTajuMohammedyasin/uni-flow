"""The home screen in one request (M9.1): same visibility as the feed, few queries."""

from datetime import UTC, date, datetime, time

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import Course, School, Term
from apps.accounts import semesters
from apps.accounts.models import UserRole
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.intelligence.models import Delivery, Insight, InsightEvidence, Message, Source
from apps.notifications.models import Notification
from apps.publishing.models import Status
from apps.timetable.models import ClassChange, ClassMeeting, CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

HOME = "/api/v1/feed/home/"


@pytest.fixture(autouse=True)
def today(monkeypatch):
    monkeypatch.setattr(semesters, "today", lambda: date(2026, 10, 5))  # a Monday


@pytest.fixture
def ali():
    """A student with a Monday class, a class change waiting, items and an unread alert."""
    term = Term.objects.create(
        name="T1",
        academic_session="2026/2027",
        number=1,
        starts_on=date(2026, 9, 28),
        ends_on=date(2027, 1, 29),
    )
    school = School.objects.create(code="SCI", name="Computing")
    course = Course.objects.create(school=school, code="CDE2313", name="Data Structures")
    section = CourseSection.objects.create(course=course, term=term, code="A")
    ClassMeeting.objects.create(
        section=section, weekday=0, start_time=time(10), end_time=time(12), room="B2"
    )
    user = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    SectionEnrollment.objects.create(user=user, section=section)

    for number, tier in enumerate(["direct", "action", "important", "digest", "digest"] * 2):
        deliver(user, f"{tier} {number}", tier)
    change_insight = deliver(user, "CDE2313 moved", "important", kind="class_moved")
    group = Source.objects.create(platform="manual", title="CDE2313 A")
    message = Message.objects.create(
        source=group, external_id="m1", text="Moved", sent_at=datetime(2026, 10, 5, tzinfo=UTC)
    )
    InsightEvidence.objects.create(insight=change_insight, message=message, quote="Moved")
    ClassChange.objects.create(
        insight=change_insight,
        section=section,
        kind="class_moved",
        date=date(2026, 10, 12),
        new_start=time(14),
        new_end=time(16),
    )
    Notification.objects.create(recipient=user, kind="digest", title="Your daily digest")
    return user


def deliver(user, title, tier, kind="academic_notice"):
    insight = Insight.objects.create(
        audience=Audience.objects.create(),
        origin=Insight.Origin.AI,
        kind=kind,
        title=title,
        summary="…",
        confidence=0.9,
        status=Status.PUBLISHED,
        published_at=timezone.now(),
    )
    Delivery.objects.create(insight=insight, user=user, relevance=80, tier=tier, reason="Because")
    return insight


def test_the_home_screen_in_one_request(ali, django_assert_max_num_queries):
    api = APIClient()
    api.force_authenticate(ali)

    with django_assert_max_num_queries(15):
        body = api.get(HOME).json()

    assert [item["tier"] for item in body["direct"]] == ["direct", "direct"]
    assert len(body["action"]) == 2
    assert {item["title"] for item in body["important"]} >= {"CDE2313 moved"}
    assert len(body["digest_preview"]) == 3  # a preview only
    [lesson] = body["todays_classes"]
    assert (lesson["course_code"], lesson["start_time"], lesson["room"]) == (
        "CDE2313",
        "10:00",
        "B2",
    )
    [change] = body["pending_timetable_changes"]
    assert (change["course_code"], change["my_status"], change["new_start"]) == (
        "CDE2313",
        "pending",
        "14:00",
    )
    assert change["evidence"][0]["quote"] == "Moved"
    assert body["unread_notifications"] == 1


def test_same_visibility_as_the_feed(ali):
    retracted = Insight.objects.get(title="direct 0")
    retracted.status = Status.ARCHIVED
    retracted.save()
    Delivery.objects.filter(insight__title="direct 5").update(dismissed_at=timezone.now())

    sara = create_user("sara@student.aiu.edu.my", "Str0ng-pass-99", full_name="Sara")
    api = APIClient()
    api.force_authenticate(ali)
    assert api.get(HOME).json()["direct"] == []  # retracted and dismissed are hidden

    api.force_authenticate(sara)
    body = api.get(HOME).json()
    assert body["important"] == [] and body["pending_timetable_changes"] == []
    assert body["unread_notifications"] == 0


def test_staff_get_an_empty_timetable_part():
    lee = create_user("lee@aiu.edu.my", "Str0ng-pass-99", full_name="Lee", role=UserRole.LECTURER)
    api = APIClient()
    api.force_authenticate(lee)
    body = api.get(HOME).json()
    assert body["todays_classes"] == [] and body["pending_timetable_changes"] == []
    assert APIClient().get(HOME).status_code == 401
