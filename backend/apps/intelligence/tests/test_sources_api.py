import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.academics.models import School
from apps.accounts.services import create_user
from apps.intelligence import services
from apps.intelligence.models import Message, Source, SourceMember

pytestmark = pytest.mark.django_db

SOURCES = "/api/v1/sources/"
CHAT = """01/10/2026, 09:12 - Dr Lee: Tomorrow's CDE2313 class has been moved to 2 PM.
01/10/2026, 09:13 - Sara: Which room?
"""


def login(email):
    api = APIClient()
    api.force_authenticate(create_user(email, "Str0ng-pass-99", full_name=email))
    return api


@pytest.fixture
def ali():
    return login("ali@student.aiu.edu.my")


@pytest.fixture
def group(ali):
    return ali.post(SOURCES, {"title": "CDE2313 Sec A"}, format="json").json()


def export_file(text=CHAT, name="WhatsApp Chat with CDE2313.txt"):
    return SimpleUploadedFile(name, text.encode("utf-8"), content_type="text/plain")


def test_create_a_group_for_pasted_messages(ali):
    school = School.objects.create(code="SCI", name="Computing")
    response = ali.post(SOURCES, {"title": "SCI notices", "school": school.id}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["platform"] == "manual"
    assert body["status"] == "active"
    assert body["school"] == school.id
    source = Source.objects.get(pk=body["id"])
    assert SourceMember.objects.filter(source=source, user__email="ali@student.aiu.edu.my").exists()

    listed = ali.get(SOURCES).json()
    assert [(s["title"], s["message_count"]) for s in listed] == [("SCI notices", 0)]


def test_my_groups_only_shows_groups_i_added(ali, group):
    sara = login("sara@student.aiu.edu.my")
    assert sara.get(SOURCES).json() == []
    assert APIClient().get(SOURCES).status_code == 401


def test_paste_whatsapp_text_once(ali, group):
    url = f"{SOURCES}{group['id']}/paste/"

    first = ali.post(url, {"text": CHAT}, format="json")
    assert first.status_code == 201
    assert first.json() == {"added": 2, "already_stored": 0}
    assert ali.post(url, {"text": CHAT}, format="json").json() == {"added": 0, "already_stored": 2}

    stored = Message.objects.get(sender_name="Sara")
    assert stored.text == "Which room?"
    assert stored.triage == "pending"
    assert ali.get(SOURCES).json()[0]["message_count"] == 2


def test_paste_a_plain_message_once(ali, group):
    url = f"{SOURCES}{group['id']}/paste/"
    body = {
        "text": "Industry visit to Intel on Friday, register by Wednesday.",
        "sender_name": "Ms Aina",
    }

    assert ali.post(url, body, format="json").json() == {"added": 1, "already_stored": 0}
    assert ali.post(url, body, format="json").json() == {"added": 0, "already_stored": 1}
    assert Message.objects.get().sender_name == "Ms Aina"


def test_upload_a_whatsapp_export_once(ali, group):
    url = f"{SOURCES}{group['id']}/export/"

    first = ali.post(url, {"file": export_file()}, format="multipart")
    assert first.status_code == 201
    assert first.json() == {"added": 2, "already_stored": 0}

    longer = CHAT + "01/10/2026, 09:20 - Dr Lee: Room B2\n"
    again = ali.post(url, {"file": export_file(longer)}, format="multipart")
    assert again.json() == {"added": 1, "already_stored": 2}  # only the new message


def test_export_checks_the_file(ali, group, monkeypatch):
    url = f"{SOURCES}{group['id']}/export/"

    wrong_type = ali.post(url, {"file": export_file(name="chat.pdf")}, format="multipart")
    assert wrong_type.status_code == 400
    assert "file" in wrong_type.json()["error"]["fields"]

    empty = ali.post(url, {"file": export_file("just some notes")}, format="multipart")
    assert empty.status_code == 400

    monkeypatch.setattr(services, "MAX_EXPORT_BYTES", 10)
    assert ali.post(url, {"file": export_file()}, format="multipart").status_code == 400


def test_only_members_can_add_messages(group):
    sara = login("sara@student.aiu.edu.my")
    url = f"{SOURCES}{group['id']}/paste/"
    assert sara.post(url, {"text": CHAT}, format="json").status_code == 403
    assert sara.post(f"{SOURCES}999/paste/", {"text": CHAT}, format="json").status_code == 404
