"""Inngest: runs slow work (the AI, files, daily jobs) in the background (M9.6j-m; it replaced
Celery and Redis). No worker program and no Redis are needed.

How it works: Django sends an event (e.g. "uniflow/ping") to Inngest; Inngest then calls
Django back at /api/inngest to run every function waiting for that event. If a function
fails, Inngest calls again later (retries); it also starts the daily jobs at their times.

On your laptop, start Inngest's dev server next to runserver (its dashboard, with every run,
opens at http://127.0.0.1:8288), from any folder, on one line:

    npx --ignore-scripts=false inngest-cli@1.45.1 dev --no-discovery -u <address>

where <address> is http://127.0.0.1:8000/api/inngest (Django's runserver).

Online, Inngest Cloud needs INNGEST_SIGNING_KEY (Django checks each call really comes from
Inngest) and INNGEST_EVENT_KEY (lets Django send events). Guide: docs/10, section 21.
"""

from collections.abc import Callable

import inngest
from django.conf import settings

client = inngest.Inngest(app_id="uniflow", is_production=not settings.INNGEST_DEV)

# Every function Inngest may run, served at /api/inngest (config/urls.py). Apps add theirs
# with @function when Django starts (each app's functions.py, loaded in its AppConfig.ready).
functions: list[inngest.Function] = []
# For tests (INNGEST_RUN_NOW): event name -> the plain job functions waiting for it.
_jobs: dict[str, list[Callable[..., object]]] = {}


def function(
    event: str | None = None,
    *,
    daily_at: str | None = None,
    retries: int = 0,
    one_at_a_time_per: str | None = None,
):
    """Make a plain job an Inngest function, started by `event` (it is called as
    `run(**event_data, attempt=0)`) or every day at `daily_at` (e.g. "19:00", in TIME_ZONE;
    called as `run(attempt=0)`).

    retries: how many more tries after an error (Inngest waits longer each time; a job can
    also raise inngest.RetryAfterError to choose the wait itself).
    one_at_a_time_per: an event data field, e.g. "source_id": runs for the same value wait
    for each other (never two runs on one group at once); other values run side by side.

    The decorated name stays the plain function, so code and tests can still call it.
    """
    if (event is None) == (daily_at is None):
        raise ValueError("Give a job either an event or a daily_at time.")

    def register(run: Callable[..., object]) -> Callable[..., object]:
        concurrency = None
        if one_at_a_time_per:
            concurrency = [inngest.Concurrency(limit=1, key=f"event.data.{one_at_a_time_per}")]

        if event:
            trigger = inngest.TriggerEvent(event=event)

            def handler(ctx: inngest.ContextSync) -> object:
                return run(**ctx.event.data, attempt=ctx.attempt)

            _jobs.setdefault(event, []).append(run)
        else:
            hour, minute = (int(part) for part in daily_at.split(":"))
            trigger = inngest.TriggerCron(cron=f"TZ={settings.TIME_ZONE} {minute} {hour} * * *")

            def handler(ctx: inngest.ContextSync) -> object:
                return run(attempt=ctx.attempt)

        functions.append(
            client.create_function(
                fn_id=run.__name__.replace("_", "-"),
                trigger=trigger,
                retries=retries,
                concurrency=concurrency,
            )(handler)
        )
        return run

    return register


def send(event: str, **data) -> None:
    """Start the functions waiting for `event`, e.g. send("uniflow/messages.added", source_id=3).

    In tests (INNGEST_RUN_NOW) they run at once in this process instead, and errors are
    raised; nothing is sent to Inngest."""
    if settings.INNGEST_RUN_NOW:
        for run in _jobs.get(event, []):
            run(**data)
        return
    client.send_sync(inngest.Event(name=event, data=data))


@client.create_function(fn_id="ping", trigger=inngest.TriggerEvent(event="uniflow/ping"))
def ping(ctx: inngest.ContextSync) -> str:
    """A tiny job to check the set-up: `pipenv run python manage.py inngest_ping`, and the
    dev server's dashboard (Runs) shows "ping" completed with "pong"."""
    return "pong"


functions.append(ping)
