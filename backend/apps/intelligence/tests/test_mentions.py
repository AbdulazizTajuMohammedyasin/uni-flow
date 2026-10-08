"""Which student is "Ali"? (M7.2)"""

from datetime import UTC, datetime

import pytest

from apps.academics.models import School
from apps.accounts.models import UserRole
from apps.accounts.services import create_user
from apps.intelligence.extraction import extract_source
from apps.intelligence.mentions import find_student, is_match, record_mentions
from apps.intelligence.models import Insight, InsightMention, Message, Source, SourceMember
from apps.intelligence.providers import fake_provider

pytestmark = pytest.mark.django_db


@pytest.fixture
def group():
    return Source.objects.create(platform="manual", title="CDE2313 Section A")


def person(name, group=None, aliases="", role=UserRole.STUDENT, school=None):
    domain = "student.aiu.edu.my" if role == UserRole.STUDENT else "aiu.edu.my"
    email = f"{name.lower().replace(' ', '.')}@{domain}"
    user = create_user(email, "Str0ng-pass-99", full_name=name, role=role)
    if role == UserRole.STUDENT:
        profile = user.student_profile
        profile.aliases, profile.school = aliases, school
        profile.save()
    if group is not None:
        SourceMember.objects.create(source=group, user=user)
    return user


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Ali Hassan", True),
        ("ali", True),  # part of the full name, any case
        ("Hassan", True),
        ("Bro Ali", True),  # titles are ignored
        ("Ali Rahman", False),  # another surname
        ("Al", False),  # a word must match whole
        ("Ally", True),  # a nickname
        ("", False),
    ],
)
def test_names_and_nicknames(name, expected):
    ali = person("Ali Hassan", aliases="Ally, AH")
    assert is_match(name, ali) is expected


def test_the_only_ali_in_the_group_is_found(group):
    ali = person("Ali Hassan", group)
    person("Ali Rahman")  # not in this group, and the group has no scope
    assert find_student("Ali", group) == ali


def test_a_name_shared_by_two_members_is_not_a_mention(group):
    person("Ali Hassan", group)
    person("Ali Rahman", group)
    assert find_student("Ali", group) is None
    assert find_student("Ali Rahman", group) is not None  # the full name is clear


def test_two_members_with_the_name_stops_the_search(group):
    school = School.objects.create(code="SCI", name="Computing")
    group.school = school
    group.save()
    person("Sara Lim", group)
    person("Sara Tan", group)
    person("Sara Wong", school=school)  # in the group's school, but never guessed instead
    assert find_student("Sara", group) is None


def test_then_the_students_the_group_is_for(group):
    school = School.objects.create(code="SCI", name="Computing")
    group.school = school
    group.save()
    omar = person("Omar Faruk", school=school)  # didn't add the group, but it's for SCI
    person("Omar Ali")  # another school
    assert find_student("Omar", group) == omar


def test_without_a_scope_nobody_outside_the_group_is_looked_up(group):
    person("Omar Faruk")
    assert find_student("Omar", group) is None


def test_staff_are_never_mentions(group):
    person("Sara Lee", group, role=UserRole.LECTURER)
    assert find_student("Sara", group) is None


def test_a_found_request_records_its_mentions(group):
    ali = person("Ali Hassan", group)
    sara = person("Sara Lim", group, aliases="Sasa")
    person("Zaid Omar", group)
    person("Zaid Ahmad", group)
    message = Message.objects.create(
        source=group,
        external_id="m1",
        sender_name="Dr Lee",
        text="Ali, Sasa and Zaid: please see me about your FYP.",
        sent_at=datetime(2026, 10, 5, 1, tzinfo=UTC),
        triage=Message.Triage.RELEVANT,
    )
    fake_provider().answers.append(
        {
            "changes": [],
            "items": [
                {
                    "kind": "direct_request",
                    "title": "See Dr Lee about your FYP",
                    "summary": "Dr Lee asks Ali, Sasa and Zaid to see him.",
                    "importance": 90,
                    "names": ["Ali", "Sasa", "Zaid"],
                    "confidence": 0.9,
                    "evidence": [{"message_id": message.id, "quote": message.text}],
                }
            ],
        }
    )

    extract_source(group)

    insight = Insight.objects.get()
    mentioned = {(m.user, m.matched_text) for m in insight.mentions.all()}
    assert mentioned == {(ali, "Ali"), (sara, "Sasa")}  # two Zaids: nobody

    record_mentions(insight, ["Ali"], group)  # running again adds nothing
    assert InsightMention.objects.count() == 2
