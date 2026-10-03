"""The visibility rules, checked as a matrix of audiences x students."""

from datetime import date

import pytest
from django.contrib.auth.models import AnonymousUser

from apps.academics.models import Course, Intake, Programme, School, Term
from apps.accounts import semesters
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.audiences.selectors import students_matching, visible_audience_q
from apps.timetable.models import CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

PASSWORD = "Str0ng-pass-99"


@pytest.fixture
def world(monkeypatch):
    sci = School.objects.create(code="SCI", name="Computing")
    sbss = School.objects.create(code="SBSS", name="Business")
    items = {
        "sci": sci,
        "sbss": sbss,
        "bcs": Programme.objects.create(school=sci, code="BCS", name="CS", level="bachelor"),
        "bit": Programme.objects.create(school=sci, code="BIT", name="IT", level="bachelor"),
        "bba": Programme.objects.create(school=sbss, code="BBA", name="BA", level="bachelor"),
        "oct24": Intake.objects.create(
            code="2024-OCT", name="Oct 24", start_date=date(2024, 10, 1)
        ),
        "mar25": Intake.objects.create(code="2025-MAR", name="Mar 25", start_date=date(2025, 3, 1)),
    }

    def student(name, school=None, programme=None, intake=None):
        user = create_user(f"{name}@student.aiu.edu.my", PASSWORD, full_name=name)
        profile = user.student_profile
        profile.school = items.get(school)
        profile.programme = items.get(programme)
        profile.intake = items.get(intake)
        profile.save()
        return user

    items["students"] = {
        "ali": student("ali", "sci", "bcs", "oct24"),
        "sara": student("sara", "sci", "bit", "mar25"),
        "omar": student("omar", "sbss", "bba", "oct24"),
        "new": student("new"),  # hasn't done onboarding
        "half": student("half", "sci"),  # chose a school only (incomplete)
    }

    # Courses and sections: this term, plus one section from last term.
    def term(number, starts):
        return Term.objects.create(
            name=f"T{number}",
            academic_session="2025/26",
            number=number,
            starts_on=starts,
            ends_on=date(starts.year, starts.month + 3, 1),
        )

    # "Today" is 1 Oct 2025, inside the second term (the current one).
    monkeypatch.setattr(semesters, "today", lambda: date(2025, 10, 1))
    last, now = term(1, date(2025, 3, 1)), term(2, date(2025, 9, 1))
    items["cde"] = Course.objects.create(school=sci, code="CDE2313", name="DS")
    items["mgt"] = Course.objects.create(school=sbss, code="MGT1001", name="Management")
    items["cde_a"] = CourseSection.objects.create(course=items["cde"], term=now, code="A")
    items["cde_b"] = CourseSection.objects.create(course=items["cde"], term=now, code="B")
    items["cde_old"] = CourseSection.objects.create(course=items["cde"], term=last, code="A")
    items["mgt_a"] = CourseSection.objects.create(course=items["mgt"], term=now, code="A")
    students = items["students"]
    for name, section in [
        ("ali", "cde_a"),
        ("sara", "cde_b"),
        ("omar", "mgt_a"),
        ("omar", "cde_old"),  # took CDE2313 last term, not now
        ("half", "cde_a"),  # incomplete profile: still only "all students"
    ]:
        SectionEnrollment.objects.create(user=students[name], section=items[section])
    return items


def make_audience(world, schools=(), programmes=(), intakes=(), courses=(), sections=()):
    audience = Audience.objects.create()
    audience.schools.set([world[k] for k in schools])
    audience.programmes.set([world[k] for k in programmes])
    audience.intakes.set([world[k] for k in intakes])
    audience.courses.set([world[k] for k in courses])
    audience.sections.set([world[k] for k in sections])
    return audience


def can_see(user, audience) -> bool:
    return (
        Audience.objects.filter(pk=audience.pk).filter(visible_audience_q(user, via="pk")).exists()
    )


EVERYONE = {"ali", "sara", "omar", "new", "half"}

CASES = [
    # (schools, programmes, intakes) -> students who see it
    (((), (), ()), EVERYONE),
    ((("sci",), (), ()), {"ali", "sara"}),
    ((("sbss",), (), ()), {"omar"}),
    ((("sci", "sbss"), (), ()), {"ali", "sara", "omar"}),
    (((), ("bcs",), ()), {"ali"}),
    (((), ("bcs", "bit"), ()), {"ali", "sara"}),
    (((), ("bcs", "bba"), ()), {"ali", "omar"}),
    (((), (), ("oct24",)), {"ali", "omar"}),
    (((), (), ("mar25",)), {"sara"}),
    (((), (), ("oct24", "mar25")), {"ali", "sara", "omar"}),
    ((("sci",), (), ("oct24",)), {"ali"}),
    ((("sci",), (), ("mar25",)), {"sara"}),
    ((("sbss",), (), ("mar25",)), set()),
    ((("sci",), ("bit",), ()), {"sara"}),
    ((("sci",), ("bba",), ()), set()),  # programme outside the school: nobody
    ((("sci", "sbss"), ("bcs", "bba"), ("oct24",)), {"ali", "omar"}),
    ((("sci",), ("bcs", "bit"), ("oct24", "mar25")), {"ali", "sara"}),
    # (schools, programmes, intakes, courses, sections)
    (((), (), (), ("cde",), ()), {"ali", "sara"}),  # not omar: that was last term
    (((), (), (), ("mgt",), ()), {"omar"}),
    (((), (), (), ("cde", "mgt"), ()), {"ali", "sara", "omar"}),
    (((), (), (), (), ("cde_a",)), {"ali"}),
    (((), (), (), (), ("cde_a", "cde_b")), {"ali", "sara"}),
    (((), (), (), (), ("cde_old",)), {"omar"}),  # an exact section counts in any term
    ((("sci",), (), (), ("cde",), ()), {"ali", "sara"}),
    (((), (), ("oct24",), ("cde",), ()), {"ali"}),
    (((), ("bit",), (), (), ("cde_a",)), set()),
    ((("sbss",), (), (), ("cde",), ()), set()),
]


@pytest.mark.parametrize(("choice", "expected"), CASES)
def test_visibility_matrix(world, choice, expected):
    audience = make_audience(world, *choice)
    students = world["students"]

    seen_by = {name for name, user in students.items() if can_see(user, audience)}
    matched = {user.email.split("@")[0] for user in students_matching(audience)}

    assert seen_by == expected
    assert matched == expected  # the two functions agree


def test_staff_see_everything_and_visitors_nothing(world):
    audience = make_audience(world, ("sbss",), ("bba",), ("mar25",))
    lecturer = create_user("lee@aiu.edu.my", PASSWORD, full_name="Lee", role="lecturer")
    school_staff = create_user("ss@aiu.edu.my", PASSWORD, full_name="SS", role="school_staff")

    assert can_see(lecturer, audience)
    assert can_see(school_staff, audience)
    assert not can_see(AnonymousUser(), audience)
    assert lecturer not in students_matching(audience)  # only students are notified


def test_suspended_and_inactive_students_are_not_matched(world):
    audience = make_audience(world)
    ali, sara = world["students"]["ali"], world["students"]["sara"]
    ali.is_suspended = True
    ali.save()
    sara.is_active = False
    sara.save()

    matched = set(students_matching(audience))
    assert ali not in matched
    assert sara not in matched


def test_no_duplicate_rows(world):
    many = [make_audience(world, ("sci", "sbss"), ("bcs", "bit", "bba"), ("oct24", "mar25"))]
    many.append(make_audience(world))
    ali = world["students"]["ali"]

    visible = Audience.objects.filter(visible_audience_q(ali, via="pk"))
    assert visible.count() == 2
    assert students_matching(many[0]).count() == 3  # ali, sara, omar once each


def test_two_sections_of_one_course_count_once(world):
    ali = world["students"]["ali"]
    SectionEnrollment.objects.create(user=ali, section=world["cde_b"])
    audience = make_audience(world, courses=("cde",))

    assert list(students_matching(audience)).count(ali) == 1
    assert Audience.objects.filter(visible_audience_q(ali, via="pk")).count() == 1
