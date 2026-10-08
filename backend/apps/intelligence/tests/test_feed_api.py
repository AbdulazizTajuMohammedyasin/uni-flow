"""The "For you" feed API (M7.5): only my own deliveries."""

from datetime import UTC, datetime, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.intelligence.models import (
    Delivery,
    Insight,
    InsightEvidence,
    Message,
    Source,
)
from apps.intelligence.services import retract_insight
from apps.publishing.models import Status

pytestmark = pytest.mark.django_db

FEED = "/api/v1/feed/"


def login(email):
    user = create_user(email, "Str0ng-pass-99", full_name=email)
    api = APIClient()
    api.force_authenticate(user)
    return user, api


def item(user, tier="digest", minutes=0, title=None, **fields):
    """An insight delivered to `user` at `tier`."""
    insight = Insight.objects.create(
        audience=Audience.objects.create(),
        origin=Insight.Origin.AI,
        kind=fields.pop("kind", "academic_notice"),
        title=title or f"{tier} {minutes}",
        summary="Summary.",
        confidence=fields.pop("confidence", 0.9),
        status=Status.PUBLISHED,
        published_at=timezone.now() + timedelta(minutes=minutes),
        **fields,
    )
    Delivery.objects.create(insight=insight, user=user, relevance=80, tier=tier, reason="Because")
    return insight


def test_my_feed_in_order_and_by_level():
    ali, api = login("ali@student.aiu.edu.my")
    item(ali, "digest", 3)
    item(ali, "important", 1)
    item(ali, "direct", 0)
    item(ali, "important", 2)
    item(ali, "action", 0)

    titles = [entry["title"] for entry in api.get(FEED).json()["results"]]
    assert titles == ["direct 0", "action 0", "important 2", "important 1", "digest 3"]

    only = api.get(FEED, {"tier": "important"}).json()
    assert [entry["title"] for entry in only["results"]] == ["important 2", "important 1"]
    assert api.get(FEED, {"tier": "urgent"}).status_code == 400


def test_an_item_looks_like_this():
    ali, api = login("ali@student.aiu.edu.my")
    item(
        ali, "action", title="Apply for Petronas", action_required=True, action_text="Apply",
        link="https://careers.example.com", confidence=0.7,
    )  # fmt: skip
    [entry] = api.get(FEED).json()["results"]
    assert entry["tier"] == "action"
    assert entry["reason"] == "Because"
    assert (entry["action_required"], entry["action_text"]) == (True, "Apply")
    assert (entry["not_confirmed"], entry["official"], entry["read"]) == (True, False, False)


def test_the_detail_shows_the_original_messages():
    ali, api = login("ali@student.aiu.edu.my")
    insight = item(ali, "important")
    channel = Source.objects.create(
        platform="telegram_channel", external_id="-1001234", title="AIU Notices"
    )
    message = Message.objects.create(
        source=channel,
        external_id="42",
        sender_name="Registrar",
        text="Exam timetable is out.",
        sent_at=datetime(2026, 10, 5, 1, tzinfo=UTC),
        raw={"chat": {"username": "aiunotices"}},
    )
    InsightEvidence.objects.create(insight=insight, message=message, quote="Exam timetable is out.")

    body = api.get(f"{FEED}{insight.id}/").json()

    [evidence] = body["evidence"]
    assert evidence["group"] == {
        "id": channel.id,
        "platform": "telegram_channel",
        "title": "AIU Notices",
    }
    assert (evidence["sender_name"], evidence["quote"]) == ("Registrar", "Exam timetable is out.")
    assert evidence["open_url"] == "https://t.me/aiunotices/42"
    assert body["timetable_change"] is None


def test_read_dismiss_and_not_relevant():
    ali, api = login("ali@student.aiu.edu.my")
    first, second, third = item(ali), item(ali, minutes=1), item(ali, minutes=2)

    assert api.post(f"{FEED}{first.id}/read/").status_code == 204
    assert api.post(f"{FEED}{second.id}/dismiss/").status_code == 204
    response = api.post(f"{FEED}{third.id}/feedback/", {"feedback": "not_relevant"}, format="json")
    assert response.status_code == 204

    [shown] = api.get(FEED).json()["results"]
    assert (shown["id"], shown["read"]) == (first.id, True)
    assert Delivery.objects.get(insight=third).feedback == "not_relevant"
    assert api.get(f"{FEED}{second.id}/").json()["dismissed"] is True  # still openable
    bad = api.post(f"{FEED}{first.id}/feedback/", {"feedback": "boring"}, format="json")
    assert bad.status_code == 400


def test_only_my_own_items():
    ali, _ = login("ali@student.aiu.edu.my")
    _, sara = login("sara@student.aiu.edu.my")
    mine = item(ali, "direct")

    assert sara.get(FEED).json()["results"] == []
    for path in ("", "read/", "dismiss/"):
        method = sara.get if path == "" else sara.post
        assert method(f"{FEED}{mine.id}/{path}").status_code == 404
    assert APIClient().get(FEED).status_code == 401


def test_retracted_and_expired_items_disappear():
    ali, api = login("ali@student.aiu.edu.my")
    retracted = item(ali, minutes=1)
    item(ali, minutes=-180, expires_at=timezone.now() - timedelta(hours=1))  # expired
    kept = item(ali, minutes=0)

    retract_insight(retracted, None)

    assert [entry["id"] for entry in api.get(FEED).json()["results"]] == [kept.id]
    assert api.get(f"{FEED}{retracted.id}/").status_code == 404
