"""The UniFlow Telegram bot (docs/08-messaging-integrations.md, "The Telegram bot").

Telegram sends every update to the webhook (views.TelegramWebhookView), and
handle_update() turns it into UniFlow data:
- a message in a group, or a post in a channel -> a Message in that chat's Source (the
  Source is created the first time). A photo, PDF or Excel file is downloaded in the
  background (fetch_file), then the AI sorts the message as usual.
- the bot added to or removed from a chat -> the Source becomes active or disconnected.
- a group upgraded by Telegram to a "supergroup" gets a new chat id -> the Source follows.
Private chats with the bot and edited messages are ignored for now.

Talking to Telegram uses Python's own urllib (no extra library). The bot token is part of
Telegram's addresses, so errors never include the address.
"""

import hashlib
import json
import logging
import urllib.error
import urllib.request
from datetime import UTC, datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from . import files
from .models import Message, Source
from .services import queue_triage

logger = logging.getLogger(__name__)

API = "https://api.telegram.org"
TIMEOUT_SECONDS = 15
GROUP_TYPES = {"group", "supergroup"}
UPDATES = ["message", "channel_post", "my_chat_member"]  # what the bot asks Telegram for


class TelegramError(Exception):
    """Telegram couldn't be reached or refused (the message never contains the token)."""


def call(method: str, **params):
    """Call a Bot API method, e.g. call("getFile", file_id=...). Returns its result."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN is not set.")
    request = urllib.request.Request(
        f"{API}/bot{token}/{method}",
        data=json.dumps(params).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read())
    except urllib.error.HTTPError as error:  # Telegram explains refusals in the body
        try:
            body = json.loads(error.read())
        except ValueError:
            body = {"description": f"HTTP {error.code}"}
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise TelegramError("Couldn't reach Telegram. Try again later.") from None
    if not body.get("ok"):
        raise TelegramError(f"Telegram said: {body.get('description', 'no reason given')}")
    return body["result"]


def download_file(file_path: str) -> bytes:
    """A file's contents (path from getFile), at most the upload limit plus one byte."""
    url = f"{API}/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            return response.read(files.max_bytes() + 1)
    except (urllib.error.URLError, TimeoutError):
        raise TelegramError("Couldn't download the file from Telegram.") from None


# --- Updates ------------------------------------------------------------------------------


def _platform(chat: dict) -> str | None:
    if chat.get("type") in GROUP_TYPES:
        return Source.Platform.TELEGRAM_GROUP
    if chat.get("type") == "channel":
        return Source.Platform.TELEGRAM_CHANNEL
    return None  # a private chat with the bot


def _source(chat: dict, platform: str) -> Source:
    """The chat's Source, created the first time UniFlow hears from it."""
    title = (chat.get("title") or "Telegram chat")[:200]
    source, created = Source.objects.get_or_create(
        platform=platform,
        external_id=str(chat["id"]),
        defaults={"title": title, "status": Source.Status.ACTIVE, "joined_at": timezone.now()},
    )
    if not created and chat.get("title") and source.title != title:
        source.title = title  # the group was renamed
        source.save(update_fields=["title", "updated_at"])
    return source


def _bot_membership(update: dict) -> None:
    """The bot was added to (or made admin of) a chat, or removed from it."""
    chat, status = update["chat"], update["new_chat_member"]["status"]
    platform = _platform(chat)
    if platform is None:
        return
    source = _source(chat, platform)
    if status in ("member", "administrator"):
        source.status, source.joined_at = Source.Status.ACTIVE, timezone.now()
    elif status in ("left", "kicked"):
        source.status = Source.Status.DISCONNECTED
    else:
        return
    source.save(update_fields=["status", "joined_at", "updated_at"])


def _sender(message: dict) -> tuple[str, str]:
    """(name shown, hash of the sender's Telegram id). A channel post, or a message an
    admin sent "as the group", has no person: the channel or group is the sender."""
    if "sender_chat" in message or "from" not in message:
        chat = message.get("sender_chat") or message["chat"]
        name = message.get("author_signature") or chat.get("title", "")
        sender_id = str(chat["id"])
    else:
        person = message["from"]
        name = " ".join(filter(None, [person.get("first_name"), person.get("last_name")]))
        sender_id = str(person["id"])
    return name[:150], hashlib.sha256(f"tg:{sender_id}".encode()).hexdigest()[:16]


def _attachment(message: dict) -> tuple[str, str] | None:
    """(Telegram file id, file name) of a photo, PDF or Excel file small enough to keep."""
    if message.get("photo"):
        item, name = message["photo"][-1], "photo.jpg"  # the largest size
    elif message.get("document", {}).get("mime_type") in files.ALLOWED_TYPES:
        item = message["document"]
        name = item.get("file_name") or "file"
    else:
        return None
    if item.get("file_size", 0) > files.max_bytes():
        return None
    return item["file_id"], name[:255]


def _store(source: Source, message: dict) -> Message | None:
    """Save a message once (Telegram may send the same update again)."""
    text = message.get("text") or message.get("caption") or ""
    attachment = _attachment(message)
    if not text.strip() and attachment is None:
        return None  # someone joined, a sticker, a poll…
    sender_name, sender_ref = _sender(message)
    reply = message.get("reply_to_message")
    stored, created = Message.objects.get_or_create(
        source=source,
        external_id=str(message["message_id"]),
        defaults={
            "sender_name": sender_name,
            "sender_ref": sender_ref,
            "text": text,
            "sent_at": datetime.fromtimestamp(message["date"], tz=UTC),
            "reply_to": source.messages.filter(external_id=str(reply["message_id"])).first()
            if reply
            else None,
            "raw": message,
        },
    )
    if not created:
        return stored
    if attachment:  # download first, then the AI sorts it (a file counts as academic)
        from .tasks import fetch_telegram_file  # tasks imports this module

        transaction.on_commit(lambda: fetch_telegram_file.delay(stored.id, *attachment))
    else:
        queue_triage(source)
    return stored


def handle_update(update: dict) -> None:
    """One update from Telegram (see the module docstring)."""
    if "my_chat_member" in update:
        _bot_membership(update["my_chat_member"])
        return
    message = update.get("message") or update.get("channel_post")
    if not message:
        return  # edited messages and other kinds aren't used yet
    chat = message["chat"]
    platform = _platform(chat)
    if platform is None:
        return
    if "migrate_to_chat_id" in message:  # the group became a supergroup with a new id
        Source.objects.filter(platform=platform, external_id=str(chat["id"])).update(
            external_id=str(message["migrate_to_chat_id"])
        )
        return
    source = _source(chat, platform)
    if source.status != Source.Status.DISCONNECTED:
        _store(source, message)


def fetch_file(message: Message, file_id: str, name: str) -> None:
    """Download a message's photo or document and keep it if it really is one we read."""
    info = call("getFile", file_id=file_id)
    data = download_file(info["file_path"])
    if len(data) > files.max_bytes():
        return
    try:
        kind, mime, extension, _ = files._check_contents(data, "file")
    except ValidationError:
        logger.info("Telegram file for message %s is not a type UniFlow reads.", message.id)
        return
    files._save(
        data,
        user=None,
        kind=kind,
        mime=mime,
        extension=extension,
        original_name=name,
        message=message,
    )
