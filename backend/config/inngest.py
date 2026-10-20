"""Inngest: runs slow work (the AI, daily jobs) in the background, replacing Celery step by
step (M9.6j onwards). No worker program and no Redis are needed.

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

import inngest
from django.conf import settings

client = inngest.Inngest(app_id="uniflow", is_production=not settings.INNGEST_DEV)


@client.create_function(fn_id="ping", trigger=inngest.TriggerEvent(event="uniflow/ping"))
def ping(ctx: inngest.ContextSync) -> str:
    """A tiny job to check the set-up: `pipenv run python manage.py inngest_ping`, and the
    dev server's dashboard (Runs) shows "ping" completed with "pong"."""
    return "pong"


# Every function Inngest may run; served at /api/inngest (config/urls.py).
functions = [ping]
