import pytest
from django.core.management import call_command

from apps.academics.models import Intake, Programme, School

pytestmark = pytest.mark.django_db


def test_seed_loads_aiu_structure_and_can_run_twice():
    call_command("seed_academics", stdout=None)
    call_command("seed_academics", stdout=None)  # second run must not duplicate anything

    assert School.objects.count() == 4
    assert Programme.objects.count() == 23
    assert Intake.objects.count() == 8
    assert Programme.objects.get(code="BCS").school.name == "School of Computing and Informatics"
