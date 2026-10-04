"""Getting messages into UniFlow by hand: groups for pasted messages, pasting, and
uploading a WhatsApp "Export chat" file. The connectors (M6) reuse store_messages().
Also the daily privacy clean-up of old message text and files (clear_old_messages), and
saving what the AI found (save_ai_insight).

The same message is never stored twice: each one gets a fingerprint (time, sender and
text) as its id, so pasting or uploading the same chat again adds nothing.
"""

import hashlib
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audiences.models import Audience
from apps.publishing.models import PublisherType
from apps.publishing.services import publish

from . import whatsapp_export
from .models import UNSURE, Insight, InsightEvidence, Message, MessageFile, Source, SourceMember
from .whatsapp_export import ParsedMessage

MAX_EXPORT_BYTES = 5 * 1024 * 1024  # 5 MB of text is years of a busy group


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


@transaction.atomic
def create_manual_source(user, *, title: str, **scope) -> Source:
    """A group for pasted or uploaded messages; the creator is its first member."""
    source = Source.objects.create(
        platform=Source.Platform.MANUAL,
        title=title.strip(),
        status=Source.Status.ACTIVE,
        connected_by=user,
        joined_at=timezone.now(),
        **scope,
    )
    SourceMember.objects.create(source=source, user=user)
    return source


def require_member(user, source: Source) -> None:
    """Only students who added the group (and super admins) may add messages to it."""
    is_member = SourceMember.objects.filter(source=source, user=user).exists()
    if not (is_member or user.is_superuser):
        raise PermissionDenied("Add this group to your groups first.")


def store_messages(source: Source, parsed: list[ParsedMessage]) -> tuple[int, int]:
    """Save messages that aren't stored yet. Returns (added, already there)."""
    rows = [
        Message(
            source=source,
            external_id="fp:" + _hash(item.sent_at.isoformat(), item.sender_name, item.text)[:60],
            sender_name=item.sender_name[:150],
            sender_ref=_hash(item.sender_name)[:16] if item.sender_name else "",
            text=item.text,
            sent_at=item.sent_at,
        )
        for item in parsed
    ]
    # Fingerprints already stored for this group, plus repeats inside this batch.
    known = set(
        Message.objects.filter(
            source=source, external_id__in=[row.external_id for row in rows]
        ).values_list("external_id", flat=True)
    )
    new_rows = []
    for row in rows:
        if row.external_id not in known:
            known.add(row.external_id)
            new_rows.append(row)
    Message.objects.bulk_create(new_rows)
    if new_rows:
        queue_triage(source)
    return len(new_rows), len(rows) - len(new_rows)


def queue_triage(source: Source) -> None:
    """Ask the background worker to sort the new messages, once the save is committed."""
    from .tasks import triage_source  # tasks imports this module

    transaction.on_commit(lambda: triage_source.delay(source.id))


def paste_messages(user, source: Source, *, text: str, sender_name: str = "") -> tuple[int, int]:
    """Text copied from WhatsApp becomes separate messages; anything else is one message."""
    require_member(user, source)
    if not whatsapp_export.looks_like_whatsapp(text):
        return _store_plain_message(source, text, sender_name)
    parsed = whatsapp_export.parse(text)
    if not parsed:
        raise ValidationError({"text": "No messages found in this text."})
    return store_messages(source, parsed)


def _store_plain_message(source: Source, text: str, sender_name: str) -> tuple[int, int]:
    """A message without WhatsApp's date and time counts as sent "now". Its fingerprint
    leaves the time out, so pasting it again is still recognised."""
    _, created = Message.objects.get_or_create(
        source=source,
        external_id="fp:" + _hash("plain", sender_name, text)[:60],
        defaults={
            "sender_name": sender_name[:150],
            "sender_ref": _hash(sender_name)[:16] if sender_name else "",
            "text": text,
            "sent_at": timezone.now(),
        },
    )
    if created:
        queue_triage(source)
    return (1, 0) if created else (0, 1)


def import_whatsapp_export(user, source: Source, uploaded_file) -> tuple[int, int]:
    """A WhatsApp "Export chat" .txt file becomes messages in this group."""
    require_member(user, source)
    if not uploaded_file.name.lower().endswith(".txt"):
        raise ValidationError({"file": 'Upload the .txt file from WhatsApp\'s "Export chat".'})
    if uploaded_file.size > MAX_EXPORT_BYTES:
        raise ValidationError({"file": "The file is too large (5 MB at most)."})
    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValidationError({"file": "This doesn't look like a WhatsApp chat export."}) from None
    parsed = whatsapp_export.parse(text)
    if not parsed:
        raise ValidationError({"file": "No messages found in this file."})
    return store_messages(source, parsed)


def clear_old_messages(now=None) -> dict[str, int]:
    """Privacy: blank the text of messages older than MESSAGE_RETENTION_DAYS and delete old
    timetable files. The message rows stay (sender, time), and so does anything already
    learned from them (classes, and from M5 the insights with their short quotes).
    """
    now = now or timezone.now()
    cutoff = now - timedelta(days=settings.MESSAGE_RETENTION_DAYS)

    cleared = Message.objects.filter(sent_at__lt=cutoff, text_deleted_at__isnull=True).update(
        text="", raw={}, text_deleted_at=now
    )

    old_files = MessageFile.objects.filter(file_deleted_at__isnull=True).filter(
        Q(message__sent_at__lt=cutoff) | Q(message__isnull=True, created_at__lt=cutoff)
    )
    deleted_files = 0
    for stored in old_files:
        if stored.file:
            stored.file.delete(save=False)  # removes it from the disk
        stored.file = ""
        stored.file_deleted_at = now
        stored.save(update_fields=["file", "file_deleted_at", "updated_at"])
        deleted_files += 1

    return {"messages_cleared": cleared, "files_deleted": deleted_files}


AUDIENCE_LISTS = ("schools", "programmes", "intakes", "courses", "sections")


@transaction.atomic
def save_ai_insight(
    *,
    source: Source,
    kind: str,
    title: str,
    summary: str,
    confidence: float,
    evidence: list[tuple[Message, str]],
    audience: dict | None = None,
    **fields,
) -> Insight:
    """Store what the AI found, linked to its messages, and apply the "how sure" rule:
    sure (>= CONFIDENT) or unsure (>= UNSURE) -> published; very unsure -> draft."""
    audience = audience or {}
    target = Audience.objects.create(
        semester_min=audience.get("semester_min"), semester_max=audience.get("semester_max")
    )
    for name in AUDIENCE_LISTS:
        getattr(target, name).set(audience.get(name, []))

    insight = Insight.objects.create(
        audience=target,
        publisher_type=PublisherType.SOURCE,
        publisher_source=source,
        origin=Insight.Origin.AI,
        kind=kind,
        title=title[:200],
        summary=summary[:500],
        confidence=confidence,
        **fields,
    )
    InsightEvidence.objects.bulk_create(
        InsightEvidence(insight=insight, message=message, quote=quote[:500])
        for message, quote in evidence
    )
    if confidence >= UNSURE:
        publish(insight, None)
    return insight
