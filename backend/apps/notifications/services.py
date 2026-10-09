"""Sending alerts (docs/07-notifications.md). Any part of UniFlow builds Notification rows
and calls send(); this app never needs to know about insights or timetables."""

from .models import Notification


def send(alerts: list[Notification]) -> None:
    """Store alerts in batches. An alert whose (recipient, dedupe_key) already exists is
    skipped, so the same alert is never sent twice, even if a job runs again."""
    Notification.objects.bulk_create(alerts, batch_size=1000, ignore_conflicts=True)
