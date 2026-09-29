"""Read-only filters for posts."""

from django.db.models import Q
from django.utils import timezone

from .models import Status


def published_q(now=None) -> Q:
    """Posts that are live right now: published and not expired."""
    now = now or timezone.now()
    return Q(status=Status.PUBLISHED) & (Q(expires_at__isnull=True) | Q(expires_at__gt=now))
