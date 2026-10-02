from datetime import date

import pytest
from django.core.management import call_command

from apps.academics.models import Intake, Programme, School, Term

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
