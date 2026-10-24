"""'Year 2' targeting: the semester comes from the intake (or the student's override)."""

from datetime import date

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction

from apps.academics.models import Intake, Programme, School
from apps.accounts import semesters
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.audiences.selectors import students_matching, visible_audience_q
from apps.audiences.serializers import AudienceSerializer

pytestmark = pytest.mark.django_db

TODAY = date(2026, 10, 15)


@pytest.fixture
def students(monkeypatch):
    monkeypatch.setattr(semesters, "today", lambda: TODAY)
    call_command("seed_academics", stdout=None)  # official terms up to Aug 2026, then estimated
    school = School.objects.create(code="SCI-T", name="Computing")
    programme = Programme.objects.create(school=school, code="BCS-T", name="CS", level="bachelor")
    foundation = Programme.objects.create(
        school=school, code="FND-T", name="Foundation", level="foundation"
    )

    def student(name, intake_start, override=None, programme=programme):
        intake = Intake.objects.create(code=name, name=name, start_date=intake_start)
        user = create_user(f"{name}@student.aiu.edu.my", "Str0ng-pass-99", full_name=name)
        profile = user.student_profile
        profile.school, profile.programme, profile.intake = school, programme, intake
        profile.semester_override = override
        profile.save()
        return user

    # On 15 Oct 2026, counting the official terms that started since the intake:
    return {
        "sem1": student("sem1", date(2026, 10, 1)),  # no term started yet
        "sem2": student("sem2", date(2026, 3, 1)),  # Mar 26, Aug 26
        "sem3": student("sem3", date(2025, 10, 1)),  # Oct 25, Mar 26, Aug 26
        "sem5": student("sem5", date(2025, 3, 1)),  # Mar 25 ... Aug 26
        "sem6": student("sem6", date(2024, 10, 1)),  # all six terms
        "late": student("late", date(2026, 10, 1), override=4),  # says semester 4
        # Foundation calendar: Oct 25 (13 Oct), Feb 26, Jun 26, and Oct 26 (12 Oct, worked out
        # from last year's calendar) -> semester 4
        "fnd4": student("fnd4", date(2025, 10, 1), programme=foundation),
        "new": create_user("new@student.aiu.edu.my", "Str0ng-pass-99", full_name="New"),
    }


@pytest.mark.parametrize(
    ("low", "high", "expected"),
    [
        (None, None, {"sem1", "sem2", "sem3", "sem5", "sem6", "late", "fnd4", "new"}),
        (1, 1, {"sem1"}),
        (4, 6, {"sem5", "sem6", "late", "fnd4"}),  # "Year 2"
        (2, None, {"sem2", "sem3", "sem5", "sem6", "late", "fnd4"}),
        (None, 3, {"sem1", "sem2", "sem3"}),
        (3, 3, {"sem3"}),
        (7, None, set()),  # nobody can be in semester 7 yet
    ],
)
def test_semester_targeting(students, low, high, expected):
    audience = Audience.objects.create(semester_min=low, semester_max=high)

    seen_by = {
        name
        for name, user in students.items()
        if Audience.objects.filter(pk=audience.pk)
        .filter(visible_audience_q(user, via="pk"))
        .exists()
    }
    matched = {user.email.split("@")[0] for user in students_matching(audience)}

    assert seen_by == expected
    assert matched == expected  # the two functions agree


def test_semester_text_and_range_rules():
    assert Audience(semester_min=4, semester_max=6).semester_text() == "Semesters 4–6"
    assert Audience(semester_min=2, semester_max=2).semester_text() == "Semester 2"
    assert Audience(semester_min=5).semester_text() == "Semester 5 and above"
    assert Audience(semester_max=2).semester_text() == "Up to semester 2"

    assert not AudienceSerializer(data={"semester_min": 4, "semester_max": 3}).is_valid()
    with transaction.atomic(), pytest.raises(IntegrityError):
        Audience.objects.create(semester_min=4, semester_max=3)
