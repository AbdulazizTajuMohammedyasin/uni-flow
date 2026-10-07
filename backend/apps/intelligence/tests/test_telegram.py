"""The Telegram bot webhook, with made-up updates (nothing is sent to Telegram)."""

from datetime import UTC, datetime
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from rest_framework.test import APIClient

from apps.intelligence import telegram
from apps.intelligence.models import Message, MessageFile, Source
from apps.intelligence.providers import fake_provider

pytestmark = pytest.mark.django_db

WEBHOOK = "/api/v1/integrations/telegram/webhook/"
SECRET = "test-secret-123"
GROUP = {"id": -1001234, "type": "supergroup", "title": "CDE2313 Section A"}
CHANNEL = {"id": -1009999, "type": "channel", "title": "AIU Announcements"}
PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
SENT = 1790000000  # a Unix time, as Telegram sends it


@pytest.fixture(autouse=True)
def bot(settings, tmp_path):
    settings.TELEGRAM_BOT_TOKEN = "123:fake-token"
    settings.TELEGRAM_WEBHOOK_SECRET = SECRET
    settings.MEDIA_ROOT = tmp_path


def send(update, secret=SECRET):
    headers = {"HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN": secret} if secret else {}
    return APIClient().post(WEBHOOK, update, format="json", **headers)


def message(message_id=1, text="CDE2313 class tomorrow moves to 2pm", chat=GROUP, **extra):
    return {
        "update_id": 500 + message_id,
        "message": {
            "message_id": message_id,
            "date": SENT,
            "chat": chat,
            "from": {"id": 42, "is_bot": False, "first_name": "Lee", "last_name": "Wong"},
            "text": text,
        }
        | extra,
    }


def test_a_group_message_is_stored_once_and_sorted_by_the_ai(django_capture_on_commit_callbacks):
    fake_provider().answers.append({"results": [{"id": 0, "academic": True}]})
    with django_capture_on_commit_callbacks(execute=True):
        assert send(message()).status_code == 200
    assert send(message()).status_code == 200  # Telegram sent it again

    stored = Message.objects.get()
    assert stored.text == "CDE2313 class tomorrow moves to 2pm"
    assert stored.sender_name == "Lee Wong"
    assert stored.sender_ref and "42" not in stored.sender_ref  # only a hash of the id
    assert stored.sent_at == datetime.fromtimestamp(SENT, tz=UTC)
    assert stored.external_id == "1"
    source = stored.source
    assert (source.platform, source.external_id) == ("telegram_group", "-1001234")
    assert (source.title, source.status) == ("CDE2313 Section A", "active")
    assert stored.triage == "relevant"  # the AI sorted it…
    assert len(fake_provider().calls) == 2  # …then looked for timetable changes


@pytest.mark.parametrize("secret", ["wrong", None])
def test_a_wrong_or_missing_secret_is_refused(secret):
    assert send(message(), secret=secret).status_code == 403
    assert Message.objects.count() == 0


def test_no_secret_configured_refuses_everything(settings):
    settings.TELEGRAM_WEBHOOK_SECRET = ""
    assert send(message(), secret="").status_code == 403


def test_a_channel_post_and_a_reply():
    post = message(chat=CHANNEL, text="Exam timetable is out.")
    post["channel_post"] = post.pop("message")
    del post["channel_post"]["from"]
    post["channel_post"]["author_signature"] = "Registrar"
    send(post)
    send(message(2, "Thanks!", chat=CHANNEL, reply_to_message={"message_id": 1}))

    first, reply = Message.objects.order_by("id")
    assert first.source.platform == "telegram_channel"
    assert first.sender_name == "Registrar"
    assert reply.reply_to == first


def test_private_chats_joins_and_stickers_are_ignored():
    send(message(chat={"id": 42, "type": "private"}))
    send(message(2, text=""))  # e.g. "Ali joined the group"
    assert Message.objects.count() == 0


def test_the_bot_added_and_removed(django_capture_on_commit_callbacks):
    def membership(status):
        return {
            "update_id": 1,
            "my_chat_member": {"chat": GROUP, "new_chat_member": {"status": status}},
        }

    send(membership("administrator"))
    assert Source.objects.get().status == "active"

    send(membership("kicked"))
    assert Source.objects.get().status == "disconnected"
    send(message())
    assert Message.objects.count() == 0  # a disconnected group isn't read


def test_a_group_that_became_a_supergroup_keeps_its_messages():
    old = {"id": -555, "type": "group", "title": "SCI Year 1"}
    send(message(chat=old))
    send(message(2, chat=old, migrate_to_chat_id=-1005550000))

    source = Source.objects.get()
    assert source.external_id == "-1005550000"
    send(message(3, chat={**old, "id": -1005550000, "type": "supergroup"}))
    assert source.messages.count() == 2


def test_a_pdf_is_downloaded_then_sorted(monkeypatch, django_capture_on_commit_callbacks):
    asked = []

    def get_file(method, **params):
        asked.append(params)
        return {"file_path": "d/1"}

    monkeypatch.setattr(telegram, "call", get_file)
    monkeypatch.setattr(telegram, "download_file", lambda path: PDF)
    document = {"file_id": "abc", "file_name": "timetable.pdf", "mime_type": "application/pdf"}

    with django_capture_on_commit_callbacks(execute=True):
        send(message(text="", caption="New timetable", document=document))

    stored = MessageFile.objects.get()
    assert stored.message.text == "New timetable"
    assert (stored.kind, stored.original_name) == ("pdf", "timetable.pdf")
    assert asked == [{"file_id": "abc"}]
    assert Message.objects.get().triage == "relevant"  # a file counts as academic


def test_a_fake_pdf_is_not_kept(monkeypatch, django_capture_on_commit_callbacks):
    monkeypatch.setattr(telegram, "call", lambda method, **p: {"file_path": "d/1"})
    monkeypatch.setattr(telegram, "download_file", lambda path: b"not really a pdf")
    document = {"file_id": "abc", "file_name": "x.pdf", "mime_type": "application/pdf"}
    fake_provider().answers.append({"results": []})

    with django_capture_on_commit_callbacks(execute=True):
        send(message(text="see file", document=document))

    assert MessageFile.objects.count() == 0
    assert Message.objects.count() == 1


def test_a_broken_update_still_gets_200():
    assert send({"update_id": 9, "message": {"message_id": 1}}).status_code == 200


def test_set_webhook_command(monkeypatch):
    asked = []
    monkeypatch.setattr(telegram, "call", lambda method, **p: asked.append((method, p)) or True)
    out = StringIO()

    call_command("set_telegram_webhook", "https://uniflow.example.com/", stdout=out)

    [(method, params)] = asked
    assert method == "setWebhook"
    assert params["url"] == f"https://uniflow.example.com{WEBHOOK}"
    assert params["secret_token"] == SECRET
    assert params["allowed_updates"] == ["message", "channel_post", "my_chat_member"]
    assert "123:fake-token" not in out.getvalue()
    with pytest.raises(CommandError):
        call_command("set_telegram_webhook", "http://not-https.example.com")
