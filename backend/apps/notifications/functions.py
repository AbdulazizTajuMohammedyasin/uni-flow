"""Background jobs of the notifications app (Inngest, see config/inngest.py): pushing alerts
to phones (docs/07-notifications.md, M9.15). Each job is a plain function tests can call."""

import datetime
import logging

import inngest
from django.conf import settings

from config.inngest import function

from . import push
from .services import NOTIFICATIONS_CREATED

logger = logging.getLogger(__name__)
_told_no_token = False


def _has_token() -> bool:
    global _told_no_token
    if not settings.EXPO_ACCESS_TOKEN and not _told_no_token:
        logger.info("EXPO_ACCESS_TOKEN is not set: nothing is pushed to phones.")
        _told_no_token = True
    return bool(settings.EXPO_ACCESS_TOKEN)


# On every new alert, plus every 5 minutes in case an event was missed. One run at a time:
# a pending ticket is never sent by two runs.
@function(NOTIFICATIONS_CREATED, every_minutes=5, retries=5, one_at_a_time=True)
def push_notifications(attempt: int = 0) -> dict[str, int]:
    """Push new alerts to their recipients' phones. When Expo can't be reached, try again
    after 1, 2, 4… minutes; only tickets younger than an hour are sent then."""
    if not _has_token():
        return {}
    push.skip_old()
    claimed = 0
    for _ in range(20):  # at most 10,000 alerts a run; the next run takes the rest
        if not (batch := push.claim()):
            break
        claimed += batch
    try:
        return {"claimed": claimed, **push.send_pending()}
    except push.ExpoUnavailable as error:
        logger.warning("Expo is unavailable (%s); pushes will be tried again", error)
        raise inngest.RetryAfterError(str(error), datetime.timedelta(minutes=2**attempt)) from None


@function(every_minutes=15, retries=2)
def check_push_receipts(attempt: int = 0) -> dict[str, int]:
    """What Google or Apple said about recent pushes (phones that are gone are switched off),
    and tickets older than 7 days are deleted."""
    deleted = push.delete_old_tickets()
    if not _has_token():
        return {"deleted": deleted}
    try:
        return {"deleted": deleted, **push.check_receipts()}
    except push.ExpoUnavailable as error:
        logger.warning("Expo is unavailable (%s); receipts will be checked later", error)
        return {"deleted": deleted}


@function(daily_at="03:00", retries=2)
def deactivate_stale_devices(attempt: int = 0) -> int:
    """Phones not used for longer than a login lasts (14 days) stop getting alerts."""
    return push.switch_off_stale_devices()
