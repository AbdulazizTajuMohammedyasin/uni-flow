"""Actions that change a post's status. Views call these instead of editing `status` directly."""

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import PublishableModel, Status


def publish(item: PublishableModel, user) -> PublishableModel:
    """Make a draft (or archived) post live now. Publishing a live post changes nothing."""
    if item.status == Status.PUBLISHED:
        return item
    now = timezone.now()
    if item.expires_at is not None and item.expires_at <= now:
        raise ValidationError({"expires_at": "The expiry date has already passed."})
    item.status = Status.PUBLISHED
    item.published_at = now
    item.updated_by = user
    item.save(update_fields=["status", "published_at", "updated_by", "updated_at"])
    return item


def archive(item: PublishableModel, user) -> PublishableModel:
    """Take a post out of the feeds (kept for history; it can be published again)."""
    if item.status == Status.ARCHIVED:
        return item
    item.status = Status.ARCHIVED
    item.updated_by = user
    item.save(update_fields=["status", "updated_by", "updated_at"])
    return item
