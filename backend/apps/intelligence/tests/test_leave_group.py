"""Removing a group from my list: it stays for the others; nobody left means it isn't read."""

import pytest

from apps.intelligence.models import Message, Source
from apps.intelligence.tests.test_add_by_number import add_by_number
from apps.intelligence.tests.test_connect_group import SOURCES, connect, login
from apps.intelligence.tests.test_connector_api import (
    GROUP_ID,
    JOINED,
    MESSAGES,
    new_message,
    post_json,
    secret,  # noqa: F401  (signs the connector's requests)
)

pytestmark = pytest.mark.django_db


def leave(api, source_id):
    return api.delete(f"{SOURCES}{source_id}/membership/")


def joined_by_link(*students):
    """A group added by link by these students, that UniFlow's number has joined."""
    group_id = None
    for api in students:
        group_id = connect(api).json()["id"]
    post_json(JOINED, {"source_id": group_id, "external_id": GROUP_ID, "title": "CDE2313 A"})
    return group_id


def test_removing_a_group_keeps_it_for_the_others():
    ali, sara = login("ali@student.aiu.edu.my"), login("sara@student.aiu.edu.my")
    group_id = joined_by_link(ali, sara)

    assert leave(ali, group_id).status_code == 204

    assert ali.get(SOURCES).json() == []
    assert [group["id"] for group in sara.get(SOURCES).json()] == [group_id]
    assert Source.objects.get().status == Source.Status.ACTIVE
    assert post_json(MESSAGES, new_message()).status_code == 201  # still read for Sara


def test_when_the_last_student_removes_it_uniflow_stops_reading_it():
    ali = login("ali@student.aiu.edu.my")
    group_id = joined_by_link(ali)
    post_json(MESSAGES, new_message("OLD1"))

    leave(ali, group_id)

    assert Source.objects.get().status == Source.Status.UNUSED
    assert post_json(MESSAGES, new_message("NEW1")).status_code == 404
    assert list(Message.objects.values_list("external_id", flat=True)) == ["OLD1"]


def test_adding_an_unused_group_back_reads_it_again():
    ali, sara = login("ali@student.aiu.edu.my"), login("sara@student.aiu.edu.my")
    group_id = joined_by_link(ali)
    leave(ali, group_id)

    again = connect(sara)

    assert (again.status_code, again.json()["id"], again.json()["status"]) == (
        200,
        group_id,
        "active",
    )
    assert post_json(MESSAGES, new_message()).status_code == 201


def test_adding_an_unused_group_back_by_number_matches_its_name(settings):
    settings.UNIFLOW_WHATSAPP_NUMBER = "+60123456789"
    ali, sara = login("ali@student.aiu.edu.my"), login("sara@student.aiu.edu.my")
    group_id = joined_by_link(ali)
    leave(ali, group_id)

    # UniFlow's number never left the group, so it won't "join" it again: the name links it.
    again = connect(sara, invite_url="", title="cde2313  a")

    assert (again.status_code, again.json()["id"], again.json()["status"]) == (
        200,
        group_id,
        "active",
    )
    assert Source.objects.count() == 1


def test_a_group_not_joined_yet_is_dropped_when_nobody_wants_it(settings):
    settings.UNIFLOW_WHATSAPP_NUMBER = "+60123456789"
    ali = login("ali@student.aiu.edu.my")
    waiting = add_by_number(ali)
    by_link = connect(ali, invite_url="https://chat.whatsapp.com/XyZ987654321").json()

    leave(ali, waiting["id"])
    leave(ali, by_link["id"])

    assert Source.objects.count() == 0  # UniFlow's number won't join it either


def test_official_groups_are_still_read():
    ali = login("ali@student.aiu.edu.my")
    group_id = joined_by_link(ali)
    Source.objects.update(trust=Source.Trust.OFFICIAL)

    leave(ali, group_id)

    assert Source.objects.get().status == Source.Status.ACTIVE


def test_only_a_group_in_my_list_can_be_removed():
    ali, sara = login("ali@student.aiu.edu.my"), login("sara@student.aiu.edu.my")
    group_id = joined_by_link(ali)

    assert leave(sara, group_id).status_code == 404
    assert [group["id"] for group in ali.get(SOURCES).json()] == [group_id]
