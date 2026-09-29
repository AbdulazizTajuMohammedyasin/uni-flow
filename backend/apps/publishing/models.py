"""The shared base for every kind of post (see docs/03-data-model.md, "publishing").

These are "abstract" models: they have no table of their own. Announcements, events and
application listings extend TargetedModel; documents extend PublishableModel.
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.academics.models import School
from apps.audiences.models import Audience
from core.models import TimeStampedModel


class PublisherType(models.TextChoices):
    UNIVERSITY = "university", "University"
    SCHOOL = "school", "School"


class Status(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class SourcePlatform(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    TELEGRAM = "telegram", "Telegram"
    WEBSITE = "website", "Website"
    EMAIL = "email", "Email"
    PORTAL = "portal", "Portal"
    OTHER = "other", "Other"


class PublishableModel(TimeStampedModel):
    # Who it is from: the university, or one school.
    publisher_type = models.CharField(max_length=20, choices=PublisherType)
    publisher_school = models.ForeignKey(
        School, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )

    status = models.CharField(max_length=20, choices=Status, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)  # set by services.publish()
    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="Optional. After this it leaves the feeds."
    )
    notified_at = models.DateTimeField(null=True, blank=True)  # so it never notifies twice

    # Where it was first posted, if it came from somewhere else (optional).
    source_platform = models.CharField(max_length=20, choices=SourcePlatform, blank=True)
    source_url = models.URLField(max_length=500, blank=True)

    class Meta:
        abstract = True
        indexes = [models.Index(fields=["status", "published_at"])]
        constraints = [
            models.CheckConstraint(
                # A school post names its school; a university post has none.
                condition=(
                    Q(publisher_type=PublisherType.SCHOOL, publisher_school__isnull=False)
                    | (~Q(publisher_type=PublisherType.SCHOOL) & Q(publisher_school__isnull=True))
                ),
                name="%(app_label)s_%(class)s_publisher_school",
            ),
            models.CheckConstraint(
                condition=(
                    Q(expires_at__isnull=True)
                    | Q(published_at__isnull=True)
                    | Q(expires_at__gt=F("published_at"))
                ),
                name="%(app_label)s_%(class)s_expires_after_publish",
            ),
        ]

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= timezone.now()


class TargetedModel(PublishableModel):
    """A post with an audience (who it is for). Each post owns its own Audience row."""

    audience = models.OneToOneField(Audience, on_delete=models.PROTECT, related_name="+")

    class Meta(PublishableModel.Meta):
        abstract = True
