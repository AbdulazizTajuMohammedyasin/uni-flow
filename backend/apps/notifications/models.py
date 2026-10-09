"""Alerts inside UniFlow (docs/07-notifications.md). Phone push comes with the mobile app.

A Notification tells one user that something needs their attention ("Dr Lee named you
in CDE2313 Section A") and points at what to open (target_type + target_id, e.g.
("insight", 42)); each client turns that into its own page.
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
