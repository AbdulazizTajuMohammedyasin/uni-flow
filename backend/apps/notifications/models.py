"""Alerts inside UniFlow (docs/07-notifications.md), and the phones they can be pushed to.

A Notification tells one user that something needs their attention ("Dr Lee named you
in CDE2313 Section A") and points at what to open (target_type + target_id, e.g.
("insight", 42)); each client turns that into its own page.

A Device is a phone with the UniFlow app; PushSettings say which alerts reach the phone
(the bell always shows everything).
"""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class NotificationKind(models.TextChoices):
    DIRECT_ATTENTION = "direct_attention", "You were named"
    ACTION_REQUIRED = "action_required", "Action required"
    IMPORTANT_UPDATE = "important_update", "Important update"
    TIMETABLE_CHANGE_PROPOSED = "timetable_change_proposed", "Class change to confirm"
    TIMETABLE_CHANGE_RETRACTED = "timetable_change_retracted", "Class change taken back"
    DIGEST = "digest", "Daily digest"
    SYSTEM = "system", "From UniFlow"


class Notification(TimeStampedModel):
    Kind = NotificationKind  # Notification.Kind.DIGEST etc.

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=30, choices=Kind)
    title = models.CharField(max_length=200)
    body = models.CharField(max_length=500, blank=True)
    target_type = models.CharField(max_length=30, blank=True, help_text='e.g. "insight"')
    target_id = models.BigIntegerField(null=True, blank=True)
    # The same alert is never sent twice: e.g. "ins:42:u:7" for insight 42 to user 7.
    # NULL (not "") when there is none, so such rows don't clash in the unique rule below.
    dedupe_key = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001
    read_at = models.DateTimeField(null=True, blank=True)
    # Claimed by the push job (pushed to the phones, or skipped): never claimed twice.
    pushed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["recipient", "read_at", "created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "dedupe_key"], name="notifications_unique_dedupe_key"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} for {self.recipient}: {self.title}"


class Device(TimeStampedModel):
    """A phone with the UniFlow app that may get push notifications for its user. The
    website inside the app registers it with the user's own login (docs/07-notifications.md)."""

    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"

    class Reason(models.TextChoices):
        LOGOUT = "logout", "Logged out"
        NOT_REGISTERED = "not_registered", "Removed from the phone"
        STALE = "stale", "Not used for a long time"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices"
    )
    # "ExponentPushToken[…]": an address, not a secret, but personal: never logged in full.
    # Unique: a phone has one owner, the last student who logged in on it.
    expo_token = models.CharField(max_length=200, unique=True)
    platform = models.CharField(max_length=10, choices=Platform)
    app_version = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField()  # the last registration: the app was used
    deactivated_reason = models.CharField(max_length=30, choices=Reason, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user", "is_active"])]

    def __str__(self) -> str:
        return f"{self.get_platform_display()} phone of {self.user}"


class PushSettings(TimeStampedModel):
    """Which alerts reach the student's phones. No row yet means everything does.
    Alerts from UniFlow itself (`system`) always go out."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="push_settings",
    )
    class_changes = models.BooleanField(default=True)  # timetable_change_proposed / _retracted
    needs_you = models.BooleanField(default=True)  # direct_attention, action_required, important
    daily_digest = models.BooleanField(default=True)  # digest

    class Meta:
        verbose_name_plural = "push settings"

    def __str__(self) -> str:
        return f"Push settings of {self.user}"


class PushTicket(TimeStampedModel):
    """One alert pushed to one phone, and what Expo answered (kept 7 days)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Waiting to be sent"
        OK = "ok", "Accepted by Expo"
        ERROR = "error", "Refused"

    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="push_tickets"
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="push_tickets")
    status = models.CharField(max_length=10, choices=Status, default=Status.PENDING)
    expo_id = models.CharField(max_length=100, blank=True)  # Expo's ticket id, for the receipt
    error = models.CharField(max_length=50, blank=True)  # e.g. "DeviceNotRegistered"
    # What Google or Apple finally said, from Expo's receipt: "ok" or an error code.
    receipt = models.CharField(max_length=50, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "device"], name="notifications_one_ticket_per_phone"
            )
        ]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return f"Push of notification {self.notification_id} to device {self.device_id}"
