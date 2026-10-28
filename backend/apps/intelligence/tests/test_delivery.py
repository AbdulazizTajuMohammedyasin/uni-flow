"""Who gets an insight, how relevant it is to them, which level and why (M7.4)."""

from datetime import UTC, date, datetime

import pytest
from django.utils import timezone

from apps.academics.models import Course, Intake, Programme, School, Term
from apps.accounts import semesters
from apps.accounts.models import UserRole
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.intelligence import merging
from apps.intelligence.mentions import record_mentions
from apps.intelligence.models import Delivery, Insight, Message, Source, SourceMember
from apps.intelligence.services import publish_insight, save_ai_insight
from apps.timetable.models import CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def today(monkeypatch):
    monkeypatch.setattr(semesters, "today", lambda: date(2026, 10, 5))


@pytest.fixture
def uni():
    """SCI with Computer Science (BCS); CDE2313 Sections A and B; a group with Ali in it."""
    term = Term.objects.create(
        name="T1",
        academic_session="2026/2027",
        number=1,
        starts_on=date(2026, 9, 28),
        ends_on=date(2027, 1, 29),
    )
    sci = School.objects.create(code="SCI", name="School of Computing")
    biz = School.objects.create(code="SBM", name="School of Business")
    bcs = Programme.objects.create(
        code="BCS", school=sci, name="Computer Science", level="bachelor"
    )
    bit = Programme.objects.create(code="BIT", school=sci, name="IT", level="bachelor")
    bba = Programme.objects.create(code="BBA", school=biz, name="Business", level="bachelor")
    intake = Intake.objects.create(
        code="2025-OCT", name="October 2025", start_date=date(2025, 10, 1)
    )
    course = Course.objects.create(school=sci, code="CDE2313", name="Data Structures")
    a = CourseSection.objects.create(course=course, term=term, code="A")
    b = CourseSection.objects.create(course=course, term=term, code="B")
    group = Source.objects.create(platform="manual", title="SCI Year 2")

    def student(name, programme, section=None, interests=(), info_types=(), member=False):
        user = create_user(f"{name.lower()}@student.aiu.edu.my", "Str0ng-pass-99", full_name=name)
        profile = user.student_profile
        profile.school, profile.programme, profile.intake = programme.school, programme, intake
        profile.interests, profile.info_types = list(interests), list(info_types)
        profile.save()
        if section:
            SectionEnrollment.objects.create(user=user, section=section)
        if member:
            SourceMember.objects.create(source=group, user=user)
        return user

    people = {
        "ali": student("Ali Hassan", bcs, a, interests=["ai"], member=True),
        "sara": student("Sara Lim", bcs, b),
        "omar": student("Omar Faruk", bit),
        "zara": student("Zara Tan", bba),
    }
    create_user("lee@aiu.edu.my", "Str0ng-pass-99", full_name="Dr Lee", role=UserRole.LECTURER)
    return {"group": group, "sci": sci, "bcs": bcs, "course": course, "a": a, **people}


def found(uni, kind="academic_notice", confidence=0.9, audience=None, **fields):
    """What the AI found in a message of the group (published if sure enough)."""
    message = Message.objects.create(
        source=uni["group"],
        external_id=f"m{Message.objects.count()}",
        sender_name="Office",
        text="…",
        sent_at=datetime(2026, 10, 5, 1, tzinfo=UTC),
    )
    return save_ai_insight(
        source=uni["group"],
        kind=kind,
        title="Something",
        summary="Something happened.",
        confidence=confidence,
        evidence=[(message, "…")],
        audience=audience or {},
        **fields,
    )


def delivered(insight):
    """{first name: (tier, relevance, reason)}"""
    return {
        d.user.full_name.split()[0].lower(): (d.tier, d.relevance, d.reason)
        for d in Delivery.objects.filter(insight=insight).select_related("user")
    }


def test_a_change_to_my_class_is_important_only_for_my_section(uni):
    change = found(
        uni,
        kind="class_moved",
        audience={"sections": [uni["a"]]},
        importance=80,
        data={"section_ids": [uni["a"].id], "date": "2026-10-06", "course_id": uni["course"].id},
    )
    assert delivered(change) == {"ali": ("important", 90, "You are in CDE2313 Section A")}


def test_a_notice_for_my_programme(uni):
    notice = found(uni, audience={"programmes": [uni["bcs"]]}, importance=75)
    assert delivered(notice) == {
        "ali": ("important", 80, 'You are in the group "SCI Year 2"'),  # the stronger reason
        "sara": ("important", 65, "For Computer Science students"),
    }


def test_for_nobody_in_particular_only_the_groups_members(uni):
    notice = found(uni, importance=40)
    assert delivered(notice) == {"ali": ("digest", 80, 'You are in the group "SCI Year 2"')}


def test_a_staff_post_for_everyone_reaches_every_student_but_no_staff(uni):
    post = Insight.objects.create(
        audience=Audience.objects.create(),  # an empty audience = all students
        origin=Insight.Origin.STAFF,
        kind="student_affairs",
        title="Library closed on Friday",
        summary="…",
        topics=["ai"],
    )
    publish_insight(post, None)
    result = delivered(post)
    assert set(result) == {"ali", "sara", "omar", "zara"}
    assert result["sara"] == ("digest", 40, "For all students")
    assert result["ali"] == ("digest", 50, "Matches your interest: Artificial Intelligence")


def test_a_request_reaches_only_the_named_student(uni):
    request = found(uni, kind="direct_request", audience={"schools": [uni["sci"]]}, importance=60)
    assert delivered(request) == {}  # published before the names are matched: nobody yet
    record_mentions(request, ["Ali"], uni["group"])
    assert delivered(request) == {"ali": ("direct", 100, "You were named in this message")}


def test_a_request_for_someone_else_never_reaches_the_group(uni):
    """ "Dr Basheer requests Amir Wuhab", in a group Amir didn't add: the members don't get
    it, not even in the digest."""
    request = found(uni, kind="direct_request", importance=80, action_required=True)
    record_mentions(request, ["Amir Wuhab"], uni["group"])  # nobody matches
    assert delivered(request) == {}  # no delivery, so no alert or digest line either


def test_action_required(uni):
    deadline = found(
        uni, kind="deadline", audience={"programmes": [uni["bcs"]]}, importance=50,
        action_required=True, action_text="Submit the form",
    )  # fmt: skip
    assert delivered(deadline)["sara"][0] == "action"


def test_an_unsure_finding_goes_to_the_digest_only(uni):
    rumour = found(uni, confidence=0.6, audience={"programmes": [uni["bcs"]]}, importance=90)
    assert {tier for tier, _, _ in delivered(rumour).values()} == {"digest"}


def test_a_kind_of_information_i_switched_off(uni):
    sara = uni["sara"].student_profile
    sara.info_types = ["internship"]  # Sara only wants internships
    sara.save()
    notice = found(
        uni, audience={"schools": [uni["sci"]]}, importance=40, info_type="academic_notice"
    )
    assert "sara" not in delivered(notice)  # 55 - 40 = 15: below the digest threshold
    assert "omar" in delivered(notice)


def test_running_again_keeps_read_and_adds_a_forwarding_groups_members(uni):
    notice = found(uni, audience={"courses": [uni["course"]]}, importance=40)
    Delivery.objects.filter(user=uni["ali"]).update(read_at=timezone.now())

    other = Source.objects.create(platform="manual", title="BIT friends")
    SourceMember.objects.create(source=other, user=uni["omar"])
    copy = Message.objects.create(
        source=other, external_id="fwd", text="Fwd: …", sent_at=timezone.now()
    )
    merging.add_evidence(notice, [(copy, "Fwd: …")], 0.9)

    result = delivered(notice)
    assert result["omar"] == ("digest", 80, 'You are in the group "BIT friends"')
    assert Delivery.objects.get(insight=notice, user=uni["ali"]).read_at is not None


def test_drafts_reach_nobody(uni):
    draft = found(uni, confidence=0.3, audience={"programmes": [uni["bcs"]]})
    assert delivered(draft) == {}
