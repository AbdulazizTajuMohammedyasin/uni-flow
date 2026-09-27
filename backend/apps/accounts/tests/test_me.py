from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.academics.models import Intake, Programme, School
from apps.accounts.models import User
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

ME = "/api/v1/auth/users/me/"


@pytest.fixture
def aiu():
    computing = School.objects.create(code="SCI", name="School of Computing and Informatics")
    business = School.objects.create(code="SBSS", name="School of Business & Social Sciences")
    closed = School.objects.create(code="OLD", name="Closed School", is_active=False)
    return {
        "computing": computing,
        "business": business,
        "closed": closed,
        "bcs": Programme.objects.create(
            school=computing, code="BCS", name="Bachelor in Computer Science", level="bachelor"
        ),
        "bba": Programme.objects.create(
            school=business,
            code="BBA",
            name="Bachelor of Business Administration",
            level="bachelor",
        ),
        "intake": Intake.objects.create(
            code="2024-OCT", name="October 2024", start_date=date(2024, 10, 1)
        ),
    }


@pytest.fixture
def student():
    return create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali Hassan")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_me_needs_login():
    assert APIClient().get(ME).status_code == 401


def test_new_student_sees_their_details_and_an_incomplete_profile(student):
    response = client_for(student).get(ME)

    assert response.status_code == 200
    assert response.json() == {
        "id": student.id,
        "email": "ali@student.aiu.edu.my",
        "full_name": "Ali Hassan",
        "role": "student",
        "profile_complete": False,
        "student_profile": {
            "student_number": None,
            "school": None,
            "programme": None,
            "intake": None,
        },
        "staff_profile": None,
    }


def test_student_completes_their_profile(student, aiu):
    response = client_for(student).patch(
        ME,
        {
            "student_profile": {
                "school": aiu["computing"].id,
                "programme": aiu["bcs"].id,
                "intake": aiu["intake"].id,
            }
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["profile_complete"] is True
    assert User.objects.get(pk=student.pk).profile_complete is True


def test_partial_update_keeps_other_fields(student, aiu):
    client = client_for(student)
    client.patch(
        ME,
        {"student_profile": {"school": aiu["computing"].id, "programme": aiu["bcs"].id}},
        format="json",
    )

    response = client.patch(ME, {"student_profile": {"intake": aiu["intake"].id}}, format="json")

    profile = response.json()["student_profile"]
    assert profile["school"] == aiu["computing"].id
    assert profile["programme"] == aiu["bcs"].id
    assert profile["intake"] == aiu["intake"].id


def test_programme_must_belong_to_the_school(student, aiu):
    response = client_for(student).patch(
        ME,
        {"student_profile": {"school": aiu["computing"].id, "programme": aiu["bba"].id}},
        format="json",
    )

    assert response.status_code == 400
    assert "student_profile" in response.json()["error"]["fields"]


def test_inactive_school_cannot_be_chosen(student, aiu):
    response = client_for(student).patch(
        ME, {"student_profile": {"school": aiu["closed"].id}}, format="json"
    )
    assert response.status_code == 400


def test_name_can_change_but_email_and_role_cannot(student):
    response = client_for(student).patch(
        ME,
        {"full_name": "Ali H.", "email": "x@gmail.com", "role": "super_admin"},
        format="json",
    )

    assert response.status_code == 200
    student.refresh_from_db()
    assert student.full_name == "Ali H."
    assert student.email == "ali@student.aiu.edu.my"
    assert student.role == "student"


def test_student_number_is_unique_but_keeping_your_own_is_fine(student):
    other = create_user("b@student.aiu.edu.my", "Str0ng-pass-99", full_name="B")
    other.student_profile.student_number = "AIU22001"
    other.student_profile.save()
    client = client_for(student)

    taken = client.patch(ME, {"student_profile": {"student_number": "AIU22001"}}, format="json")
    assert taken.status_code == 400

    client.patch(ME, {"student_profile": {"student_number": "AIU22002"}}, format="json")
    same_again = client.patch(
        ME, {"student_profile": {"student_number": "AIU22002"}}, format="json"
    )
    assert same_again.status_code == 200


def test_staff_see_their_staff_profile_and_cannot_set_a_student_profile(aiu):
    staff = create_user(
        "lect@aiu.edu.my", "Str0ng-pass-99", full_name="Dr Lee", role="school_staff"
    )
    staff.staff_profile.school = aiu["computing"]
    staff.staff_profile.position_title = "Lecturer"
    staff.staff_profile.save()
    client = client_for(staff)

    data = client.get(ME).json()
    assert data["profile_complete"] is True
    assert data["student_profile"] is None
    assert data["staff_profile"] == {"school": aiu["computing"].id, "position_title": "Lecturer"}

    response = client.patch(ME, {"student_profile": {"intake": aiu["intake"].id}}, format="json")
    assert response.status_code == 400
