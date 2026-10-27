"""Background jobs with Inngest (M9.6j-m): no real Inngest server is contacted."""

import json
import os
import subprocess
import sys

import inngest
import inngest.django
import pytest
from django.conf import settings
from django.test import RequestFactory
from inngest.experimental import mocked
from rest_framework.test import APIClient

from config.inngest import function, functions, ping

SIGNING_KEY = "signkey-prod-" + "ab" * 32  # made up


def test_ping_answers_pong():
    result = mocked.trigger(ping, inngest.Event(name="uniflow/ping"), mocked.Inngest(app_id="t"))
    assert result.status is mocked.Status.COMPLETED
    assert result.output == "pong"


def test_inngest_can_reach_uniflow():
    response = APIClient().get("/api/inngest")
    assert response.status_code == 200
    assert response.json()["function_count"] == len(functions)


def test_each_job_tells_inngest_when_it_runs_its_retries_and_limits():
    """What Inngest is told about each job (M9.6k, M9.6l, M9.15): AI jobs retry 6 times and
    sorting never runs twice at once for the same group; alerts and the digest are never
    retried (no double alerts); pushing runs one at a time, on new alerts and every 5
    minutes; the daily jobs run at 03:00 and 19:00 Kuala Lumpur time."""
    told = {}
    for fn in functions:
        config = fn.get_config("http://testserver/api/inngest").main
        told[config.name] = (
            [getattr(trigger, "event", None) or trigger.cron for trigger in config.triggers],
            config.steps["step"].retries.attempts if config.steps["step"].retries else None,
            [(c.key, c.limit) for c in config.concurrency or []],
        )
    one_per_group = [("event.data.source_id", 1)]
    kl = "TZ=Asia/Kuala_Lumpur"
    assert told == {
        "ping": (["uniflow/ping"], None, []),
        "triage-source": (["uniflow/messages.added"], 6, one_per_group),
        "extract-source": (["uniflow/messages.academic"], 6, one_per_group),
        "notify-insight": (["uniflow/insight.delivered"], 0, []),
        "notify-retraction": (["uniflow/insight.retracted"], 0, []),
        "read-timetable-import": (["uniflow/timetable-import.started"], 6, []),
        "offer-group-timetable": (["uniflow/group-file.shared"], 6, []),
        "fetch-telegram-file": (["uniflow/telegram-file.received"], 3, []),
        "clear-old-messages": ([f"{kl} 0 3 * * *"], 2, []),
        "send-daily-digest": ([f"{kl} 0 19 * * *"], 0, []),
        "push-notifications": (
            ["uniflow/notifications.created", f"{kl} */5 * * * *"],
            5,
            [(None, 1)],
        ),
        "check-push-receipts": ([f"{kl} */15 * * * *"], 2, []),
        "deactivate-stale-devices": ([f"{kl} 0 3 * * *"], 2, []),
    }


def test_a_job_needs_an_event_or_a_time():
    with pytest.raises(ValueError):
        function()
    with pytest.raises(ValueError):
        function(daily_at="19:00", every_minutes=5)


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


def start_production(**inngest_settings):
    """Load the production settings in a separate Python, as Render would start the site."""
    env = {name: value for name, value in os.environ.items() if not name.startswith("INNGEST_")}
    env |= {
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "DJANGO_SECRET_KEY": "test-only-" + "x" * 50,
        "DJANGO_ALLOWED_HOSTS": "uniflow.example.com",
        "INNGEST_DEV": "",  # online: Inngest Cloud (wins over any backend/.env value)
        **inngest_settings,
    }
    return subprocess.run(
        [sys.executable, "-c", "import django; django.setup(); import config.urls"],
        cwd=settings.BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_online_the_site_refuses_to_start_without_the_inngest_keys():
    missing = start_production(INNGEST_EVENT_KEY="event-key")
    assert missing.returncode != 0
    assert "Missing required environment variable: INNGEST_SIGNING_KEY" in missing.stderr

    ready = start_production(INNGEST_SIGNING_KEY=SIGNING_KEY, INNGEST_EVENT_KEY="event-key")
    assert ready.returncode == 0, ready.stderr
