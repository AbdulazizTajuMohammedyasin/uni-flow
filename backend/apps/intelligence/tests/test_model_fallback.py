"""Falling back to the next model when one is used up or busy (free tier)."""

from datetime import UTC, datetime

import pytest
from django.core.cache import cache

from apps.intelligence import providers
from apps.intelligence.extraction import extract_source
from apps.intelligence.models import Insight, Message, Source
from apps.intelligence.providers import AIBusy, AIRateLimited, ask, fake_provider

QUESTION = {"instructions": "…", "prompt": "…", "schema": {}}


@pytest.fixture(autouse=True)
def three_models(settings):
    settings.AI_SMART_MODELS = ["smart-a", "smart-b", "smart-c"]


def models_asked():
    return [call["model"] for call in fake_provider().calls]


def test_the_first_model_answers_when_it_can():
    fake_provider().answers.append({"ok": True})
    answer = ask("smart", **QUESTION)
    assert (answer.data, answer.model) == ({"ok": True}, "smart-a")


def test_a_used_up_model_hands_over_and_rests_as_long_as_google_says():
    fake_provider().answers.extend([AIRateLimited("429", retry_after=49332), {"ok": True}])

    answer = ask("smart", **QUESTION)

    assert answer.model == "smart-b"
    assert cache.get("ai-resting:smart-a")  # not asked again until it can answer
    fake_provider().answers.append({"again": True})
    assert ask("smart", **QUESTION).model == "smart-b"
    assert models_asked() == ["smart-a", "smart-b", "smart-b"]


def test_a_busy_model_hands_over_too():
    fake_provider().answers.extend([AIBusy("503 high demand"), {"ok": True}])
    assert ask("smart", **QUESTION).model == "smart-b"


def test_when_every_model_is_used_up_the_job_waits():
    fake_provider().answers.extend(
        [
            AIRateLimited("429", retry_after=600),
            AIBusy("503"),
            AIRateLimited("429", retry_after=3600),
        ]
    )
    with pytest.raises(AIRateLimited) as raised:
        ask("smart", **QUESTION)
    assert raised.value.retry_after == 60  # the soonest one back (the busy one)

    with pytest.raises(AIRateLimited):  # all resting: nothing is asked
        ask("smart", **QUESTION)
    assert len(fake_provider().calls) == 3


def test_other_problems_are_not_hidden():
    fake_provider().answers.append(providers.AIError("bad key"))
    with pytest.raises(providers.AIError):
        ask("smart", **QUESTION)
    assert models_asked() == ["smart-a"]  # a bad key isn't a reason to try the others


def test_googles_retry_delay_is_read():
    message = "429 RESOURCE_EXHAUSTED. {... 'retryDelay': '49332s'}]}}"
    assert providers._retry_after(message) == 49332
    assert providers._retry_after("429 too many requests") is None


@pytest.mark.django_db
def test_the_model_that_answered_is_recorded_on_insights():
    group = Source.objects.create(platform="manual", title="SCI")
    message = Message.objects.create(
        source=group,
        external_id="m",
        text="Hackathon on Friday",
        sent_at=datetime(2026, 10, 5, tzinfo=UTC),
        triage="relevant",
    )
    item = {
        "kind": "competition",
        "title": "Hackathon",
        "summary": "…",
        "importance": 50,
        "confidence": 0.9,
        "evidence": [{"message_id": message.id, "quote": "Hackathon on Friday"}],
    }
    fake_provider().answers.extend([AIRateLimited("429"), {"changes": [], "items": [item]}])

    extract_source(group)

    assert Insight.objects.get().model_version == "smart-b"
