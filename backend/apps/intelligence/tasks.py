"""Background jobs for the intelligence app (run by Celery; see config/celery.py)."""

import logging

from celery import shared_task

from . import services

logger = logging.getLogger(__name__)


@shared_task
def clear_old_messages() -> dict[str, int]:
    """Daily privacy clean-up (scheduled in CELERY_BEAT_SCHEDULE)."""
    result = services.clear_old_messages()
    logger.info("Privacy clean-up: %s", result)
    return result
