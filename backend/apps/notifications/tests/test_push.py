"""Pushing alerts to phones through Expo (M9.15). Expo is replaced by a fake: no real requests."""

import importlib
import logging
from datetime import timedelta
from itertools import count

import httpx
import inngest
import pytest
from django.apps import apps as django_apps
from django.utils import timezone

from apps.accounts.services import create_user
from apps.notifications import functions, push, services
from apps.notifications.models import Device, Notification, PushSettings, PushTicket

pytestmark = pytest.mark.django_db

TOKEN = "ExponentPushToken[ali-phone]"
ids = count(1)


class FakeExpo:
    """Answers like Expo: every push accepted, every receipt "ok", unless told otherwise."""

    def __init__(self):
        self.requests: list[tuple[str, object, dict]] = []
        self.answers: list = []  # the next answers: a Response, an exception or a JSON body
        self.receipts: dict = {}

    def __call__(self, url, *, json, headers, timeout):
        self.requests.append((url, json, headers))
        if self.answers:
            answer = self.answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return (
                answer if isinstance(answer, httpx.Response) else httpx.Response(200, json=answer)
            )
        if url == push.SEND_URL:
            return httpx.Response(
                200, json={"data": [{"status": "ok", "id": f"t{next(ids)}"} for _ in json]}
            )
        return httpx.Response(200, json={"data": self.receipts})

    @property
    def pushed(self) -> list[dict]:
        return [m for url, body, _ in self.requests if url == push.SEND_URL for m in body]


@pytest.fixture
def expo(settings, monkeypatch):
    settings.EXPO_ACCESS_TOKEN = "made-up-expo-token"
    fake = FakeExpo()
    monkeypatch.setattr(push.httpx, "post", fake)
    return fake


def student(email="ali@student.aiu.edu.my", token=TOKEN, **fields):
    user = create_user(email, "Str0ng-pass-99", full_name=email, **fields)
    if token:
        Device.objects.create(
            user=user, expo_token=token, platform="android", last_seen_at=timezone.now()
        )
    return user


def alert(user, kind=Notification.Kind.TIMETABLE_CHANGE_PROPOSED, **fields):
    return Notification.objects.create(
        recipient=user,
        kind=kind,
        title=fields.pop("title", "CDE2313 moved to 2 PM"),
        body=fields.pop("body", "Confirm it on your timetable."),
        target_type="insight",
        target_id=42,
        **fields,
    )


def test_an_alert_reaches_each_phone_of_its_student(expo):
    ali = student()
    Device.objects.create(
        user=ali, expo_token="ExpoPushToken[tablet]", platform="ios", last_seen_at=timezone.now()
    )
    alert(ali, kind=Notification.Kind.DIGEST, read_at=timezone.now())  # read: not in the badge
    new = alert(ali)

    result = functions.push_notifications()

    assert result == {"claimed": 2, "ok": 4, "error": 0, "expired": 0}
    first = expo.pushed[2]
    assert first == {
        "to": TOKEN,
        "title": "CDE2313 moved to 2 PM",
        "body": "Confirm it on your timetable.",
        "data": {"v": 1, "notification_id": new.id, "target_type": "insight", "target_id": 42},
        "channelId": "class-changes",
        "priority": "high",
        "sound": "default",
        "badge": 1,
    }
    assert {m["to"] for m in expo.pushed} == {TOKEN, "ExpoPushToken[tablet]"}
    assert (expo.pushed[0]["channelId"], expo.pushed[0]["priority"]) == ("digest", "normal")
    assert expo.requests[0][2] == {"Authorization": "Bearer made-up-expo-token"}
    assert set(PushTicket.objects.values_list("status", flat=True)) == {"ok"}


def test_running_again_pushes_nothing_twice(expo):
    alert(student())

    functions.push_notifications()
    functions.push_notifications()

    assert len(expo.pushed) == 1


def test_saving_alerts_starts_the_push(expo, django_capture_on_commit_callbacks):
    ali = student()

    with django_capture_on_commit_callbacks(execute=True):
        services.send([Notification(recipient=ali, kind="system", title="Welcome")])

    assert [m["title"] for m in expo.pushed] == ["Welcome"]


def test_only_phones_that_should_get_it(expo):
    ali = student()
    alert(ali)
    Device.objects.create(  # registered after the alert
        user=ali, expo_token="ExpoPushToken[new]", platform="ios", last_seen_at=timezone.now()
    )
    Device.objects.filter(expo_token="ExpoPushToken[new]").update(
        created_at=timezone.now() + timedelta(seconds=1)
    )
    off = student("sara@student.aiu.edu.my", token="ExpoPushToken[sara]")
    Device.objects.filter(user=off).update(is_active=False)
    alert(off)
    alert(student("omar@student.aiu.edu.my", token="ExpoPushToken[omar]", is_suspended=True))

    functions.push_notifications()

    assert [m["to"] for m in expo.pushed] == [TOKEN]


def test_switched_off_kinds_are_not_pushed_but_uniflow_alerts_are(expo):
    ali = student()
    PushSettings.objects.create(user=ali, class_changes=False, needs_you=True, daily_digest=False)
    alert(ali)  # class change: off
    alert(ali, kind=Notification.Kind.DIGEST, title="Your digest")  # off
    alert(ali, kind=Notification.Kind.ACTION_REQUIRED, title="Submit the form")
    alert(ali, kind=Notification.Kind.SYSTEM, title="From UniFlow")

    functions.push_notifications()

    assert [m["title"] for m in expo.pushed] == ["Submit the form", "From UniFlow"]
    assert Notification.objects.filter(pushed_at__isnull=True).count() == 0  # all claimed


def test_alerts_older_than_an_hour_are_not_pushed(expo):
    old = alert(student())
    Notification.objects.filter(id=old.id).update(created_at=timezone.now() - timedelta(hours=2))

    functions.push_notifications()

    assert expo.pushed == []
    assert Notification.objects.get().pushed_at is not None


def test_nothing_is_pushed_without_the_expo_token(expo, settings):
    settings.EXPO_ACCESS_TOKEN = ""
    alert(student())

    assert functions.push_notifications() == {}
    assert expo.requests == []
    assert Notification.objects.get().pushed_at is None  # pushed once the token is set


def test_existing_alerts_are_not_pushed_after_the_migration(expo):
    alert(student())
    migration = importlib.import_module("apps.notifications.migrations.0003_push_tickets")

    migration.mark_existing_alerts_as_pushed(django_apps, None)
    functions.push_notifications()

    assert expo.pushed == []


def test_a_phone_that_is_gone_is_switched_off(expo):
    alert(student())
    expo.answers.append(
        {"data": [{"status": "error", "details": {"error": "DeviceNotRegistered"}}]}
    )

    functions.push_notifications()

    device = Device.objects.get()
    assert (device.is_active, device.deactivated_reason) == (False, "not_registered")
    assert PushTicket.objects.get().error == "DeviceNotRegistered"


@pytest.mark.parametrize(
    "failure", [httpx.Response(500), httpx.Response(429), httpx.ConnectTimeout("slow")]
)
def test_when_expo_is_unavailable_the_push_is_tried_again(expo, failure):
    alert(student())
    expo.answers.append(failure)

    with pytest.raises(inngest.RetryAfterError):
        functions.push_notifications(attempt=2)
    assert PushTicket.objects.get().status == "pending"

    assert functions.push_notifications(attempt=3)["ok"] == 1  # the retry sends it
    assert PushTicket.objects.get().status == "ok"


def test_a_pending_push_older_than_an_hour_is_given_up(expo):
    alert(student())
    expo.answers.append(httpx.Response(503))
    with pytest.raises(inngest.RetryAfterError):
        functions.push_notifications()
    PushTicket.objects.update(created_at=timezone.now() - timedelta(hours=2))

    assert functions.push_notifications()["expired"] == 1
    assert len(expo.pushed) == 1  # only the first try


def test_a_refused_request_is_not_tried_again(expo):
    alert(student())
    expo.answers.append(httpx.Response(400, json={"errors": [{"code": "VALIDATION_ERROR"}]}))

    assert functions.push_notifications()["error"] == 1
    assert (PushTicket.objects.get().status, PushTicket.objects.get().error) == (
        "error",
        "http_400",
    )


def test_many_pushes_go_in_batches_of_100(expo):
    for n in range(150):
        Device.objects.create(
            user=student(f"s{n}@student.aiu.edu.my", token=None),
            expo_token=f"ExpoPushToken[p{n}]",
            platform="android",
            last_seen_at=timezone.now(),
        )
    for user in Device.objects.values_list("user", flat=True):
        Notification.objects.create(recipient_id=user, kind="system", title="Hello")

    functions.push_notifications()

    assert [len(body) for url, body, _ in expo.requests] == [100, 50]


def test_logs_hold_no_push_address_or_text(expo, caplog):
    alert(student(), title="Private title", body="Private body")
    expo.answers.append(
        {"data": [{"status": "error", "details": {"error": "DeviceNotRegistered"}}]}
    )

    with caplog.at_level(logging.DEBUG, logger="apps.notifications"):
        functions.push_notifications()

    assert caplog.text
    for secret in ("ali-phone", "Private", "made-up-expo-token"):
        assert secret not in caplog.text


# --- Receipts and clean-up --------------------------------------------------------------------


def sent_ticket(expo, minutes_ago=20):
    alert(student())
    functions.push_notifications()
    PushTicket.objects.update(created_at=timezone.now() - timedelta(minutes=minutes_ago))
    return PushTicket.objects.get()


def test_receipts_are_stored_and_gone_phones_switched_off(expo):
    ticket = sent_ticket(expo)
    expo.receipts = {
        ticket.expo_id: {"status": "error", "details": {"error": "DeviceNotRegistered"}}
    }

    assert functions.check_push_receipts() == {"deleted": 0, "ok": 0, "error": 1}

    assert expo.requests[-1][:2] == (push.RECEIPTS_URL, {"ids": [ticket.expo_id]})
    assert PushTicket.objects.get().receipt == "DeviceNotRegistered"
    assert Device.objects.get().deactivated_reason == "not_registered"


def test_receipts_are_asked_once_and_only_after_15_minutes(expo):
    ticket = sent_ticket(expo, minutes_ago=5)
    functions.check_push_receipts()
    assert expo.requests[-1][0] == push.SEND_URL  # too early: not asked yet

    PushTicket.objects.update(created_at=timezone.now() - timedelta(minutes=20))
    expo.receipts = {ticket.expo_id: {"status": "ok"}}
    assert functions.check_push_receipts()["ok"] == 1
    assert functions.check_push_receipts() == {"deleted": 0, "ok": 0, "error": 0}


def test_a_wrong_firebase_set_up_is_logged_as_an_error(expo, caplog):
    ticket = sent_ticket(expo)
    expo.receipts = {
        ticket.expo_id: {"status": "error", "details": {"error": "InvalidCredentials"}}
    }

    functions.check_push_receipts()

    assert [r.levelname for r in caplog.records if "InvalidCredentials" in r.message] == ["ERROR"]


def test_tickets_older_than_7_days_are_deleted(expo):
    sent_ticket(expo, minutes_ago=8 * 24 * 60)

    assert functions.check_push_receipts()["deleted"] == 1
    assert not PushTicket.objects.exists()


def test_phones_not_used_for_14_days_are_switched_off():
    student()
    student("sara@student.aiu.edu.my", token="ExpoPushToken[sara]")
    Device.objects.filter(expo_token=TOKEN).update(last_seen_at=timezone.now() - timedelta(days=15))

    assert functions.deactivate_stale_devices() == 1

    assert dict(Device.objects.values_list("expo_token", "deactivated_reason")) == {
        TOKEN: "stale",
        "ExpoPushToken[sara]": "",
    }
