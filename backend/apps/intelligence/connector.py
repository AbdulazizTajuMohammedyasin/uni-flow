"""The private addresses the WhatsApp connector uses (docs/08-messaging-integrations.md).

The connector (connectors/whatsapp/, M6.3) runs UniFlow's own WhatsApp number in a
separate program. It never touches the database; it calls /api/v1/internal/ to:
- ask which groups to join (pending_sources),
- say it joined a group (mark_joined),
- hand over each new group message (store_message) and its files (attach_file).

A student can also add UniFlow's number to a group themselves (services.add_by_number). That
group is linked to the student when UniFlow joins a group of the same name (mark_joined), or
when the student picks it from the groups UniFlow joined since (services.claim_group).

Every request is signed (ConnectorSignature): two headers,
    X-UniFlow-Timestamp: the Unix time in seconds, e.g. 1790000000
    X-UniFlow-Signature: hex HMAC-SHA256 of "<timestamp>.<METHOD>.<path>.<body>" with
                         CONNECTOR_SECRET (see sign())
so a forged request gets 403, and an old request replayed later (over 5 minutes) too.
"""

import hashlib
import hmac
import time

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission

from . import files, timetable_reading
from .models import Message, MessageFile, Source
from .services import is_excluded, merge_waiting_into, queue_triage

MAX_AGE_SECONDS = 5 * 60


def sign(secret: str, timestamp: str, method: str, path: str, body: bytes) -> str:
    """The signature the connector sends (the connector computes the same thing)."""
    signed = f"{timestamp}.{method.upper()}.{path}.".encode() + body
    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()


class ConnectorSignature(BasePermission):
    """Only correctly signed, recent requests from the connector get through."""

    message = "Bad or missing connector signature."

    def has_permission(self, request, view) -> bool:
        secret = settings.CONNECTOR_SECRET
        timestamp = request.headers.get("X-UniFlow-Timestamp", "")
        given = request.headers.get("X-UniFlow-Signature", "")
        if not secret or not timestamp.isdigit() or not given:
            return False
        if abs(time.time() - int(timestamp)) > MAX_AGE_SECONDS:
            return False
        expected = sign(secret, timestamp, request.method, request.path, request.body)
        return hmac.compare_digest(expected, given)


def _hash_sender(sender_ref: str) -> str:
    """Hashed again here, so a phone number can never be stored, even by mistake."""
    return hashlib.sha256(f"wa:{sender_ref}".encode()).hexdigest()[:16] if sender_ref else ""


def pending_sources():
    """WhatsApp groups students added that the connector hasn't joined yet."""
    return Source.objects.filter(
        platform=Source.Platform.WHATSAPP_GROUP, status=Source.Status.PENDING
    ).exclude(invite_url="")


def _same_name(a: str, b: str) -> bool:
    """ "CCS2213  HCI" and "ccs2213 hci" are the same group name."""
    return " ".join(a.split()).casefold() == " ".join(b.split()).casefold()


def _waiting_by_name(title: str) -> Source | None:
    """The one group a student is adding by number under this name (none if 0 or several)."""
    waiting = Source.objects.filter(
        platform=Source.Platform.WHATSAPP_GROUP,
        status=Source.Status.PENDING,
        added_by_number=True,
    )
    matches = [source for source in waiting if title and _same_name(source.title, title)]
    return matches[0] if len(matches) == 1 else None


@transaction.atomic
def mark_joined(*, external_id: str, title: str, source_id=None, notice_sent=False) -> Source:
    """The connector is now in a WhatsApp group. `source_id` is the pending group it
    joined from a student's link; without it, someone added UniFlow's number directly, and
    a group a student is adding by number under the same name is used."""
    pending = (
        Source.objects.filter(pk=source_id, platform=Source.Platform.WHATSAPP_GROUP).first()
        if source_id
        else _waiting_by_name(title)
    )
    existing = Source.objects.filter(
        platform=Source.Platform.WHATSAPP_GROUP, external_id=external_id
    ).first()
    if existing and pending and existing != pending:
        # Another student's link (or a group of the same name) is one UniFlow is already in.
        merge_waiting_into(existing, pending)
    source = existing or pending or Source(platform=Source.Platform.WHATSAPP_GROUP)
    source.external_id = external_id
    source.title = (title or source.title or "WhatsApp group")[:200]
    source.status = Source.Status.ACTIVE
    source.joined_at = source.joined_at or timezone.now()
    if notice_sent and not source.notice_sent_at:
        source.notice_sent_at = timezone.now()
    source.save()
    return source


def store_message(data: dict) -> tuple[Message | None, bool]:
    """Save a group message once. Returns (message, created); (None, False) when its sender
    asked not to be read. A message whose files are still coming is sorted by the AI after
    the last file arrives (attach_file)."""
    if is_excluded(_hash_sender(data.get("sender_ref", ""))):
        return None, False
    source = Source.objects.get(
        platform=Source.Platform.WHATSAPP_GROUP,
        external_id=data["source_external_id"],
        status=Source.Status.ACTIVE,
    )
    reply = (
        source.messages.filter(external_id=data["reply_to"]).first()
        if data.get("reply_to")
        else None
    )
    message, created = Message.objects.get_or_create(
        source=source,
        external_id=data["message_id"],
        defaults={
            "sender_name": data.get("sender_name", "")[:150],
            "sender_ref": _hash_sender(data.get("sender_ref", "")),
            "text": data.get("text", ""),
            "sent_at": data["sent_at"],
            "reply_to": reply,
        },
    )
    if created and not data.get("has_files"):
        queue_triage(source)
    return message, created


def attach_file(message: Message, uploaded_file) -> MessageFile:
    """An image, PDF or Excel file from a group message, checked like a student upload."""
    if uploaded_file.size > files.max_bytes():
        raise ValidationError({"file": f"Too large ({settings.MAX_UPLOAD_MB} MB at most)."})
    data = uploaded_file.read()
    kind, mime, extension, _ = files._check_contents(data, "file")
    stored = files._save(
        data,
        user=None,
        kind=kind,
        mime=mime,
        extension=extension,
        original_name=uploaded_file.name,
        message=message,
    )
    queue_triage(message.source)
    timetable_reading.offer_when_saved(stored)  # maybe a timetable for the group
    return stored
