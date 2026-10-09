"""Background jobs for the intelligence app (run by Celery; see config/celery.py)."""

import logging

from celery import shared_task

from . import delivery, extraction, services, telegram, timetable_reading, triage
from .models import Insight, Message, MessageFile, Source, TimetableImport
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
    if result["relevant"]:
        extract_source.delay(source_id)  # next step: understand the academic messages
    return result


@shared_task(bind=True, max_retries=6)
def extract_source(self, source_id: int) -> int | None:
    """Find timetable changes in a group's new academic messages (the smart AI model).

    Same retry rule as triage; on any other AI problem the messages stay "not looked at
    yet" for the next run.
    """
    source = Source.objects.filter(pk=source_id).first()
    if source is None:
        return None
    try:
        created = extraction.extract_source(source)
    except AIRateLimited as error:
        raise self.retry(exc=error, countdown=60 * 2**self.request.retries) from error
    except AIError as error:
        logger.warning("Extraction for source %s failed: %s", source_id, error)
        return None
    logger.info("Extraction for source %s: %s insights", source_id, created)
    return created


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


@shared_task(bind=True, max_retries=3)
def fetch_telegram_file(self, message_id: int, file_id: str, name: str) -> None:
    """Download a photo or document from a Telegram message, then let the AI sort the
    message. If Telegram can't be reached, try again in a minute (3 times at most)."""
    message = Message.objects.filter(pk=message_id).first()
    if message is None:
        return
    try:
        telegram.fetch_file(message, file_id, name)
    except telegram.TelegramError as error:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=error, countdown=60) from error
        logger.warning("Telegram file for message %s not downloaded: %s", message_id, error)
    triage_source.delay(message.source_id)


@shared_task(bind=True, max_retries=6)
def offer_group_timetable(self, file_id: int) -> int | None:
    """A file shared in a group: "Is this your timetable?" for members without classes."""
    message_file = MessageFile.objects.select_related("message__source").filter(pk=file_id).first()
    if message_file is None:
        return None
    try:
        offered = timetable_reading.offer_to_group(message_file)
    except AIRateLimited as error:
        raise self.retry(exc=error, countdown=60 * 2**self.request.retries) from error
    except (timetable_reading.ImportProblem, AIError) as error:
        logger.warning("Group timetable %s not offered: %s", file_id, error)
        return None
    logger.info("Group timetable %s offered to %s students", file_id, len(offered))
    return len(offered)


@shared_task
def notify_insight(insight_id: int) -> int:
    """Alerts for an insight's Direct attention, Action required and Important deliveries."""
    insight = Insight.objects.filter(pk=insight_id).first()
    return delivery.notify_deliveries(insight) if insight else 0


@shared_task
def notify_retraction(insight_id: int) -> int:
    """Tell the students who were alerted about a class change that it was taken back."""
    insight = Insight.objects.filter(pk=insight_id).first()
    return delivery.notify_retraction(insight) if insight else 0


@shared_task
def send_daily_digest() -> int:
    """Every evening (CELERY_BEAT_SCHEDULE): one digest alert per student with new items."""
    sent = delivery.send_daily_digests()
    logger.info("Daily digest sent to %s students", sent)
    return sent
