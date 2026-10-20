"""Background jobs with Inngest (M9.6j, M9.6k): no real Inngest server is contacted."""

import json

import inngest
import inngest.django
import pytest
from django.test import RequestFactory
from inngest.experimental import mocked
from rest_framework.test import APIClient

from config.inngest import functions, ping

SIGNING_KEY = "signkey-prod-" + "ab" * 32  # made up


def test_ping_answers_pong():
    result = mocked.trigger(ping, inngest.Event(name="uniflow/ping"), mocked.Inngest(app_id="t"))
    assert result.status is mocked.Status.COMPLETED
    assert result.output == "pong"


def test_inngest_can_reach_uniflow():
    response = APIClient().get("/api/inngest")
    assert response.status_code == 200
    assert response.json()["function_count"] == len(functions)


def test_each_job_tells_inngest_its_event_retries_and_limits():
    """What Inngest is told about each job (M9.6k): AI jobs retry 6 times and never run twice
    at once for the same group; alerts are never retried (no double alerts)."""
    told = {}
    for fn in functions:
        config = fn.get_config("http://testserver/api/inngest").main
        told[config.name] = (
            config.triggers[0].event,
            config.steps["step"].retries.attempts if config.steps["step"].retries else None,
            [(c.key, c.limit) for c in config.concurrency or []],
        )
    one_per_group = [("event.data.source_id", 1)]
    assert told == {
        "ping": ("uniflow/ping", None, []),
        "triage-source": ("uniflow/messages.added", 6, one_per_group),
        "extract-source": ("uniflow/messages.academic", 6, one_per_group),
        "notify-insight": ("uniflow/insight.delivered", 0, []),
        "notify-retraction": ("uniflow/insight.retracted", 0, []),
    }


@pytest.mark.parametrize(
    ("online", "status", "answer"), [(False, 200, b'"pong"'), (True, 401, None)]
)
def test_online_only_inngest_can_start_a_job(online, status, answer):
    """The same unsigned call to /api/inngest runs the job with the dev server, but online
    (where Inngest signs every call with the signing key) it is refused and nothing runs."""
    client = inngest.Inngest(app_id="uniflow", is_production=online, signing_key=SIGNING_KEY)
    view = inngest.django.serve(client, [ping]).callback
    event = {"name": "uniflow/ping", "data": {}}
    call = {
        "event": event,
        "events": [event],
        "steps": {},
        "ctx": {
            "attempt": 0,
            "disable_immediate_execution": False,
            "run_id": "run-1",
            "stack": {"stack": []},
        },
        "use_api": False,
    }
    response = view(
        RequestFactory().post(
            "/api/inngest?fnId=uniflow-ping&stepId=step",
            data=json.dumps(call),
            content_type="application/json",
        )
    )
    assert response.status_code == status
    if answer:
        assert response.content == answer
    else:
        assert b"pong" not in response.content
