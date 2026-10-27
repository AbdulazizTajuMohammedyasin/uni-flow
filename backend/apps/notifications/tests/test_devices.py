"""Phones that can get push notifications, and which alerts reach them (the mobile app)."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import UserRole
from apps.accounts.services import create_user
from apps.notifications.models import Device, PushSettings
from apps.notifications.tests.test_api import login

pytestmark = pytest.mark.django_db

DEVICES = "/api/v1/notifications/devices/"
UNREGISTER = "/api/v1/notifications/devices/unregister/"
SETTINGS = "/api/v1/notifications/push-settings/"
TOKEN = "ExponentPushToken[abc123_XYZ-9]"


def register(api, token=TOKEN, **fields):
    return api.post(DEVICES, {"token": token, "platform": "android", **fields}, format="json")


def test_registering_my_phone():
    ali, api = login("ali@student.aiu.edu.my")

    response = register(api, app_version="1.0.0")

    assert (response.status_code, response.json()) == (201, {"registered": True})
    device = Device.objects.get()
    assert (device.user, device.expo_token, device.platform, device.app_version) == (
        ali,
        TOKEN,
        "android",
        "1.0.0",
    )
    assert device.is_active


def test_registering_again_updates_the_phone():
    _, api = login("ali@student.aiu.edu.my")
    register(api, app_version="1.0.0")
    Device.objects.update(
        last_seen_at=timezone.now() - timedelta(days=3),
        is_active=False,
        deactivated_reason=Device.Reason.LOGOUT,
    )

    response = register(api, app_version="1.1.0")

    assert response.status_code == 200
    device = Device.objects.get()
    assert (device.is_active, device.deactivated_reason, device.app_version) == (True, "", "1.1.0")
    assert device.last_seen_at > timezone.now() - timedelta(minutes=1)


def test_a_phone_moves_to_the_student_who_logs_in_on_it():
    _, ali = login("ali@student.aiu.edu.my")
    sara_user, sara = login("sara@student.aiu.edu.my")
    register(ali)

    assert register(sara).status_code == 200

    assert list(Device.objects.values_list("user", flat=True)) == [sara_user.id]


def test_a_student_can_have_several_phones():
    _, api = login("ali@student.aiu.edu.my")
    register(api)
    register(api, token="ExpoPushToken[second-phone]")

    assert Device.objects.count() == 2


def test_logging_out_switches_off_only_my_own_phone():
    _, ali = login("ali@student.aiu.edu.my")
    _, sara = login("sara@student.aiu.edu.my")
    register(ali)

    assert sara.post(UNREGISTER, {"token": TOKEN}, format="json").status_code == 204
    assert Device.objects.get().is_active  # not Sara's: nothing changes, nothing is revealed

    assert ali.post(UNREGISTER, {"token": TOKEN}, format="json").status_code == 204
    device = Device.objects.get()
    assert (device.is_active, device.deactivated_reason) == (False, "logout")

    unknown = ali.post(UNREGISTER, {"token": "ExpoPushToken[unknown]"}, format="json")
    assert unknown.status_code == 204


@pytest.mark.parametrize(
    "body",
    [
        {"token": "not-a-push-address", "platform": "android"},
        {"token": "ExponentPushToken[bad token]", "platform": "android"},
        {"token": TOKEN, "platform": "windows"},
        {"token": TOKEN, "platform": "ios", "app_version": "1" * 21},
        {"platform": "android"},
    ],
)
def test_invalid_registrations_are_refused(body):
    _, api = login("ali@student.aiu.edu.my")

    assert api.post(DEVICES, body, format="json").status_code == 400
    assert not Device.objects.exists()


def test_only_logged_in_students_have_phones():
    anonymous = APIClient()
    assert register(anonymous).status_code == 401
    assert anonymous.get(SETTINGS).status_code == 401

    staff = APIClient()
    staff.force_authenticate(create_user("lee@aiu.edu.my", role=UserRole.SCHOOL_STAFF))
    assert register(staff).status_code == 403
    assert staff.get(SETTINGS).status_code == 403
    assert not Device.objects.exists()


def test_registering_is_throttled():
    _, api = login("ali@student.aiu.edu.my")

    codes = [register(api).status_code for _ in range(31)]

    assert codes[:30] == [201] + [200] * 29
    assert codes[30] == 429


def test_push_settings_start_with_everything_on():
    _, api = login("ali@student.aiu.edu.my")

    response = api.get(SETTINGS)

    assert response.json() == {"class_changes": True, "needs_you": True, "daily_digest": True}
    assert not PushSettings.objects.exists()  # nothing saved just by looking


def test_changing_one_push_setting_keeps_the_others():
    ali, api = login("ali@student.aiu.edu.my")
    _, sara = login("sara@student.aiu.edu.my")

    response = api.patch(SETTINGS, {"daily_digest": False}, format="json")

    assert response.json() == {"class_changes": True, "needs_you": True, "daily_digest": False}
    api.patch(SETTINGS, {"needs_you": False}, format="json")
    assert api.get(SETTINGS).json() == {
        "class_changes": True,
        "needs_you": False,
        "daily_digest": False,
    }
    assert PushSettings.objects.get().user == ali
    assert sara.get(SETTINGS).json()["daily_digest"] is True  # only my own
