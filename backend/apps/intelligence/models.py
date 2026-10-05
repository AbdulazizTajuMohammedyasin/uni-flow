"""The AI pipeline's data (docs/03-data-model.md, "intelligence").

- Source: a connected group or channel (WhatsApp, Telegram), or a staff/manual source.
- SourceMember: a student who added that group in UniFlow ("I am in this group").
- Message: one message from a source. Raw text is deleted after the retention period.
- MessageFile: a timetable image, PDF or spreadsheet (from a group, an upload or a Google
  Drive link). Stored privately; deleted with the message text after the retention period.
- Insight: one piece of information (found by the AI, or posted by staff), with
  InsightEvidence linking it to the original messages.
- TimetableImport: one student's classes read from a timetable file, waiting for them to
  confirm (it lives here, not in timetable, because it points at a MessageFile).
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.academics.models import Course, Intake, Programme, School, Term
from apps.accounts.models import InfoType
from apps.publishing.models import TargetedModel
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


def message_file_path(instance, filename: str) -> str:
    """message_files/2026/10/<random>.pdf — the original name is never used in the path."""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"message_files/{timezone.now():%Y/%m}/{uuid.uuid4().hex}.{extension}"


class MessageFile(TimeStampedModel):
    """A file UniFlow can read: from a group message, a student's upload, or a Drive link."""

    class Kind(models.TextChoices):
        IMAGE = "image", "Image"
        PDF = "pdf", "PDF"
        SPREADSHEET = "spreadsheet", "Spreadsheet"

    message = models.ForeignKey(
        Message, null=True, blank=True, on_delete=models.CASCADE, related_name="files"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="uploaded_files",
        help_text="Set for a student's own upload or Drive link (only they can use it).",
    )
    kind = models.CharField(max_length=20, choices=Kind)
    file = models.FileField(upload_to=message_file_path, blank=True)
    original_name = models.CharField(max_length=255, blank=True)
    source_url = models.URLField(max_length=1000, blank=True, help_text="The Drive link, if any.")
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    file_deleted_at = models.DateTimeField(null=True, blank=True)
    # The AI's reading of a timetable file, done once and reused for every student:
    # {"tabs": {"<tab name>": [<class rows>], ...}} ("" for an image or PDF).
    reading = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.original_name or self.source_url or f"File {self.pk}"


# How sure the AI must be (docs/12-intelligence.md, "How sure must the AI be?"):
CONFIDENT = 0.8  # at or above: published and delivered normally
UNSURE = 0.5  # from here up to CONFIDENT: published, digest only, marked "Not confirmed"
#               below UNSURE: kept as a draft until someone checks it


class Insight(TargetedModel):
    """One piece of information UniFlow found (or a staff member posted), e.g. "CDE2313 class
    moved to 2 PM tomorrow". Inherited from TargetedModel: audience (who it is for),
    publisher, status (draft = held for review, published = delivered, archived =
    retracted), created_by, published_at, expires_at and notified_at.
    """

    class Kind(models.TextChoices):
        CLASS_MOVED = "class_moved", "Class moved"
        CLASS_CANCELLED = "class_cancelled", "Class cancelled"
        ROOM_CHANGED = "room_changed", "Room changed"
        EXTRA_SESSION = "extra_session", "Extra session"
        TIMETABLE_SHARED = "timetable_shared", "Timetable shared"
        INTERNSHIP = "internship", "Internship"
        BOOTCAMP = "bootcamp", "Bootcamp"
        INDUSTRY_VISIT = "industry_visit", "Industry visit"
        COMPETITION = "competition", "Competition"
        SCHOLARSHIP = "scholarship", "Scholarship"
        ACADEMIC_NOTICE = "academic_notice", "Academic notice"
        STUDENT_AFFAIRS = "student_affairs", "Student affairs"
        MANDATORY_EVENT = "mandatory_event", "Mandatory event"
        DEADLINE = "deadline", "Deadline"
        DIRECT_REQUEST = "direct_request", "Request to a student"

    class Origin(models.TextChoices):
        AI = "ai", "Found by the AI"
        STAFF = "staff", "Posted by staff"

    kind = models.CharField(max_length=30, choices=Kind)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=500)
    importance = models.PositiveSmallIntegerField(default=50, help_text="0–100.")
    action_required = models.BooleanField(default=False)
    action_text = models.CharField(max_length=200, blank=True)
    info_type = models.CharField(max_length=30, choices=InfoType, blank=True)
    topics = models.JSONField(default=list, blank=True, help_text="Interest values.")
    starts_at = models.DateTimeField(null=True, blank=True)
    deadline_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    link = models.URLField(max_length=500, blank=True)
    data = models.JSONField(default=dict, blank=True, help_text="The AI's checked answer.")
    confidence = models.FloatField(default=1.0, help_text="0–1: how sure the AI was.")
    origin = models.CharField(max_length=10, choices=Origin, default=Origin.STAFF)
    publisher_source = models.ForeignKey(
        Source, null=True, blank=True, on_delete=models.PROTECT, related_name="insights"
    )
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    corrected_at = models.DateTimeField(null=True, blank=True)
    model_version = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=50, blank=True)
    merge_key = models.CharField(max_length=200, blank=True, db_index=True)

    class Meta(TargetedModel.Meta):
        indexes = [*TargetedModel.Meta.indexes, models.Index(fields=["kind"])]
        constraints = [
            *TargetedModel.Meta.constraints,
            models.CheckConstraint(
                # An insight "from a group" names its group; other publishers don't.
                condition=(
                    models.Q(publisher_type="source", publisher_source__isnull=False)
                    | (~models.Q(publisher_type="source") & models.Q(publisher_source__isnull=True))
                ),
                name="intelligence_insight_publisher_source",
            ),
            models.CheckConstraint(
                condition=models.Q(confidence__gte=0, confidence__lte=1),
                name="intelligence_insight_confidence_range",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def is_unconfirmed(self) -> bool:
        """Shown only in the daily digest, marked "Not confirmed" (the AI wasn't sure)."""
        return self.origin == self.Origin.AI and self.confidence < CONFIDENT


class InsightEvidence(TimeStampedModel):
    """Links an insight to an original message. The quote stays after the message text is
    deleted (60-day privacy clean-up), so the insight can still show where it came from."""

    insight = models.ForeignKey(Insight, on_delete=models.CASCADE, related_name="evidence")
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="evidence")
    quote = models.CharField(max_length=500)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["insight", "message"], name="intelligence_evidence_unique"
            )
        ]

    def __str__(self) -> str:
        return self.quote


class TimetableImport(TimeStampedModel):
    """One student's "Is this your timetable?": classes read from a file, saved only when
    the student confirms (then the shared sections are created and they are enrolled)."""

    class Status(models.TextChoices):
        READING = "reading", "Being read"
        READY = "ready", "Ready to confirm"
        CONFIRMED = "confirmed", "Confirmed"
        DISCARDED = "discarded", "Discarded"
        FAILED = "failed", "Could not be read"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="timetable_imports"
    )
    message_file = models.ForeignKey(MessageFile, on_delete=models.PROTECT, related_name="imports")
    tab = models.CharField(max_length=100, blank=True, help_text="The spreadsheet tab chosen.")
    term = models.ForeignKey(
        Term, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    status = models.CharField(max_length=20, choices=Status, default=Status.READING)
    rows = models.JSONField(default=list, blank=True, help_text="This student's classes.")
    report = models.JSONField(default=dict, blank=True, help_text="What confirming changed.")
    error = models.CharField(max_length=300, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Timetable import {self.pk} for {self.user} ({self.status})"
