"""People who asked not to be read (M9.3): their messages are skipped everywhere."""

import json
import time
from datetime import UTC, datetime

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.intelligence import services
from apps.intelligence.connector import sign
from apps.intelligence.models import (
    ExcludedSender,
    Insight,
    InsightEvidence,
    Message,
    Source,
    SourceMember,
)

pytestmark = pytest.mark.django_db

CHAT = """01/10/2026, 09:12 - Dr Lee: Class moved to 2 PM.
01/10/2026, 09:13 - Sara: Which room?
"""


@pytest.fixture
def group():
    return Source.objects.create(platform="manual", title="CDE2313 Sec A")


@pytest.fixture
def admin_user():
    return User.objects.create_superuser("admin@aiu.edu.my", "Str0ng-pass-99", full_name="Admin")


def test_excluding_erases_their_stored_words(group, admin_user):
    services.store_messages(group, services.whatsapp_export.parse(CHAT))  # Dr Lee and Sara
    lee = Message.objects.get(sender_name="Dr Lee")
    insight = Insight.objects.create(
        audience=Audience.objects.create(), kind="class_moved", title="Moved", summary="…"
    )
    InsightEvidence.objects.create(insight=insight, message=lee, quote="Class moved to 2 PM.")

    excluded = services.exclude_sender(lee, admin_user, reason="Asked by email")

    lee.refresh_from_db()
    assert (lee.text, lee.triage, lee.text_deleted_at is not None) == ("", "noise", True)
    assert InsightEvidence.objects.get().quote == services.REMOVED_QUOTE
    assert Message.objects.get(sender_name="Sara").text == "Which room?"  # others untouched
    assert (excluded.sender_name, excluded.reason, excluded.added_by) == (
        "Dr Lee",
        "Asked by email",
        admin_user,
    )


def test_pasted_and_exported_messages_from_them_are_skipped(group, admin_user):
    services.store_messages(group, services.whatsapp_export.parse(CHAT))
    services.exclude_sender(Message.objects.get(sender_name="Sara"), admin_user)
    Message.objects.all().delete()

    added, _ = services.store_messages(group, services.whatsapp_export.parse(CHAT))
    assert added == 1
    assert list(Message.objects.values_list("sender_name", flat=True)) == ["Dr Lee"]

    member = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    SourceMember.objects.create(source=group, user=member)
    assert services.paste_messages(member, group, text="Hi all", sender_name="Sara") == (0, 0)


def test_telegram_messages_from_them_are_skipped(settings, admin_user):
    settings.TELEGRAM_WEBHOOK_SECRET = "secret"

    def send(message_id, sender_id):
        update = {
            "update_id": message_id,
            "message": {
                "message_id": message_id,
                "date": 1790000000,
                "chat": {"id": -1001, "type": "supergroup", "title": "SCI"},
                "from": {"id": sender_id, "first_name": f"User {sender_id}"},
                "text": "Hello",
            },
        }
        APIClient().post(
            "/api/v1/integrations/telegram/webhook/",
            update,
            format="json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="secret",
        )

    send(1, sender_id=42)
    services.exclude_sender(Message.objects.get(), admin_user)
    send(2, sender_id=42)
    send(3, sender_id=7)

    assert list(Message.objects.order_by("id").values_list("external_id", flat=True)) == ["1", "3"]


def test_whatsapp_connector_messages_from_them_are_skipped(settings, admin_user):
    settings.CONNECTOR_SECRET = "secret"
    Source.objects.create(
        platform="whatsapp_group", external_id="1@g.us", title="SCI", status="active"
    )

    def send(message_id):
        body = json.dumps(
            {
                "source_external_id": "1@g.us",
                "message_id": message_id,
                "sender_ref": "123@lid",
                "sender_name": "Omar",
                "text": "Hello",
                "sent_at": "2026-10-05T09:00:00+08:00",
            }
        ).encode()
        stamp = str(int(time.time()))
        path = "/api/v1/internal/messages/"
        return APIClient().generic(
            "POST",
            path,
            body,
            "application/json",
            HTTP_X_UNIFLOW_TIMESTAMP=stamp,
            HTTP_X_UNIFLOW_SIGNATURE=sign("secret", stamp, "POST", path, body),
        )

    assert send("A1").status_code == 201
    services.exclude_sender(Message.objects.get(), admin_user)

    response = send("A2")
    assert (response.status_code, response.json()) == (
        200,
        {"id": None, "created": False, "skipped": True},
    )
    assert Message.objects.count() == 1


def test_the_admin_action(group, admin_user, client):
    services.store_messages(group, services.whatsapp_export.parse(CHAT))
    client.force_login(admin_user)

    client.post(
        "/django-admin/intelligence/message/",
        {
            "action": "exclude_senders",
            "_selected_action": [Message.objects.get(sender_name="Sara").pk],
        },
    )

    assert list(ExcludedSender.objects.values_list("sender_name", flat=True)) == ["Sara"]
    assert Message.objects.get(sender_name="Sara").text == ""


def test_a_message_without_a_sender_cannot_be_excluded(group, admin_user):
    message = Message.objects.create(
        source=group, external_id="x", text="Hi", sent_at=datetime(2026, 10, 5, tzinfo=UTC)
    )
    with pytest.raises(ValidationError):
        services.exclude_sender(message, admin_user)
