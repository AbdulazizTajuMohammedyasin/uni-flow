"""Adding a WhatsApp group without an invite link: the student adds UniFlow's number to it."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.intelligence.connector import pending_sources
from apps.intelligence.models import Source
from apps.intelligence.tests.test_connect_group import CONNECT, SOURCES, connect, login
from apps.intelligence.tests.test_connector_api import (
    GROUP_ID,
    JOINED,
    post_json,
    secret,  # noqa: F401  (signs the connector's requests)
)

pytestmark = pytest.mark.django_db

NUMBER = "+60123456789"
OTHER_GROUP_ID = "120363000000000002@g.us"


@pytest.fixture(autouse=True)
def uniflow_number(settings):
    settings.UNIFLOW_WHATSAPP_NUMBER = NUMBER


def add_by_number(api, title="CCS2223 HCI – Section C2"):
    response = connect(api, invite_url="", title=title)
    assert response.status_code == 201, response.json()
    return response.json()


def unclaimed(api, source_id):
    return api.get(f"{SOURCES}{source_id}/unclaimed/")


def claim(api, source_id, group_id):
    return api.post(f"{SOURCES}{source_id}/claim/", {"group": group_id}, format="json")


def test_without_a_link_the_student_gets_uniflows_number():
    ali = login("ali@student.aiu.edu.my")

    body = add_by_number(ali)

    assert (body["platform"], body["status"]) == ("whatsapp_group", "pending")
    assert (body["added_by_number"], body["uniflow_number"]) == (True, NUMBER)
    assert list(pending_sources()) == []  # nothing for the connector to join by link
    assert [group["id"] for group in ali.get(SOURCES).json()] == [body["id"]]


def test_a_group_added_by_link_shows_no_number():
    body = connect(login("ali@student.aiu.edu.my")).json()
    assert (body["added_by_number"], body["uniflow_number"]) == (False, "")


def test_uniflow_added_to_a_group_of_the_same_name_links_it():
    ali = login("ali@student.aiu.edu.my")
    waiting = add_by_number(ali, title="CCS2223 HCI – Section C2")

    post_json(JOINED, {"external_id": GROUP_ID, "title": "ccs2223  hci – section c2"})

    group = Source.objects.get()
    assert group.id == waiting["id"]
    assert (group.status, group.external_id) == ("active", GROUP_ID)
    mine = ali.get(SOURCES).json()
    assert [(item["status"], item["uniflow_number"]) for item in mine] == [("active", "")]


def test_a_differently_named_group_can_be_picked_from_the_unclaimed_ones():
    ali = login("ali@student.aiu.edu.my")
    waiting = add_by_number(ali, title="HCI group")
    post_json(JOINED, {"external_id": GROUP_ID, "title": "CCS2223 HCI – Section C2"})
    joined = Source.objects.get(external_id=GROUP_ID)

    listed = unclaimed(ali, waiting["id"])
    assert listed.status_code == 200
    assert [(item["id"], item["title"]) for item in listed.json()] == [
        (joined.id, "CCS2223 HCI – Section C2")
    ]

    response = claim(ali, waiting["id"], joined.id)

    assert response.status_code == 200
    assert (response.json()["id"], response.json()["status"]) == (joined.id, "active")
    assert Source.objects.count() == 1  # the waiting entry was merged in
    assert [item["id"] for item in ali.get(SOURCES).json()] == [joined.id]


def test_only_groups_joined_since_and_unclaimed_are_listed():
    post_json(JOINED, {"external_id": OTHER_GROUP_ID, "title": "Joined before"})
    Source.objects.filter(external_id=OTHER_GROUP_ID).update(
        joined_at=timezone.now() - timedelta(minutes=5)
    )
    sara = login("sara@student.aiu.edu.my")
    by_link = connect(sara).json()  # joined by link: Sara's group, not unclaimed
    post_json(JOINED, {"external_id": GROUP_ID, "title": "CDE2313", "source_id": by_link["id"]})
    ali = login("ali@student.aiu.edu.my")

    waiting = add_by_number(ali, title="HCI group")

    assert unclaimed(ali, waiting["id"]).json() == []


def test_a_group_can_only_be_claimed_from_the_list_and_only_by_its_student():
    ali = login("ali@student.aiu.edu.my")
    waiting = add_by_number(ali, title="HCI group")
    sara = login("sara@student.aiu.edu.my")
    by_link = connect(sara).json()
    post_json(JOINED, {"external_id": GROUP_ID, "title": "CDE2313", "source_id": by_link["id"]})

    refused = claim(ali, waiting["id"], by_link["id"])  # Sara's group, not unclaimed
    assert refused.status_code == 400
    assert unclaimed(sara, waiting["id"]).status_code == 403  # not Sara's waiting group


def test_a_group_added_by_link_has_nothing_to_claim():
    ali = login("ali@student.aiu.edu.my")
    by_link = connect(ali).json()
    assert unclaimed(ali, by_link["id"]).status_code == 400


def test_two_students_waiting_under_one_name_are_not_guessed():
    add_by_number(login("ali@student.aiu.edu.my"), title="HCI")
    add_by_number(login("sara@student.aiu.edu.my"), title="HCI")

    post_json(JOINED, {"external_id": GROUP_ID, "title": "HCI"})

    assert Source.objects.filter(status="pending").count() == 2  # each picks it from the list
    assert Source.objects.get(external_id=GROUP_ID).members.count() == 0


def test_login_needed():
    assert APIClient().post(CONNECT, {"title": "x"}).status_code == 401
