"""Pushing alerts to students' phones through Expo (docs/07-notifications.md, M9.15).

Nothing about who gets what is decided here: a push is a Notification row (already targeted
and never sent twice), shown on its recipient's phones.

1. skip_old() + claim(): each new row is claimed once (pushed_at). Rows older than an hour,
   recipients who can't log in and kinds switched off in PushSettings get no push. Each
   remaining row gets a PushTicket for each phone of its recipient registered before it.
2. send_pending(): pending tickets go to Expo, 100 per request. When Expo can't be reached
   they stay pending and ExpoUnavailable is raised, so the job tries again later.
3. check_receipts(): what Google or Apple finally said; phones that are gone are switched off.

Logs hold ticket and device ids and error codes only: never a push address, the access
token or the alert's text.
"""

import logging
from datetime import timedelta

import httpx
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from .models import Device, Notification, NotificationKind, PushSettings, PushTicket

logger = logging.getLogger(__name__)

SEND_URL = "https://exp.host/--/api/v2/push/send"
RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"
TIMEOUT = 15  # seconds
SEND_BATCH, RECEIPT_BATCH, CLAIM_BATCH = 100, 1000, 500
MAX_AGE = timedelta(hours=1)  # an older alert doesn't wake anyone up; it's still in the bell
RECEIPT_WAIT, RECEIPT_KEPT = timedelta(minutes=15), timedelta(hours=24)  # Expo keeps 24 h
TICKETS_KEPT = timedelta(days=7)
GONE = "DeviceNotRegistered"

Kind = NotificationKind
# Android channel (the app creates them; each can be muted in the phone's settings), priority.
CHANNELS = {
    Kind.TIMETABLE_CHANGE_PROPOSED: ("class-changes", "high"),
    Kind.TIMETABLE_CHANGE_RETRACTED: ("class-changes", "high"),
    Kind.DIRECT_ATTENTION: ("needs-you", "high"),
    Kind.ACTION_REQUIRED: ("needs-you", "high"),
    Kind.IMPORTANT_UPDATE: ("needs-you", "high"),
    Kind.DIGEST: ("digest", "normal"),
    Kind.SYSTEM: ("general", "normal"),
}
# The PushSettings switch for each kind; `system` (from UniFlow) always goes out.
SWITCHES = {
    Kind.TIMETABLE_CHANGE_PROPOSED: "class_changes",
    Kind.TIMETABLE_CHANGE_RETRACTED: "class_changes",
    Kind.DIRECT_ATTENTION: "needs_you",
    Kind.ACTION_REQUIRED: "needs_you",
    Kind.IMPORTANT_UPDATE: "needs_you",
    Kind.DIGEST: "daily_digest",
}


class ExpoUnavailable(Exception):
    """Expo couldn't be reached or is busy (network error, HTTP 429 or 5xx): try again later."""


# --- 1. Choosing what to push -----------------------------------------------------------------


def skip_old() -> int:
    """Rows too old to push are claimed without a push (e.g. after a long outage)."""
    now = timezone.now()
    return Notification.objects.filter(pushed_at__isnull=True, created_at__lt=now - MAX_AGE).update(
        pushed_at=now
    )


def claim() -> int:
    """Claim up to CLAIM_BATCH new rows and make their tickets. Rows locked by another run are
    skipped, and a claimed row is never claimed again, so nothing is pushed twice."""
    with transaction.atomic():
        alerts = list(
            Notification.objects.select_for_update(skip_locked=True)
            .filter(pushed_at__isnull=True)
            .order_by("id")[:CLAIM_BATCH]
        )
        if not alerts:
            return 0
        Notification.objects.filter(id__in=[a.id for a in alerts]).update(pushed_at=timezone.now())
        PushTicket.objects.bulk_create(_tickets_for(alerts), ignore_conflicts=True)
    return len(alerts)


def _tickets_for(alerts: list[Notification]) -> list[PushTicket]:
    recipients = {alert.recipient_id for alert in alerts}
    allowed = set(
        get_user_model()
        .objects.filter(id__in=recipients, is_active=True, is_suspended=False)
        .values_list("id", flat=True)
    )
    switches = {s.user_id: s for s in PushSettings.objects.filter(user_id__in=recipients)}
    phones: dict[int, list[Device]] = {}
    for device in Device.objects.filter(user_id__in=allowed, is_active=True):
        phones.setdefault(device.user_id, []).append(device)

    tickets = []
    for alert in alerts:
        switch = SWITCHES.get(alert.kind)
        mine = switches.get(alert.recipient_id)
        if alert.recipient_id not in allowed or (switch and mine and not getattr(mine, switch)):
            continue
        for device in phones.get(alert.recipient_id, []):
            if device.created_at <= alert.created_at:  # a new phone gets no older alerts
                tickets.append(PushTicket(notification=alert, device=device))
    return tickets


# --- 2. Sending -----------------------------------------------------------------------------


def message(ticket: PushTicket, badge: int) -> dict:
    """What Expo delivers. `data` is exactly what the app reads (it works out the page
    itself, so it never contains a link)."""
    alert = ticket.notification
    channel, priority = CHANNELS.get(alert.kind, ("general", "normal"))
    return {
        "to": ticket.device.expo_token,
        "title": alert.title,
        "body": alert.body,
        "data": {
            "v": 1,
            "notification_id": alert.id,
            "target_type": alert.target_type,
            "target_id": alert.target_id,
        },
        "channelId": channel,
        "priority": priority,
        "sound": "default",
        "badge": badge,  # iPhone: the same number as the bell
    }


def _post(url: str, body: object) -> httpx.Response:
    try:
        response = httpx.post(
            url,
            json=body,
            headers={"Authorization": f"Bearer {settings.EXPO_ACCESS_TOKEN}"},
            timeout=TIMEOUT,
        )
    except httpx.HTTPError as error:
        raise ExpoUnavailable(type(error).__name__) from None  # the error may quote the body
    if response.status_code == 429 or response.status_code >= 500:
        raise ExpoUnavailable(f"HTTP {response.status_code}")
    return response


def send_pending() -> dict[str, int]:
    """Send the pending tickets (younger than an hour; older ones are given up). Raises
    ExpoUnavailable when Expo can't take them: those not sent yet stay pending."""
    now = timezone.now()
    expired = PushTicket.objects.filter(
        status=PushTicket.Status.PENDING, created_at__lt=now - MAX_AGE
    ).update(status=PushTicket.Status.ERROR, error="expired", updated_at=now)
    counts = {"ok": 0, "error": 0, "expired": expired}
    pending = list(
        PushTicket.objects.filter(status=PushTicket.Status.PENDING)
        .select_related("notification", "device")
        .order_by("id")
    )
    for start in range(0, len(pending), SEND_BATCH):
        batch = pending[start : start + SEND_BATCH]
        for status, count in _send_batch(batch).items():
            counts[status] += count
    return counts


def _unread_counts(user_ids: set[int]) -> dict[int, int]:
    rows = (
        Notification.objects.filter(recipient_id__in=user_ids, read_at__isnull=True)
        .values("recipient_id")
        .annotate(count=Count("id"))
    )
    return {row["recipient_id"]: row["count"] for row in rows}


def _send_batch(batch: list[PushTicket]) -> dict[str, int]:
    unread = _unread_counts({ticket.notification.recipient_id for ticket in batch})
    messages = [message(t, unread.get(t.notification.recipient_id, 0)) for t in batch]
    response = _post(SEND_URL, messages)
    if response.status_code != 200:  # a mistake in the request itself: trying again won't help
        logger.error("Expo refused %s pushes: HTTP %s", len(batch), response.status_code)
        _finish(batch, [{"status": "error", "details": {"error": f"http_{response.status_code}"}}])
        return {"error": len(batch)}
    answers = response.json().get("data", [])
    if len(answers) != len(batch):
        logger.error("Expo answered %s tickets for %s pushes", len(answers), len(batch))
        answers = [{"status": "error", "details": {"error": "no_answer"}}]
    return _finish(batch, answers)


def _finish(batch: list[PushTicket], answers: list[dict]) -> dict[str, int]:
    """Store Expo's answer on each ticket (one answer for all when there's only one)."""
    counts = {"ok": 0, "error": 0}
    gone = []
    for index, ticket in enumerate(batch):
        answer = answers[index] if len(answers) > 1 else answers[0]
        if answer.get("status") == "ok":
            ticket.status, ticket.expo_id = PushTicket.Status.OK, str(answer.get("id", ""))[:100]
        else:
            ticket.status = PushTicket.Status.ERROR
            ticket.error = str((answer.get("details") or {}).get("error") or "error")[:50]
            if ticket.error == GONE:
                gone.append(ticket.device_id)
            logger.warning("Push ticket %s failed: %s", ticket.id, ticket.error)
        counts[ticket.status] += 1
    PushTicket.objects.bulk_update(batch, ["status", "expo_id", "error"])
    switch_off(gone)
    return counts


def switch_off(device_ids: list[int], reason: str = Device.Reason.NOT_REGISTERED) -> int:
    if not device_ids:
        return 0
    logger.info("Switching off devices %s: %s", sorted(set(device_ids)), reason)
    return Device.objects.filter(id__in=device_ids, is_active=True).update(
        is_active=False, deactivated_reason=reason, updated_at=timezone.now()
    )


# --- 3. Receipts and clean-up -----------------------------------------------------------------


def check_receipts() -> dict[str, int]:
    """Ask Expo what happened to tickets sent 15 minutes to 24 hours ago."""
    now = timezone.now()
    tickets = list(
        PushTicket.objects.filter(
            status=PushTicket.Status.OK,
            receipt="",
            created_at__lte=now - RECEIPT_WAIT,
            created_at__gte=now - RECEIPT_KEPT,
        ).exclude(expo_id="")
    )
    counts = {"ok": 0, "error": 0}
    for start in range(0, len(tickets), RECEIPT_BATCH):
        batch = {t.expo_id: t for t in tickets[start : start + RECEIPT_BATCH]}
        response = _post(RECEIPTS_URL, {"ids": list(batch)})
        if response.status_code != 200:
            logger.error("Expo refused a receipts request: HTTP %s", response.status_code)
            continue
        gone, checked = [], []
        for expo_id, receipt in (response.json().get("data") or {}).items():
            ticket = batch.get(expo_id)
            if ticket is None:
                continue
            if receipt.get("status") == "ok":
                ticket.receipt = "ok"
            else:
                ticket.receipt = str((receipt.get("details") or {}).get("error") or "error")[:50]
                _log_receipt(ticket)
                if ticket.receipt == GONE:
                    gone.append(ticket.device_id)
            counts["ok" if ticket.receipt == "ok" else "error"] += 1
            checked.append(ticket)
        PushTicket.objects.bulk_update(checked, ["receipt"])
        switch_off(gone)
    return counts


def _log_receipt(ticket: PushTicket) -> None:
    if ticket.receipt in {"InvalidCredentials", "MismatchSenderId"}:
        # The Firebase or Apple set-up in Expo is wrong: no phone will get anything.
        logger.error("Push ticket %s: %s", ticket.id, ticket.receipt)
    else:
        logger.warning("Push ticket %s: %s", ticket.id, ticket.receipt)


def delete_old_tickets() -> int:
    deleted, _ = PushTicket.objects.filter(created_at__lt=timezone.now() - TICKETS_KEPT).delete()
    return deleted


def switch_off_stale_devices() -> int:
    """Phones not used for longer than a login lasts: the session there has ended anyway, so
    a student who never logged out stops getting alerts on it."""
    cutoff = timezone.now() - settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    stale = Device.objects.filter(is_active=True, last_seen_at__lt=cutoff)
    return switch_off(list(stale.values_list("id", flat=True)), Device.Reason.STALE)
