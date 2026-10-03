"""The AI pipeline's data (docs/03-data-model.md, "intelligence").

- Source: a connected group or channel (WhatsApp, Telegram), or a staff/manual source.
- SourceMember: a student who added that group in UniFlow ("I am in this group").
- Message: one message from a source. Raw text is deleted after the retention period.
Insights (what the AI understood) are added in M5.
"""

from django.conf import settings
from django.db import models

from apps.academics.models import Course, Intake, Programme, School
from apps.timetable.models import CourseSection
from core.models import TimeStampedModel


class Source(TimeStampedModel):
    class Platform(models.TextChoices):
        WHATSAPP_GROUP = "whatsapp_group", "WhatsApp group"
        TELEGRAM_GROUP = "telegram_group", "Telegram group"
        TELEGRAM_CHANNEL = "telegram_channel", "Telegram channel"
        STAFF = "staff", "Staff posts"
        MANUAL = "manual", "Pasted or uploaded"

    class Trust(models.TextChoices):
        NORMAL = "normal", "Normal"
        OFFICIAL = "official", "Official"

    class Status(models.TextChoices):
        PENDING = "pending", "Waiting to join"
        ACTIVE = "active", "Active"
        DISCONNECTED = "disconnected", "Disconnected"

    platform = models.CharField(max_length=20, choices=Platform)
    # The platform's own chat id. NULL (not "") when there is none, e.g. a manual source or
    # a group not joined yet, so such sources don't clash in the unique rule below.
    external_id = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001
    title = models.CharField(max_length=200)
    invite_url = models.URLField(max_length=500, blank=True)

    # What the group is for. Given by the student who added it: only a suggestion until
    # messages, members or an admin confirm it.
    school = models.ForeignKey(
        School, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    programme = models.ForeignKey(
        Programme, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    intake = models.ForeignKey(
        Intake, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    course = models.ForeignKey(
        Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    section = models.ForeignKey(
        CourseSection, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    scope_confirmed = models.BooleanField(default=False)

    trust = models.CharField(max_length=20, choices=Trust, default=Trust.NORMAL)
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING)
    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    notice_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "external_id"], name="intelligence_source_platform_chat"
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_platform_display()})"


class SourceMember(TimeStampedModel):
    """A student who added this group in UniFlow. Students never share their phone number."""

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="source_memberships"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "user"], name="intelligence_member_unique")
        ]

    def __str__(self) -> str:
        return f"{self.user} in {self.source}"


class Message(TimeStampedModel):
    class Triage(models.TextChoices):
        PENDING = "pending", "Not looked at yet"
        NOISE = "noise", "Noise"
        RELEVANT = "relevant", "Academic information"

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="messages")
    # The platform's message id. NULL when there is none (e.g. some pasted messages).
    external_id = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001
    sender_name = models.CharField(max_length=150, blank=True)
    sender_ref = models.CharField(
        max_length=64, blank=True, help_text="A hash of the sender's platform id."
    )
    text = models.TextField(blank=True)
    sent_at = models.DateTimeField()
    reply_to = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies"
    )
    raw = models.JSONField(default=dict, blank=True, help_text="The platform's original data.")
    triage = models.CharField(max_length=20, choices=Triage, default=Triage.PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    text_deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sent_at"]
        indexes = [models.Index(fields=["source", "sent_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"], name="intelligence_message_unique"
            )
        ]

    def __str__(self) -> str:
        preview = self.text[:50] + ("…" if len(self.text) > 50 else "")
        return f"{self.sender_name or 'Unknown'}: {preview}"
