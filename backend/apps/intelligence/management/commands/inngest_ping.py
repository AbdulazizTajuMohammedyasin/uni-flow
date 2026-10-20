"""Send Inngest a test event: `pipenv run python manage.py inngest_ping`.

Checks both directions: Django → Inngest (the event is accepted) and Inngest → Django (the
dev server's dashboard shows the "ping" run completed with "pong")."""

import inngest
from django.core.management.base import BaseCommand

from config.inngest import client


class Command(BaseCommand):
    help = "Send Inngest a test event; the 'ping' function should answer 'pong'."

    def handle(self, *args, **options):
        ids = client.send_sync(inngest.Event(name="uniflow/ping"))
        self.stdout.write(
            self.style.SUCCESS(f"Sent (event {ids[0]}). Check the Inngest dashboard.")
        )
