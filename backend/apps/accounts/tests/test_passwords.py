import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

RESET = "/api/v1/auth/users/reset_password/"
RESET_CONFIRM = "/api/v1/auth/users/reset_password_confirm/"
SET_PASSWORD = "/api/v1/auth/users/set_password/"
EMAIL = "ali@student.aiu.edu.my"
OLD = "Str0ng-pass-99"
NEW = "N3w-strong-pass-77"


@pytest.fixture
def student():
    return create_user(EMAIL, OLD, full_name="Ali Hassan")


@pytest.fixture
def client():
    return APIClient()


def reset_link_parts(message):
    match = re.search(r"reset-password/([^/\s]+)/([^/\s]+)", message.body)
    assert match, message.body
    return {"uid": match.group(1), "token": match.group(2)}


# --- Forgot password -----------------------------------------------------


def test_forgot_password_emails_a_link_to_the_website(client, student):
    response = client.post(RESET, {"email": EMAIL}, format="json")

    assert response.status_code == 204
    assert len(mail.outbox) == 1
    assert "http://localhost:5173/reset-password/" in mail.outbox[0].body


def test_unknown_email_gets_the_same_reply_and_no_email(client):
    response = client.post(RESET, {"email": "nobody@student.aiu.edu.my"}, format="json")

    assert response.status_code == 204  # never reveals which emails are registered
    assert len(mail.outbox) == 0


def test_reset_link_sets_a_new_password_once(client, student):
    client.post(RESET, {"email": EMAIL}, format="json")
    parts = reset_link_parts(mail.outbox[0])

    response = client.post(
        RESET_CONFIRM, {**parts, "new_password": NEW, "re_new_password": NEW}, format="json"
    )
    assert response.status_code == 204
    student.refresh_from_db()
    assert student.check_password(NEW)
    assert not student.check_password(OLD)

    again = client.post(
        RESET_CONFIRM, {**parts, "new_password": OLD, "re_new_password": OLD}, format="json"
    )
    assert again.status_code == 400  # a used link does not work twice


def test_reset_new_passwords_must_match(client, student):
    client.post(RESET, {"email": EMAIL}, format="json")
    parts = reset_link_parts(mail.outbox[0])

    response = client.post(
        RESET_CONFIRM,
        {**parts, "new_password": NEW, "re_new_password": "different-1"},
        format="json",
    )
    assert response.status_code == 400


# --- Change password (logged in) -------------------------------------------


def test_change_password_needs_login(client, student):
    response = client.post(
        SET_PASSWORD,
        {"current_password": OLD, "new_password": NEW, "re_new_password": NEW},
        format="json",
    )
    assert response.status_code == 401


def test_logged_in_user_can_change_password(client, student):
    client.force_authenticate(student)

    response = client.post(
        SET_PASSWORD,
        {"current_password": OLD, "new_password": NEW, "re_new_password": NEW},
        format="json",
    )

    assert response.status_code == 204
    assert User.objects.get(pk=student.pk).check_password(NEW)


def test_change_password_needs_the_correct_current_password(client, student):
    client.force_authenticate(student)

    response = client.post(
        SET_PASSWORD,
        {"current_password": "wrong-password", "new_password": NEW, "re_new_password": NEW},
        format="json",
    )

    assert response.status_code == 400
    assert "current_password" in response.json()["error"]["fields"]
    assert User.objects.get(pk=student.pk).check_password(OLD)
