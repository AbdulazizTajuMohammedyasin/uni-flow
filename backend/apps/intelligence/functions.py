"""Background jobs for the intelligence app, run by Inngest (config/inngest.py; M9.6k, M9.6l).

Each job is a plain function; @function makes Inngest run it when its event is sent with
send(EVENT, ...), or every day at a set time.
"""

import datetime
import logging

import inngest

from config.inngest import function, send

from . import delivery, extraction, services, telegram, timetable_reading, triage
from .models import Insight, Message, MessageFile, Source, TimetableImport
from .providers import AIError, AIRateLimited

logger = logging.getLogger(__name__)

# Events (what happened), with the data each one carries.
MESSAGES_ADDED = "uniflow/messages.added"  # source_id: a group has new messages to sort
ACADEMIC_MESSAGES = "uniflow/messages.academic"  # source_id: sorted, some are academic
INSIGHT_DELIVERED = "uniflow/insight.delivered"  # insight_id: students to alert
INSIGHT_RETRACTED = "uniflow/insight.retracted"  # insight_id: alerted students to tell
TIMETABLE_IMPORT_STARTED = "uniflow/timetable-import.started"  # import_id: a file to read
GROUP_FILE_SHARED = "uniflow/group-file.shared"  # file_id: maybe the group's timetable
# message_id, file_id, name: a Telegram message with a photo or document to download
TELEGRAM_FILE_RECEIVED = "uniflow/telegram-file.received"


def _try_again_later(error: AIRateLimited, attempt: int) -> inngest.RetryAfterError:
    """Every model said "too many requests": try again as late as Google says the first one
    needs (at most an hour), but at least 1, 2, 4… minutes."""
    seconds = max(60 * 2**attempt, min(error.retry_after or 0, 3600))
    return inngest.RetryAfterError(str(error), datetime.timedelta(seconds=seconds))


@function(MESSAGES_ADDED, retries=6, one_at_a_time_per="source_id")
def triage_source(source_id: int, attempt: int = 0) -> dict[str, int] | None:
    """Sort a group's new messages into academic information or noise (the fast AI model).

    "Too many requests" -> try again later (1, 2, 4, 8… minutes). Any other AI problem is
    logged and the messages stay "not looked at yet" for the next run.
    """
    source = Source.objects.filter(pk=source_id).first()
    if source is None:
        return None
    try:
        result = triage.triage_source(source)
    except AIRateLimited as error:
        raise _try_again_later(error, attempt) from error
    except AIError as error:
        logger.warning("Triage of source %s failed: %s", source_id, error)
        return None
    logger.info("Triage of source %s: %s", source_id, result)
    if result["relevant"]:
        send(ACADEMIC_MESSAGES, source_id=source_id)  # next: understand the academic ones
    return result


@function(ACADEMIC_MESSAGES, retries=6, one_at_a_time_per="source_id")
def extract_source(source_id: int, attempt: int = 0) -> int | None:
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
        raise _try_again_later(error, attempt) from error
    except AIError as error:
        logger.warning("Extraction for source %s failed: %s", source_id, error)
        return None
    logger.info("Extraction for source %s: %s insights", source_id, created)
    return created


# Alerts are not retried: a second run could alert the same students twice.
@function(INSIGHT_DELIVERED)
def notify_insight(insight_id: int, attempt: int = 0) -> int:
    """Alerts for an insight's Direct attention, Action required and Important deliveries."""
    insight = Insight.objects.filter(pk=insight_id).first()
    return delivery.notify_deliveries(insight) if insight else 0


@function(INSIGHT_RETRACTED)
def notify_retraction(insight_id: int, attempt: int = 0) -> int:
    """Tell the students who were alerted about a class change that it was taken back."""
    insight = Insight.objects.filter(pk=insight_id).first()
    return delivery.notify_retraction(insight) if insight else 0


@function(TIMETABLE_IMPORT_STARTED, retries=6)
def read_timetable_import(import_id: int, attempt: int = 0) -> str | None:
    """Read a timetable file for one student's import (the smart AI model).

    "Too many requests" -> try again later. Anything else -> the import is marked "could
    not be read" with a message the student can understand.
    """
    timetable_import = TimetableImport.objects.filter(
        pk=import_id, status=TimetableImport.Status.READING
    ).first()
    if timetable_import is None:
        return None
    try:
        timetable_reading.read_import(timetable_import)
    except AIRateLimited as error:
        raise _try_again_later(error, attempt) from error
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


@function(GROUP_FILE_SHARED, retries=6)
def offer_group_timetable(file_id: int, attempt: int = 0) -> int | None:
    """A file shared in a group: "Is this your timetable?" for members without classes."""
    message_file = MessageFile.objects.select_related("message__source").filter(pk=file_id).first()
    if message_file is None:
        return None
    try:
        offered = timetable_reading.offer_to_group(message_file)
    except AIRateLimited as error:
        raise _try_again_later(error, attempt) from error
    except (timetable_reading.ImportProblem, AIError) as error:
        logger.warning("Group timetable %s not offered: %s", file_id, error)
        return None
    logger.info("Group timetable %s offered to %s students", file_id, len(offered))
    return len(offered)


TELEGRAM_TRIES = 3  # more tries when Telegram can't be reached, a minute apart


@function(TELEGRAM_FILE_RECEIVED, retries=TELEGRAM_TRIES)
def fetch_telegram_file(message_id: int, file_id: str, name: str, attempt: int = 0) -> None:
    """Download a photo or document from a Telegram message, then let the AI sort the
    message. If Telegram can't be reached, try again in a minute (3 times at most)."""
    message = Message.objects.filter(pk=message_id).first()
    if message is None:
        return
    try:
        telegram.fetch_file(message, file_id, name)
    except telegram.TelegramError as error:
        if attempt < TELEGRAM_TRIES:
            raise inngest.RetryAfterError(str(error), datetime.timedelta(minutes=1)) from error
        logger.warning("Telegram file for message %s not downloaded: %s", message_id, error)
    send(MESSAGES_ADDED, source_id=message.source_id)  # now let the AI sort the message


# --- Every day (Kuala Lumpur time) ----------------------------------------------------------


@function(daily_at="03:00", retries=2)  # safe to run again: it only deletes what's old
def clear_old_messages(attempt: int = 0) -> dict[str, int]:
    """Daily privacy clean-up: old message text, timetable files and AI request records."""
    result = services.clear_old_messages()
    logger.info("Privacy clean-up: %s", result)
    return result


@function(daily_at="19:00")
def send_daily_digest(attempt: int = 0) -> int:
    """Every evening: one digest alert per student with new items."""
    sent = delivery.send_daily_digests()
    logger.info("Daily digest sent to %s students", sent)
    return sent
