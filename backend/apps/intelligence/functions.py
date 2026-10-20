"""Background jobs for the intelligence app, run by Inngest (config/inngest.py; M9.6k).

Each job is a plain function; @function makes Inngest run it when its event is sent with
send(EVENT, ...). The jobs still in tasks.py (files, daily jobs) move here next.
"""

import datetime
import logging

import inngest

from config.inngest import function, send

from . import delivery, extraction, triage
from .models import Insight, Source
from .providers import AIError, AIRateLimited

logger = logging.getLogger(__name__)

# Events (what happened), with the data each one carries.
MESSAGES_ADDED = "uniflow/messages.added"  # source_id: a group has new messages to sort
ACADEMIC_MESSAGES = "uniflow/messages.academic"  # source_id: sorted, some are academic
INSIGHT_DELIVERED = "uniflow/insight.delivered"  # insight_id: students to alert
INSIGHT_RETRACTED = "uniflow/insight.retracted"  # insight_id: alerted students to tell


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
