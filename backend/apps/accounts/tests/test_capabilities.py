import pytest
from rest_framework.test import APIClient, APIRequestFactory

from apps.academics.models import School
from apps.accounts.capabilities import (
    ALL_CAPABILITIES,
    CONTENT_CAPABILITIES,
    HasCapability,
    capabilities_for,
    publishers_for,
)
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def computing():
    return School.objects.create(code="SCI", name="School of Computing and Informatics")


def make(role, email=None, school=None):
    user = create_user(email or f"{role}@aiu.edu.my", "Str0ng-pass-99", full_name=role, role=role)
    if school is not None:
        user.staff_profile.school = school
        user.staff_profile.save()
    return user


def granted(user):
    return {name for name, allowed in capabilities_for(user).items() if allowed}


# --- Who gets what -----------------------------------------------------------


def test_students_and_lecturers_manage_nothing():
    student = create_user("s@student.aiu.edu.my", "Str0ng-pass-99", full_name="S")
    assert granted(student) == set()
    assert granted(make("lecturer")) == set()


def test_school_staff_manage_content_only_with_a_school(computing):
    assert granted(make("school_staff", school=computing)) == set(CONTENT_CAPABILITIES)
    assert granted(make("school_staff", email="noschool@aiu.edu.my")) == set()  # half set-up


def test_university_admin_manages_content_and_academics():
    assert granted(make("university_admin")) == {*CONTENT_CAPABILITIES, "academics.manage"}


def test_super_admin_manages_everything():
    assert granted(make("super_admin")) == set(ALL_CAPABILITIES)


def test_every_capability_is_always_listed():
    student = create_user("s@student.aiu.edu.my", "Str0ng-pass-99", full_name="S")
    assert set(capabilities_for(student)) == set(ALL_CAPABILITIES)


# --- Who they may publish as ---------------------------------------------------


def test_school_staff_publish_only_as_their_school(computing):
    assert publishers_for(make("school_staff", school=computing)) == [
        {"type": "school", "id": computing.id, "name": computing.name}
    ]


def test_admins_publish_as_the_university_or_any_active_school(computing):
    School.objects.create(code="OLD", name="Closed School", is_active=False)
    publishers = publishers_for(make("university_admin"))

    assert publishers[0]["type"] == "university"
    assert [p["name"] for p in publishers[1:]] == [computing.name]  # inactive school left out


def test_students_publish_as_nobody():
    student = create_user("s@student.aiu.edu.my", "Str0ng-pass-99", full_name="S")
    assert publishers_for(student) == []


# --- The API permission ---------------------------------------------------------


def test_has_capability_permission(computing):
    permission = HasCapability("announcements.manage")()
    request = APIRequestFactory().get("/")

    request.user = make("school_staff", school=computing)
    assert permission.has_permission(request, None) is True

    request.user = make("lecturer")
    assert permission.has_permission(request, None) is False


def test_unknown_capability_is_a_programming_error():
    with pytest.raises(ValueError):
        HasCapability("nonsense.manage")


# --- users/me/ -----------------------------------------------------------------------


def test_me_includes_capabilities_and_publishers(computing):
    staff = make("school_staff", school=computing)
    client = APIClient()
    client.force_authenticate(staff)

    data = client.get("/api/v1/auth/users/me/").json()

    assert data["capabilities"]["announcements.manage"] is True
    assert data["capabilities"]["users.manage"] is False
    assert data["publishers"] == [{"type": "school", "id": computing.id, "name": computing.name}]
