import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.models import StudentProfile, User

pytestmark = pytest.mark.django_db

REGISTER_URL = "/api/v1/auth/users/"
ACTIVATE_URL = "/api/v1/auth/users/activation/"
RESEND_URL = "/api/v1/auth/users/resend_activation/"


def register(client, email="ali.hassan@student.aiu.edu.my", **overrides):
    data = {
        "email": email,
        "full_name": "Ali Hassan",
        "password": "Str0ng-pass-99",
        "re_password": "Str0ng-pass-99",
        **overrides,
    }
    return client.post(REGISTER_URL, data, format="json")


def activation_link_parts(message):
    """Pull uid and token out of the link in the activation email."""
    match = re.search(r"verify-email/([^/\s]+)/([^/\s]+)", message.body)
    assert match, message.body
    return {"uid": match.group(1), "token": match.group(2)}


@pytest.fixture
def client():
    return APIClient()


def test_student_can_register_and_gets_an_inactive_account_with_profile(client):
    response = register(client)

    assert response.status_code == 201
    user = User.objects.get(email="ali.hassan@student.aiu.edu.my")
    assert user.is_active is False
    assert user.full_name == "Ali Hassan"
    assert user.role == User.Role.STUDENT
    assert StudentProfile.objects.filter(user=user).exists()
    assert "password" not in response.json()


def test_registration_sends_an_activation_email_linking_to_the_website(client):
    register(client)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ali.hassan@student.aiu.edu.my"]
    assert "http://localhost:5173/verify-email/" in mail.outbox[0].body


def test_email_is_lowercased(client):
    register(client, email="Ali.Hassan@Student.AIU.edu.my")
    assert User.objects.filter(email="ali.hassan@student.aiu.edu.my").exists()


@pytest.mark.parametrize(
    "email",
    [
        "someone@gmail.com",
        "staff@aiu.edu.my",  # staff accounts are created by a super admin
        "trick@evil.student.aiu.edu.my",
        "trick@student.aiu.edu.my.evil.com",
    ],
)
def test_only_student_aiu_emails_can_register(client, email):
    response = register(client, email=email)

    assert response.status_code == 400
    assert "email" in response.json()["error"]["fields"]
    assert not User.objects.filter(email=email.lower()).exists()
    assert len(mail.outbox) == 0


def test_passwords_must_match(client):
    response = register(client, re_password="something-else-1")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_weak_password_is_rejected(client):
    response = register(client, password="12345678", re_password="12345678")

    assert response.status_code == 400
    assert "password" in response.json()["error"]["fields"]


def test_email_cannot_be_registered_twice(client):
    register(client)
    response = register(client)

    assert response.status_code == 400
    assert "email" in response.json()["error"]["fields"]


def test_activation_link_activates_the_account_once(client):
    register(client)
    parts = activation_link_parts(mail.outbox[0])

    response = client.post(ACTIVATE_URL, parts, format="json")
    assert response.status_code == 204
    assert User.objects.get(email="ali.hassan@student.aiu.edu.my").is_active is True

    again = client.post(ACTIVATE_URL, parts, format="json")  # a used link must not work twice
    assert again.status_code in (400, 403)


def test_invalid_activation_link_is_rejected(client):
    register(client)
    response = client.post(ACTIVATE_URL, {"uid": "bad", "token": "bad"}, format="json")

    assert response.status_code == 400
    assert User.objects.get(email="ali.hassan@student.aiu.edu.my").is_active is False


def test_activation_email_can_be_resent(client):
    register(client)
    response = client.post(RESEND_URL, {"email": "ali.hassan@student.aiu.edu.my"}, format="json")

    assert response.status_code == 204
    assert len(mail.outbox) == 2


def test_listing_users_is_not_public(client):
    response = client.get(REGISTER_URL)
    assert response.status_code == 403


def test_normal_user_cannot_change_email_or_delete_account(client):
    register(client)
    user = User.objects.get(email="ali.hassan@student.aiu.edu.my")
    client.force_authenticate(user)

    set_email = client.post(
        "/api/v1/auth/users/set_email/",
        {
            "new_email": "x@gmail.com",
            "re_new_email": "x@gmail.com",
            "current_password": "Str0ng-pass-99",
        },
        format="json",
    )
    delete = client.delete(
        "/api/v1/auth/users/me/", {"current_password": "Str0ng-pass-99"}, format="json"
    )

    assert set_email.status_code == 403
    assert delete.status_code == 403
    assert User.objects.filter(pk=user.pk, email="ali.hassan@student.aiu.edu.my").exists()
