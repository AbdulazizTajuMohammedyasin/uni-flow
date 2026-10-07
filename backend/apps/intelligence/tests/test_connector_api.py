"""The WhatsApp connector's private addresses (/api/v1/internal/), with signed requests."""

import json
import time

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import BOUNDARY, MULTIPART_CONTENT, encode_multipart
from rest_framework.test import APIClient

from apps.accounts.services import create_user
from apps.intelligence.connector import sign
from apps.intelligence.models import Message, MessageFile, Source, SourceMember
from apps.intelligence.providers import fake_provider

pytestmark = pytest.mark.django_db

SECRET = "connector-secret-123"
PENDING = "/api/v1/internal/sources/pending/"
JOINED = "/api/v1/internal/sources/joined/"
MESSAGES = "/api/v1/internal/messages/"
GROUP_ID = "120363000000000001@g.us"
PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


@pytest.fixture(autouse=True)
def secret(settings, tmp_path):
    settings.CONNECTOR_SECRET = SECRET
    settings.MEDIA_ROOT = tmp_path


def signed(method, path, body=b"", content_type="application/json", *, key=SECRET, age=0):
    """A request the way the connector sends it."""
    timestamp = str(int(time.time()) - age)
    headers = {
        "HTTP_X_UNIFLOW_TIMESTAMP": timestamp,
        "HTTP_X_UNIFLOW_SIGNATURE": sign(key, timestamp, method, path, body),
    }
    client = APIClient()
    if method == "GET":
        return client.get(path, **headers)
    return client.generic(method, path, body, content_type, **headers)


def post_json(path, data, **options):
    return signed("POST", path, json.dumps(data).encode(), **options)


def joined_group():
    return Source.objects.create(
        platform=Source.Platform.WHATSAPP_GROUP,
        external_id=GROUP_ID,
        title="SCI Year 1",
        status=Source.Status.ACTIVE,
    )


def new_message(message_id="ABC1", **fields):
    return {
        "source_external_id": GROUP_ID,
        "message_id": message_id,
        "sender_ref": "60123456789@s.whatsapp.net",
        "sender_name": "Dr Lee",
        "text": "CDE2313 class tomorrow moves to 2pm",
        "sent_at": "2026-10-05T09:00:00+08:00",
    } | fields


@pytest.mark.parametrize(
    "options",
    [
        {"key": "wrong-secret"},  # forged
        {"age": 6 * 60},  # an old request sent again later
    ],
)
def test_bad_signature_or_old_timestamp_is_refused(options):
    assert signed("GET", PENDING, **options).status_code == 403


def test_unsigned_or_changed_requests_are_refused():
    assert APIClient().get(PENDING).status_code == 403
    joined_group()
    timestamp = str(int(time.time()))
    signature = sign(SECRET, timestamp, "POST", MESSAGES, json.dumps(new_message()).encode())
    changed = json.dumps(new_message(text="All classes cancelled!"))  # body swapped
    response = APIClient().generic(
        "POST",
        MESSAGES,
        changed,
        "application/json",
        HTTP_X_UNIFLOW_TIMESTAMP=timestamp,
        HTTP_X_UNIFLOW_SIGNATURE=signature,
    )
    assert response.status_code == 403
    assert Message.objects.count() == 0


def test_no_secret_configured_refuses_everything(settings):
    settings.CONNECTOR_SECRET = ""
    assert signed("GET", PENDING, key="").status_code == 403


def test_pending_groups_and_joining_one():
    student = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    waiting = Source.objects.create(
        platform=Source.Platform.WHATSAPP_GROUP,
        title="CDE2313 Section A",
        invite_url="https://chat.whatsapp.com/AbCdEf123",
    )
    SourceMember.objects.create(source=waiting, user=student)

    assert signed("GET", PENDING).json() == [
        {"id": waiting.id, "title": "CDE2313 Section A", "invite_url": waiting.invite_url}
    ]

    response = post_json(
        JOINED,
        {
            "source_id": waiting.id,
            "external_id": GROUP_ID,
            "title": "CDE2313 A",
            "notice_sent": True,
        },
    )
    assert response.json() == {"id": waiting.id, "status": "active"}
    waiting.refresh_from_db()
    assert (waiting.external_id, waiting.title) == (GROUP_ID, "CDE2313 A")
    assert waiting.joined_at and waiting.notice_sent_at
    assert signed("GET", PENDING).json() == []


def test_a_second_link_to_a_group_already_joined_keeps_one_group():
    group = joined_group()
    sara = create_user("sara@student.aiu.edu.my", "Str0ng-pass-99", full_name="Sara")
    duplicate = Source.objects.create(
        platform=Source.Platform.WHATSAPP_GROUP,
        title="Year 1",
        invite_url="https://chat.whatsapp.com/Other",
    )
    SourceMember.objects.create(source=duplicate, user=sara)

    post_json(JOINED, {"source_id": duplicate.id, "external_id": GROUP_ID, "title": "SCI Year 1"})

    assert list(Source.objects.all()) == [group]
    assert group.members.get().user == sara


def test_added_to_a_group_directly():
    post_json(JOINED, {"external_id": GROUP_ID, "title": "AIU Notices"})
    source = Source.objects.get()
    assert (source.platform, source.status) == ("whatsapp_group", "active")
    assert source.title == "AIU Notices"


def test_a_message_is_stored_once_and_sorted(django_capture_on_commit_callbacks):
    joined_group()
    fake_provider().answers.extend([{"results": []}, {"changes": []}])

    with django_capture_on_commit_callbacks(execute=True):
        first = post_json(MESSAGES, new_message())
    again = post_json(MESSAGES, new_message())

    assert (first.status_code, first.json()["created"]) == (201, True)
    assert (again.status_code, again.json()["created"]) == (200, False)
    stored = Message.objects.get()
    assert stored.text == "CDE2313 class tomorrow moves to 2pm"
    assert stored.sender_name == "Dr Lee"
    assert "60123456789" not in stored.sender_ref  # never the phone number
    assert stored.triage == "relevant"


def test_a_reply_and_an_unknown_group():
    joined_group()
    post_json(MESSAGES, new_message("ABC1"))
    post_json(MESSAGES, new_message("ABC2", text="Same room?", reply_to="ABC1"))
    first, reply = Message.objects.order_by("id")
    assert reply.reply_to == first

    unknown = post_json(MESSAGES, new_message("X", source_external_id="999@g.us"))
    assert unknown.status_code == 404


def test_a_message_with_a_file(django_capture_on_commit_callbacks):
    joined_group()
    created = post_json(MESSAGES, new_message(text="", has_files=True))
    message = Message.objects.get(pk=created.json()["id"])
    assert message.triage == "pending"  # waits for its file

    path = f"{MESSAGES}{message.id}/files/"
    body = encode_multipart(BOUNDARY, {"file": SimpleUploadedFile("timetable.pdf", PDF)})
    with django_capture_on_commit_callbacks(execute=True):
        response = signed("POST", path, body, MULTIPART_CONTENT)

    assert response.status_code == 201
    stored = MessageFile.objects.get()
    assert (stored.message, stored.kind, stored.original_name) == (message, "pdf", "timetable.pdf")
    message.refresh_from_db()
    assert message.triage == "relevant"  # a file counts as academic


def test_a_fake_file_is_refused():
    joined_group()
    message_id = post_json(MESSAGES, new_message(has_files=True)).json()["id"]
    path = f"{MESSAGES}{message_id}/files/"
    body = encode_multipart(BOUNDARY, {"file": SimpleUploadedFile("timetable.pdf", b"not a pdf")})
    assert signed("POST", path, body, MULTIPART_CONTENT).status_code == 400
    assert MessageFile.objects.count() == 0
