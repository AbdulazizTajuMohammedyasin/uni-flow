"""The school boundary, checked for every role."""

from datetime import date

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory

from apps.academics.models import Intake, Programme, School
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.publishing.policies import (
    CanManageObject,
    can_manage,
    manageable_queryset,
    validate_audience,
    validate_publisher,
)

from .models import SamplePost

pytestmark = pytest.mark.django_db

PASSWORD = "Str0ng-pass-99"


@pytest.fixture
def world():
    sci = School.objects.create(code="SCI", name="Computing")
    sbss = School.objects.create(code="SBSS", name="Business")

    def staff(role, email, school=None):
        user = create_user(email, PASSWORD, full_name=email, role=role)
        if school:
            user.staff_profile.school = school
            user.staff_profile.save()
        return user

    def post(school=None):
        return SamplePost.objects.create(
            audience=Audience.objects.create(),
            publisher_type="school" if school else "university",
            publisher_school=school,
        )

    return {
        "sci": sci,
        "sbss": sbss,
        "bcs": Programme.objects.create(school=sci, code="BCS", name="CS", level="bachelor"),
        "bba": Programme.objects.create(school=sbss, code="BBA", name="BA", level="bachelor"),
        "oct24": Intake.objects.create(
            code="2024-OCT", name="Oct 24", start_date=date(2024, 10, 1)
        ),
        "users": {
            "super_admin": staff("super_admin", "sa@aiu.edu.my"),
            "university_admin": staff("university_admin", "ua@aiu.edu.my"),
            "sci_staff": staff("school_staff", "sci@aiu.edu.my", sci),
            "no_school_staff": staff("school_staff", "none@aiu.edu.my"),
            "lecturer": staff("lecturer", "lec@aiu.edu.my"),
            "student": create_user("ali@student.aiu.edu.my", PASSWORD, full_name="Ali"),
        },
        "posts": {"university": post(), "sci": post(sci), "sbss": post(sbss)},
    }


# Which posts each role may manage.
MANAGE = {
    "super_admin": {"university", "sci", "sbss"},
    "university_admin": {"university", "sci", "sbss"},
    "sci_staff": {"sci"},
    "no_school_staff": set(),
    "lecturer": set(),
    "student": set(),
}


@pytest.mark.parametrize(("role", "expected"), MANAGE.items())
def test_which_posts_each_role_manages(world, role, expected):
    user = world["users"][role]
    posts = world["posts"]

    listed = {name for name, p in posts.items() if p in manageable_queryset(user, SamplePost)}
    editable = {name for name, p in posts.items() if can_manage(user, p)}

    assert listed == expected
    assert editable == expected  # the list and the per-item check agree


# Who each role may publish as: (publisher_type, school key or None)
PUBLISH = {
    "super_admin": {("university", None), ("school", "sci"), ("school", "sbss")},
    "university_admin": {("university", None), ("school", "sci"), ("school", "sbss")},
    "sci_staff": {("school", "sci")},
    "no_school_staff": set(),
    "lecturer": set(),
    "student": set(),
}
ALL_PUBLISHERS = [("university", None), ("school", "sci"), ("school", "sbss")]


@pytest.mark.parametrize(("role", "allowed"), PUBLISH.items())
def test_who_each_role_may_publish_as(world, role, allowed):
    user = world["users"][role]
    for publisher_type, school_key in ALL_PUBLISHERS:
        school = world[school_key] if school_key else None
        if (publisher_type, school_key) in allowed:
            validate_publisher(user, publisher_type, school)  # no error
        else:
            with pytest.raises(PermissionDenied):
                validate_publisher(user, publisher_type, school)


def test_university_publisher_with_a_school_is_refused(world):
    with pytest.raises(PermissionDenied):
        validate_publisher(world["users"]["university_admin"], "university", world["sci"])


@pytest.mark.parametrize(
    ("audience", "allowed"),
    [
        ({"schools": ["sci"]}, True),
        ({"schools": ["sci"], "programmes": ["bcs"], "intakes": ["oct24"]}, True),
        ({"schools": ["sci"], "intakes": ["oct24"]}, True),
        ({}, False),  # "all students"
        ({"intakes": ["oct24"]}, False),  # every school's October intake
        ({"schools": ["sbss"]}, False),
        ({"schools": ["sci", "sbss"]}, False),
        ({"schools": ["sci"], "programmes": ["bba"]}, False),  # another school's programme
        ({"programmes": ["bcs"]}, False),  # school missing
    ],
)
def test_school_staff_audience_stays_in_their_school(world, audience, allowed):
    data = {field: [world[key] for key in keys] for field, keys in audience.items()}
    staff = world["users"]["sci_staff"]

    if allowed:
        validate_audience(staff, data)
    else:
        with pytest.raises(PermissionDenied):
            validate_audience(staff, data)

    validate_audience(world["users"]["university_admin"], data)  # admins: anything


def test_lecturers_cannot_set_any_audience(world):
    with pytest.raises(PermissionDenied):
        validate_audience(world["users"]["lecturer"], {"schools": [world["sci"]]})


def test_can_manage_object_permission(world):
    request = APIRequestFactory().get("/")
    request.user = world["users"]["sci_staff"]
    permission = CanManageObject()

    assert permission.has_object_permission(request, None, world["posts"]["sci"])
    assert not permission.has_object_permission(request, None, world["posts"]["sbss"])
