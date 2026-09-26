from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.academics.models import Intake, Programme, School
from apps.accounts.models import StaffProfile, StudentProfile, User
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db


@pytest.fixture
def computing():
    school = School.objects.create(code="SCI", name="School of Computing and Informatics")
    programme = Programme.objects.create(
        school=school, code="BCS", name="Bachelor in Computer Science (Honours)", level="bachelor"
    )
    intake = Intake.objects.create(
        code="2024-OCT", name="October 2024", start_date=date(2024, 10, 1)
    )
    return {"school": school, "programme": programme, "intake": intake}


def make_student(email="ali@student.aiu.edu.my"):
    return create_user(email, "pw-123456!", full_name="Ali Hassan")


def test_create_user_gives_a_student_a_student_profile():
    user = make_student()

    assert StudentProfile.objects.filter(user=user).exists()
    assert not StaffProfile.objects.filter(user=user).exists()


@pytest.mark.parametrize("role", ["lecturer", "school_staff", "university_admin"])
def test_create_user_gives_other_roles_a_staff_profile(role):
    user = create_user("staff@aiu.edu.my", "pw-123456!", full_name="Staff", role=role)

    assert StaffProfile.objects.filter(user=user).exists()
    assert not StudentProfile.objects.filter(user=user).exists()


def test_profile_complete_needs_school_programme_and_intake(computing):
    user = make_student()
    profile = user.student_profile
    assert user.profile_complete is False

    profile.school = computing["school"]
    profile.programme = computing["programme"]
    profile.save()
    assert User.objects.get(pk=user.pk).profile_complete is False  # intake still missing

    profile.intake = computing["intake"]
    profile.save()
    assert User.objects.get(pk=user.pk).profile_complete is True


def test_staff_profile_is_always_complete():
    user = create_user("staff@aiu.edu.my", "pw", full_name="Staff", role="school_staff")
    assert user.profile_complete is True


def test_student_without_profile_is_incomplete():
    # e.g. created outside create_user(); must not crash
    user = User.objects.create_user("raw@student.aiu.edu.my", "pw", full_name="Raw")
    assert user.profile_complete is False


def test_programme_must_belong_to_the_chosen_school(computing):
    other = School.objects.create(code="SBSS", name="School of Business & Social Sciences")
    profile = make_student().student_profile
    profile.school = other
    profile.programme = computing["programme"]  # a computing programme

    with pytest.raises(ValidationError) as error:
        profile.full_clean()
    assert "programme" in error.value.message_dict


def test_student_number_is_unique_but_optional():
    first = make_student("a@student.aiu.edu.my").student_profile
    second = make_student("b@student.aiu.edu.my").student_profile
    assert first.student_number is None and second.student_number is None  # many blanks allowed

    first.student_number = "AIU22001"
    first.save()
    second.student_number = "AIU22001"
    with pytest.raises(IntegrityError), transaction.atomic():
        second.save()


def test_school_in_use_by_a_student_cannot_be_deleted(computing):
    profile = make_student().student_profile
    profile.school = computing["school"]
    profile.save()

    with pytest.raises(ProtectedError):
        computing["school"].delete()
