"""Background jobs for the intelligence app (run by Celery; see config/celery.py)."""

import logging

from celery import shared_task

from . import services, triage
from .models import Source
from .providers import AIError, AIRateLimited

logger = logging.getLogger(__name__)


@shared_task
def clear_old_messages() -> dict[str, int]:
    """Daily privacy clean-up (scheduled in CELERY_BEAT_SCHEDULE)."""
    result = services.clear_old_messages()
    logger.info("Privacy clean-up: %s", result)
    return result


@shared_task(bind=True, max_retries=6)
def triage_source(self, source_id: int) -> dict[str, int] | None:
    """Sort a group's new messages into academic information or noise (the fast AI model).

    "Too many requests" -> wait and try again (1, 2, 4, 8… minutes). Any other AI problem
    is logged and the messages stay "not looked at yet" for the next run.
    """
    source = Source.objects.filter(pk=source_id).first()
    if source is None:
        return None
    try:
        result = triage.triage_source(source)
    except AIRateLimited as error:
        raise self.retry(exc=error, countdown=60 * 2**self.request.retries) from error
    except AIError as error:
        logger.warning("Triage of source %s failed: %s", source_id, error)
        return None
    logger.info("Triage of source %s: %s", source_id, result)
    return result
