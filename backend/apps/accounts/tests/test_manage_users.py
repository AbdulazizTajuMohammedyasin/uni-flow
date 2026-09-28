import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.academics.models import School
from apps.accounts.models import User
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

USERS = "/api/v1/manage/users/"
PASSWORD = "Str0ng-pass-99"


@pytest.fixture
def computing():
    return School.objects.create(code="SCI", name="School of Computing and Informatics")


@pytest.fixture
def admin():
    return User.objects.create_superuser("root@aiu.edu.my", PASSWORD, full_name="Root Admin")


@pytest.fixture
def client(admin):
    api = APIClient()
    api.force_authenticate(admin)
    return api


def new_staff(client, **overrides):
    data = {
        "email": "Dr.Lee@aiu.edu.my",
        "full_name": "Dr Lee",
        "role": "school_staff",
        "position_title": "Lecturer",
        **overrides,
    }
    return client.post(USERS, data, format="json")


# --- Access ----------------------------------------------------------------------


def test_only_super_admins_can_manage_users(computing):
    assert APIClient().get(USERS).status_code == 401

    uni_admin = create_user("ua@aiu.edu.my", PASSWORD, full_name="UA", role="university_admin")
    api = APIClient()
    api.force_authenticate(uni_admin)
    assert api.get(USERS).status_code == 403


def test_list_search_and_filter(client, computing):
    create_user("ali@student.aiu.edu.my", PASSWORD, full_name="Ali Hassan")
    new_staff(client, school=computing.id)

    assert len(client.get(USERS).json()["results"]) == 3  # admin, student, staff
    assert [u["email"] for u in client.get(USERS, {"search": "ali"}).json()["results"]] == [
        "ali@student.aiu.edu.my"
    ]
    staff = client.get(USERS, {"role": "school_staff", "school": computing.id}).json()["results"]
    assert [u["email"] for u in staff] == ["dr.lee@aiu.edu.my"]


# --- Create staff accounts ------------------------------------------------------------


def test_create_staff_account_emails_a_working_set_password_link(client, computing):
    response = new_staff(client, school=computing.id)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "dr.lee@aiu.edu.my"
    assert body["role"] == "school_staff"
    assert body["school"] == computing.id
    user = User.objects.get(email="dr.lee@aiu.edu.my")
    assert user.is_active is True
    assert user.has_usable_password() is False  # set via the emailed link

    assert len(mail.outbox) == 1
    match = re.search(r"reset-password/([^/\s]+)/([^/\s]+)", mail.outbox[0].body)
    assert match
    reset = APIClient().post(
        "/api/v1/auth/users/reset_password_confirm/",
        {
            "uid": match.group(1),
            "token": match.group(2),
            "new_password": "N3w-strong-pass-77",
            "re_new_password": "N3w-strong-pass-77",
        },
        format="json",
    )
    assert reset.status_code == 204
    login = APIClient().post(
        "/api/v1/auth/jwt/create/",
        {"email": "dr.lee@aiu.edu.my", "password": "N3w-strong-pass-77"},
        format="json",
    )
    assert login.status_code == 200


def test_school_staff_must_have_a_school(client):
    response = new_staff(client)

    assert response.status_code == 400
    assert "school" in response.json()["error"]["fields"]


def test_cannot_create_students_or_duplicate_emails(client, computing):
    assert new_staff(client, role="student").status_code == 400
    new_staff(client, school=computing.id)
    duplicate = new_staff(client, email="DR.LEE@aiu.edu.my", school=computing.id)
    assert duplicate.status_code == 400
    assert "email" in duplicate.json()["error"]["fields"]


# --- Change role / school / suspension ------------------------------------------------


def test_promoting_to_super_admin_syncs_django_admin_access(client, computing):
    user_id = new_staff(client, school=computing.id).json()["id"]

    client.patch(f"{USERS}{user_id}/", {"role": "super_admin"}, format="json")
    promoted = User.objects.get(pk=user_id)
    assert promoted.role == "super_admin"
    assert promoted.is_staff is True

    client.patch(f"{USERS}{user_id}/", {"role": "university_admin"}, format="json")
    assert User.objects.get(pk=user_id).is_staff is False


def test_change_school_and_position(client, computing):
    business = School.objects.create(code="SBSS", name="School of Business & Social Sciences")
    user_id = new_staff(client, school=computing.id).json()["id"]

    response = client.patch(
        f"{USERS}{user_id}/", {"school": business.id, "position_title": "Dean"}, format="json"
    )

    assert response.status_code == 200
    assert response.json()["school"] == business.id
    assert response.json()["position_title"] == "Dean"


def test_suspended_user_cannot_log_in_and_their_token_stops_working(client):
    student = create_user("ali@student.aiu.edu.my", PASSWORD, full_name="Ali")
    other = APIClient()
    access = other.post(
        "/api/v1/auth/jwt/create/", {"email": student.email, "password": PASSWORD}, format="json"
    ).json()["access"]

    client.patch(f"{USERS}{student.id}/", {"is_suspended": True}, format="json")

    other.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    blocked = other.get("/api/v1/auth/users/me/")
    assert blocked.status_code == 401
    assert blocked.json()["error"]["code"] == "account_suspended"
    login = APIClient().post(
        "/api/v1/auth/jwt/create/", {"email": student.email, "password": PASSWORD}, format="json"
    )
    assert login.status_code == 401

    client.patch(f"{USERS}{student.id}/", {"is_suspended": False}, format="json")
    assert other.get("/api/v1/auth/users/me/").status_code == 200  # works again


def test_admin_cannot_change_their_own_role_or_suspend_themselves(client, admin):
    assert (
        client.patch(f"{USERS}{admin.id}/", {"role": "lecturer"}, format="json").status_code == 400
    )
    assert (
        client.patch(f"{USERS}{admin.id}/", {"is_suspended": True}, format="json").status_code
        == 400
    )
    assert User.objects.get(pk=admin.id).role == "super_admin"


def test_student_role_is_not_changed_here(client):
    student = create_user("ali@student.aiu.edu.my", PASSWORD, full_name="Ali")
    response = client.patch(f"{USERS}{student.id}/", {"role": "lecturer"}, format="json")
    assert response.status_code == 400


def test_users_cannot_be_deleted(client, computing):
    user_id = new_staff(client, school=computing.id).json()["id"]
    assert client.delete(f"{USERS}{user_id}/").status_code == 405
