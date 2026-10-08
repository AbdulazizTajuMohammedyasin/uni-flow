"""Adding a WhatsApp group by its invite link (POST sources/connect/)."""

import pytest
from rest_framework.test import APIClient

from apps.academics.models import School
from apps.accounts.services import create_user
from apps.intelligence.connector import pending_sources
from apps.intelligence.models import Source

pytestmark = pytest.mark.django_db

CONNECT = "/api/v1/sources/connect/"
SOURCES = "/api/v1/sources/"
LINK = "https://chat.whatsapp.com/AbCdEf123456"


def login(email):
    api = APIClient()
    api.force_authenticate(create_user(email, "Str0ng-pass-99", full_name=email))
    return api


def connect(api, invite_url=LINK, title="CDE2313 Section A", **scope):
    return api.post(CONNECT, {"invite_url": invite_url, "title": title, **scope}, format="json")


def test_a_new_group_waits_for_uniflow_to_join():
    ali = login("ali@student.aiu.edu.my")
    school = School.objects.create(code="SCI", name="Computing")

    response = connect(ali, school=school.id)

    assert response.status_code == 201
    body = response.json()
    assert (body["title"], body["platform"], body["status"]) == (
        "CDE2313 Section A",
        "whatsapp_group",
        "pending",
    )
    assert body["school"] == school.id
    assert [source.invite_url for source in pending_sources()] == [LINK]  # the connector's list
    assert [group["id"] for group in ali.get(SOURCES).json()] == [body["id"]]


def test_the_same_group_is_not_joined_twice():
    first = connect(login("ali@student.aiu.edu.my")).json()
    sara = login("sara@student.aiu.edu.my")

    # The same link, written slightly differently.
    response = connect(sara, invite_url=" https://chat.whatsapp.com/invite/AbCdEf123456/ ")

    assert response.status_code == 200
    assert response.json()["id"] == first["id"]
    assert Source.objects.count() == 1
    assert Source.objects.get().members.count() == 2
    assert [group["id"] for group in sara.get(SOURCES).json()] == [first["id"]]


@pytest.mark.parametrize(
    "link",
    [
        "https://chat.whatsapp.com.evil.example/AbCdEf123456",  # look-alike host
        "https://evil.example/chat.whatsapp.com/AbCdEf123456",
        "http://chat.whatsapp.com/AbCdEf123456",  # not https
        "https://chat.whatsapp.com/",  # no group code
        "javascript:alert(1)",
        "CDE2313 group",
    ],
)
def test_wrong_hosts_and_broken_links_are_refused(link):
    response = connect(login("ali@student.aiu.edu.my"), invite_url=link)
    assert response.status_code == 400
    assert "chat.whatsapp.com" in str(response.json()["error"]["fields"]["invite_url"])
    assert Source.objects.count() == 0


def test_a_telegram_link_explains_how_to_add_the_bot():
    response = connect(login("ali@student.aiu.edu.my"), invite_url="https://t.me/+AbCdEf123")
    assert response.status_code == 400
    assert "add the UniFlow bot" in str(response.json()["error"]["fields"]["invite_url"])


def test_a_disconnected_group_is_not_rejoined():
    connect(login("ali@student.aiu.edu.my"))
    Source.objects.update(status=Source.Status.DISCONNECTED)
    response = connect(login("sara@student.aiu.edu.my"))
    assert response.status_code == 400
    assert Source.objects.get().members.count() == 1


def test_login_needed():
    assert APIClient().post(CONNECT, {"invite_url": LINK, "title": "x"}).status_code == 401
