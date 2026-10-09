"""Notifications API (M8.1): users see only their own."""

import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from apps.accounts.services import create_user
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db

URL = "/api/v1/notifications/"


def login(email):
    user = create_user(email, "Str0ng-pass-99", full_name=email)
    api = APIClient()
    api.force_authenticate(user)
    return user, api


def alert(user, title="Dr Lee named you", **fields):
    return Notification.objects.create(
        recipient=user,
        kind=fields.pop("kind", Notification.Kind.DIRECT_ATTENTION),
        title=title,
        target_type="insight",
        target_id=42,
        **fields,
    )


def test_my_alerts_newest_first():
    ali, api = login("ali@student.aiu.edu.my")
    alert(ali, "First")
    alert(ali, "Second", kind=Notification.Kind.IMPORTANT_UPDATE)

    body = api.get(URL).json()

    assert [item["title"] for item in body["results"]] == ["Second", "First"]
    assert body["results"][0] | {"id": None, "created_at": None} == {
        "id": None,
        "kind": "important_update",
        "title": "Second",
        "body": "",
        "target_type": "insight",
        "target_id": 42,
        "read": False,
        "created_at": None,
    }


def test_unread_count_read_one_and_read_all():
    ali, api = login("ali@student.aiu.edu.my")
    first, _, _ = alert(ali, "1"), alert(ali, "2"), alert(ali, "3")

    assert api.get(f"{URL}unread-count/").json() == {"count": 3}
    assert api.post(f"{URL}{first.id}/read/").status_code == 204
    assert api.get(f"{URL}unread-count/").json() == {"count": 2}

    assert api.post(f"{URL}read-all/").json() == {"marked": 2}
    assert api.get(f"{URL}unread-count/").json() == {"count": 0}
    assert all(item["read"] for item in api.get(URL).json()["results"])


def test_users_see_only_their_own():
    ali, _ = login("ali@student.aiu.edu.my")
    _, sara = login("sara@student.aiu.edu.my")
    mine = alert(ali)

    assert sara.get(URL).json()["results"] == []
    assert sara.get(f"{URL}unread-count/").json() == {"count": 0}
    assert sara.post(f"{URL}{mine.id}/read/").status_code == 404
    assert sara.post(f"{URL}read-all/").json() == {"marked": 0}
    mine.refresh_from_db()
    assert mine.read_at is None
    assert APIClient().get(URL).status_code == 401


def test_the_same_alert_is_never_stored_twice():
    ali, _ = login("ali@student.aiu.edu.my")
    alert(ali, dedupe_key="ins:42:u:1")
    alert(ali, dedupe_key=None)
    alert(ali, dedupe_key=None)  # alerts without a key never clash
    with pytest.raises(IntegrityError):
        alert(ali, dedupe_key="ins:42:u:1")
