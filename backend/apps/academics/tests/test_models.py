from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.academics.models import Intake, Programme, School

pytestmark = pytest.mark.django_db


def make_school(code="SCI", name="School of Computing and Informatics"):
    return School.objects.create(code=code, name=name)


def make_programme(school, code="BCS", name="Bachelor in Computer Science (Honours)"):
    return Programme.objects.create(
        school=school, code=code, name=name, level=Programme.Level.BACHELOR
    )


def test_school_defaults_and_str():
    school = make_school()

    assert school.is_active is True
    assert str(school) == "School of Computing and Informatics"
    assert school.created_at is not None
    assert school.updated_at is not None


def test_school_code_is_unique():
    make_school(code="SCI")

    with pytest.raises(IntegrityError), transaction.atomic():
        make_school(code="SCI", name="Another name")


def test_programme_belongs_to_a_school():
    school = make_school()
    programme = make_programme(school)

    assert programme.school == school
    assert list(school.programmes.all()) == [programme]
    assert str(programme) == "Bachelor in Computer Science (Honours)"


def test_programme_code_is_unique():
    school = make_school()
    make_programme(school, code="BCS")

    with pytest.raises(IntegrityError), transaction.atomic():
        make_programme(school, code="BCS", name="Duplicate code")


def test_same_programme_name_is_allowed_in_different_schools():
    # AIU has "Doctor of Philosophy" in more than one school; codes tell them apart.
    business = make_school(code="SBSS", name="School of Business & Social Sciences")
    education = make_school(code="SEHS", name="School of Education & Human Sciences")

    make_programme(business, code="PHD-SBSS", name="Doctor of Philosophy")
    make_programme(education, code="PHD-SEHS", name="Doctor of Philosophy")

    assert Programme.objects.filter(name="Doctor of Philosophy").count() == 2


def test_school_with_programmes_cannot_be_deleted():
    school = make_school()
    make_programme(school)

    with pytest.raises(ProtectedError):
        school.delete()


def test_school_without_programmes_can_be_deleted():
    school = make_school()
    school.delete()
    assert not School.objects.exists()


def test_intake_code_is_unique_and_newest_comes_first():
    Intake.objects.create(code="2023-SEP", name="September 2023", start_date=date(2023, 9, 1))
    Intake.objects.create(code="2024-SEP", name="September 2024", start_date=date(2024, 9, 1))

    assert [intake.code for intake in Intake.objects.all()] == ["2024-SEP", "2023-SEP"]

    with pytest.raises(IntegrityError), transaction.atomic():
        Intake.objects.create(code="2024-SEP", name="Duplicate", start_date=date(2024, 9, 1))


def test_schools_are_sorted_by_name():
    make_school(code="SEHS", name="School of Education & Human Sciences")
    make_school(code="CFGS", name="Centre for Foundation and General Studies")

    assert [s.name for s in School.objects.all()] == [
        "Centre for Foundation and General Studies",
        "School of Education & Human Sciences",
    ]
