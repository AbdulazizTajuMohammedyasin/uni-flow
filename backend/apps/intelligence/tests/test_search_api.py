"""Search (M9.2): only ever the caller's own deliveries."""

from datetime import UTC, datetime, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.intelligence.models import Delivery, Insight, InsightEvidence, Message, Source
from apps.publishing.models import Status

pytestmark = pytest.mark.django_db

SEARCH = "/api/v1/feed/search/"


def login(email):
    user = create_user(email, "Str0ng-pass-99", full_name=email)
    api = APIClient()
    api.force_authenticate(user)
    return user, api


def deliver(user, title, summary="…", minutes=0, **fields):
    insight = Insight.objects.create(
        audience=Audience.objects.create(),
        origin=Insight.Origin.AI,
        kind="internship",
        title=title,
        summary=summary,
        status=Status.PUBLISHED,
        **({"published_at": timezone.now() + timedelta(minutes=minutes)} | fields),
    )
    Delivery.objects.create(insight=insight, user=user, relevance=60, tier="digest", reason="…")
    return insight


def titles(api, q):
    return [item["title"] for item in api.get(SEARCH, {"q": q}).json()["results"]]


def test_finds_my_items_by_words_newest_first():
    ali, api = login("ali@student.aiu.edu.my")
    deliver(ali, "Petronas internship", "Apply by 20 Oct.", minutes=1)
    deliver(ali, "Shell internship fair", "In the Main Hall.", minutes=2, location="Main Hall")
    deliver(ali, "Hackathon", "Register by Friday.")

    assert titles(api, "internship") == ["Shell internship fair", "Petronas internship"]
    assert titles(api, "PETRONAS internship") == ["Petronas internship"]  # every word, any case
    assert titles(api, "main hall") == ["Shell internship fair"]  # summary or place
    assert titles(api, "register") == ["Hackathon"]
    assert titles(api, "scholarship") == []


def test_searches_the_quoted_original_messages_too():
    ali, api = login("ali@student.aiu.edu.my")
    insight = deliver(ali, "Industry visit")
    group = Source.objects.create(platform="manual", title="SCI")
    message = Message.objects.create(
        source=group, external_id="m", text="", sent_at=datetime(2026, 10, 5, tzinfo=UTC)
    )
    InsightEvidence.objects.create(
        insight=insight, message=message, quote="Bus leaves from Block C"
    )
    assert titles(api, "block c") == ["Industry visit"]


def test_read_and_dismissed_items_are_found_but_retracted_and_expired_are_not():
    ali, api = login("ali@student.aiu.edu.my")
    deliver(ali, "Petronas read")
    deliver(ali, "Petronas dismissed")
    Delivery.objects.filter(insight__title="Petronas read").update(read_at=timezone.now())
    Delivery.objects.filter(insight__title="Petronas dismissed").update(dismissed_at=timezone.now())
    retracted = deliver(ali, "Petronas retracted")
    retracted.status = Status.ARCHIVED
    retracted.save()
    deliver(
        ali,
        "Petronas expired",
        published_at=timezone.now() - timedelta(days=3),
        expires_at=timezone.now() - timedelta(days=1),
    )

    assert sorted(titles(api, "petronas")) == ["Petronas dismissed", "Petronas read"]


def test_never_returns_items_delivered_to_someone_else():
    ali, _ = login("ali@student.aiu.edu.my")
    _, sara = login("sara@student.aiu.edu.my")
    deliver(ali, "Ali, please see Dr Lee")
    Insight.objects.create(  # published but delivered to nobody
        audience=Audience.objects.create(),
        kind="academic_notice",
        title="Dr Lee notice",
        summary="…",
        status=Status.PUBLISHED,
        published_at=timezone.now(),
    )
    assert titles(sara, "Dr Lee") == []


def test_at_least_two_characters():
    _, api = login("ali@student.aiu.edu.my")
    assert api.get(SEARCH, {"q": "a"}).status_code == 400
    assert api.get(SEARCH).status_code == 400
    assert APIClient().get(SEARCH, {"q": "petronas"}).status_code == 401
