"""Sending alerts (docs/07-notifications.md). Any part of UniFlow builds Notification rows
and calls send(); this app never needs to know about insights or timetables.

The phones alerts can be pushed to are registered here too (register_device), always for
the logged-in user; the request never names a user."""

from django.utils import timezone

from .models import Device, Notification


def send(alerts: list[Notification]) -> None:
    """Store alerts in batches. An alert whose (recipient, dedupe_key) already exists is
    skipped, so the same alert is never sent twice, even if a job runs again."""
    Notification.objects.bulk_create(alerts, batch_size=1000, ignore_conflicts=True)


def register_device(user, token: str, platform: str, app_version: str = "") -> bool:
    """The user's phone can get push notifications (True if it wasn't known yet). A phone
    registered by another student moves to this one, so a shared or handed-on phone never
    gets the previous student's alerts."""
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
