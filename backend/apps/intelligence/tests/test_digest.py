"""The daily digest (M8.3): one per student per day, only if there is something new."""

from datetime import UTC, datetime, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.intelligence import functions
from apps.intelligence.delivery import send_daily_digests
from apps.intelligence.models import Delivery, Insight
from apps.notifications.models import Notification
from apps.publishing.models import Status

pytestmark = pytest.mark.django_db

EVENING = datetime(2026, 10, 9, 11, 0, tzinfo=UTC)  # Fri 9 Oct, 19:00 in Malaysia
NEXT_EVENING = EVENING + timedelta(days=1)


def student(email):
    return create_user(email, "Str0ng-pass-99", full_name=email)


def item(user, title, tier="digest", importance=30, **fields):
    insight = Insight.objects.create(
        audience=Audience.objects.create(),
        origin=Insight.Origin.AI,
        kind="student_affairs",
        info_type=fields.pop("info_type", "student_affairs"),
        title=title,
        summary="…",
        importance=importance,
        status=Status.PUBLISHED,
        published_at=EVENING - timedelta(hours=5),
        **fields,
    )
    return Delivery.objects.create(
        insight=insight, user=user, relevance=60, tier=tier, reason="Because"
    )


def test_one_digest_per_student_with_their_new_items():
    ali, sara = student("ali@student.aiu.edu.my"), student("sara@student.aiu.edu.my")
    item(ali, "Library open late", importance=20)
    item(ali, "Hackathon next month", importance=50)
    item(ali, "Club fair", importance=40)
    item(ali, "Bus timetable", importance=10)
    item(ali, "Class moved", tier="important")  # alerted right away instead (M8.2)
    item(sara, "Hostel inspection")

    assert send_daily_digests(EVENING) == 2

    digest = Notification.objects.get(recipient=ali)
    assert (digest.kind, digest.title) == ("digest", "Your daily digest: 4 new items")
    assert digest.body == "Hackathon next month · Club fair · Library open late"  # top 3
    assert (digest.target_type, digest.target_id) == ("digest", 20261009)
    assert Notification.objects.get(recipient=sara).title == "Your daily digest: 1 new item"
    assert not Delivery.objects.filter(tier="digest", digested_at__isnull=True).exists()


def test_nothing_new_means_no_digest():
    ali = student("ali@student.aiu.edu.my")
    item(ali, "Library open late")
    send_daily_digests(EVENING)

    assert send_daily_digests(NEXT_EVENING) == 0  # already in yesterday's digest
    assert Notification.objects.count() == 1


def test_never_two_digests_on_the_same_day():
    ali = student("ali@student.aiu.edu.my")
    item(ali, "Library open late")
    send_daily_digests(EVENING)
    item(ali, "Club fair")  # arrives later the same evening

    send_daily_digests(EVENING + timedelta(minutes=30))

    assert Notification.objects.filter(recipient=ali).count() == 1


def test_dismissed_retracted_and_expired_items_are_left_out():
    ali = student("ali@student.aiu.edu.my")
    dismissed = item(ali, "Dismissed")
    dismissed.dismissed_at = EVENING
    dismissed.save()
    not_for_me = item(ali, "Not for me")
    not_for_me.feedback = Delivery.Feedback.NOT_RELEVANT
    not_for_me.save()
    retracted = item(ali, "Retracted")
    Insight.objects.filter(pk=retracted.insight_id).update(status=Status.ARCHIVED)
    item(ali, "Expired", expires_at=EVENING - timedelta(hours=1))

    assert send_daily_digests(EVENING) == 0
    assert Notification.objects.count() == 0


def test_the_digest_page_lists_that_days_items():
    ali = student("ali@student.aiu.edu.my")
    item(ali, "Old news")
    send_daily_digests(EVENING - timedelta(days=1))
    item(ali, "Internship fair", importance=50, info_type="internship")
    item(ali, "Library open late", importance=20)
    send_daily_digests(EVENING)

    api = APIClient()
    api.force_authenticate(ali)
    latest = api.get("/api/v1/feed/digest/").json()
    assert latest["date"] == "2026-10-09"
    assert [(i["title"], i["info_type"]) for i in latest["items"]] == [
        ("Internship fair", "internship"),
        ("Library open late", "student_affairs"),
    ]
    earlier = api.get("/api/v1/feed/digest/", {"date": "2026-10-08"}).json()
    assert [i["title"] for i in earlier["items"]] == ["Old news"]
    assert api.get("/api/v1/feed/digest/", {"date": "Friday"}).status_code == 400


def test_no_digest_yet():
    api = APIClient()
    api.force_authenticate(student("ali@student.aiu.edu.my"))
    assert api.get("/api/v1/feed/digest/").json() == {"date": None, "items": []}


def test_the_evening_job(monkeypatch):
    ali = student("ali@student.aiu.edu.my")
    item(ali, "Library open late")
    monkeypatch.setattr(timezone, "now", lambda: EVENING)
    assert functions.send_daily_digest() == 1
