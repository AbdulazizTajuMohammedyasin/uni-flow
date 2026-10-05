"""Background jobs for the intelligence app (run by Celery; see config/celery.py)."""

import logging

from celery import shared_task

from . import services, timetable_reading, triage
from .models import Source, TimetableImport
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


@shared_task(bind=True, max_retries=6)
def read_timetable_import(self, import_id: int) -> str | None:
    """Read a timetable file for one student's import (the smart AI model).

    "Too many requests" -> wait and try again. Anything else -> the import is marked
    "could not be read" with a message the student can understand.
    """
    timetable_import = TimetableImport.objects.filter(
        pk=import_id, status=TimetableImport.Status.READING
    ).first()
    if timetable_import is None:
        return None
    try:
        timetable_reading.read_import(timetable_import)
    except AIRateLimited as error:
        raise self.retry(exc=error, countdown=60 * 2**self.request.retries) from error
    except (timetable_reading.ImportProblem, AIError) as error:
        logger.warning("Timetable import %s failed: %s", import_id, error)
        timetable_import.status = TimetableImport.Status.FAILED
        timetable_import.error = (
            str(error)
            if isinstance(error, timetable_reading.ImportProblem)
            else "Couldn't read this timetable right now. Please try again later."
        )
        timetable_import.save(update_fields=["status", "error", "updated_at"])
    return timetable_import.status
