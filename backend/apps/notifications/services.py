"""Sending alerts (docs/07-notifications.md). Any part of UniFlow builds Notification rows
and calls send(); this app never needs to know about insights or timetables.

The phones alerts can be pushed to are registered here too (register_device), always for
the logged-in user; the request never names a user."""

import logging

from django.db import transaction
from django.utils import timezone

from config.inngest import send as send_event

from .models import Device, Notification

NOTIFICATIONS_CREATED = "uniflow/notifications.created"  # new alerts may need a push
logger = logging.getLogger(__name__)


def send(alerts: list[Notification]) -> None:
    """Store alerts in batches. An alert whose (recipient, dedupe_key) already exists is
    skipped, so the same alert is never sent twice, even if a job runs again. Once saved,
    the push job sends the new ones to the recipients' phones (it finds them itself, since
    bulk_create doesn't say which rows were new)."""
    if not alerts:
        return
    Notification.objects.bulk_create(alerts, batch_size=1000, ignore_conflicts=True)
    transaction.on_commit(_start_push)


def _start_push() -> None:
    try:
        send_event(NOTIFICATIONS_CREATED)
    except Exception:  # the alerts are saved; the push job's 5-minute run finds them anyway
        logger.exception("Couldn't start the push job")


def register_device(user, token: str, platform: str, app_version: str = "") -> bool:
    """The user's phone can get push notifications (True if it wasn't known yet). A phone
    registered by another student moves to this one, so a shared or handed-on phone never
    gets the previous student's alerts (it counts as a new phone for them: no older alerts)."""
    Device.objects.filter(expo_token=token).exclude(user=user).delete()
    _, created = Device.objects.update_or_create(
        expo_token=token,
        defaults={
            "user": user,
            "platform": platform,
            "app_version": app_version,
            "is_active": True,
            "last_seen_at": timezone.now(),
            "deactivated_reason": "",
        },
    )
    return created


def unregister_device(user, token: str) -> None:
    """The user logged out on that phone. Someone else's phone is left as it is."""
    Device.objects.filter(user=user, expo_token=token, is_active=True).update(
        is_active=False, deactivated_reason=Device.Reason.LOGOUT, updated_at=timezone.now()
    )
