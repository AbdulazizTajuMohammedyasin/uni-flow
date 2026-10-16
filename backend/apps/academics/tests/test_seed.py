from datetime import date

import pytest
from django.core.management import call_command

from apps.academics.models import Course, Intake, Programme, School, Term

pytestmark = pytest.mark.django_db


def test_seed_loads_aiu_structure_and_can_run_twice():
    call_command("seed_academics", stdout=None)
    call_command("seed_academics", stdout=None)  # second run must not duplicate anything

    assert School.objects.count() == 4
    assert Programme.objects.count() == 23
    assert Intake.objects.count() == 8
    assert Programme.objects.get(code="BCS").school.name == "School of Computing and Informatics"
    assert Term.objects.filter(calendar="undergraduate").count() == 6
    assert Term.objects.filter(calendar="foundation").count() == 6
    semester_3 = Term.objects.get(calendar="undergraduate", academic_session="2025/2026", number=3)
    assert semester_3.name == "2025/2026 Semester 3"
    assert semester_3.starts_on == date(2026, 8, 3)
    foundation_1 = Term.objects.get(calendar="foundation", academic_session="2025/2026", number=1)
    assert foundation_1.name == "Foundation 2025/2026 Semester 1"
    assert foundation_1.starts_on == date(2025, 10, 13)


def test_seed_loads_every_schools_courses():
    call_command("seed_academics", stdout=None)
    call_command("seed_academics", stdout=None)

    assert Course.objects.count() == 376
    dsa = Course.objects.get(code="CCC2113")
    assert (dsa.name, dsa.school.code) == ("Data Structures and Algorithm Analysis", "SCI")
    assert Course.objects.get(code="MPU3113").school.code == "CFGS"
    assert Course.objects.get(code="BSE1023").name == "Education, Training and Human Resource"


def test_seed_gives_an_existing_course_its_official_name():
    call_command("seed_academics", stdout=None)
    course = Course.objects.get(code="CCC2123")
    course.name = "Operating System"  # e.g. as typed by a student who added the class
    course.save()

    call_command("seed_academics", stdout=None)

    course.refresh_from_db()
    assert course.name == "Operating Systems"
