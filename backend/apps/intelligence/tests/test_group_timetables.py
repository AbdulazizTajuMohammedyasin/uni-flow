"""A timetable shared in a group is offered to members without classes (M6.5)."""

from datetime import date, time
from io import BytesIO

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.academics.models import Course, Intake, Programme, School, Term
from apps.accounts import semesters
from apps.accounts.models import UserRole
from apps.accounts.services import create_user
from apps.intelligence import connector, timetable_reading
from apps.intelligence.models import Message, Source, SourceMember, TimetableImport
from apps.intelligence.providers import fake_provider
from apps.timetable.models import CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

IMPORTS = "/api/v1/timetable/imports/"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture(autouse=True)
def setting(settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = tmp_path
    monkeypatch.setattr(semesters, "today", lambda: date(2025, 11, 1))


@pytest.fixture
def term():
    return Term.objects.create(
        name="T1",
        academic_session="2025/2026",
        number=1,
        starts_on=date(2025, 10, 27),
        ends_on=date(2026, 2, 27),
    )


def classes(code, day):
    meeting = {"day": day, "start": "10:00", "end": "12:00", "room": "B2"}
    return {"classes": [{"course_code": code, "section": "A", "meetings": [meeting]}]}


def student(email, group, role=UserRole.STUDENT):
    school, _ = School.objects.get_or_create(code="SCI", defaults={"name": "Computing"})
    programme, _ = Programme.objects.get_or_create(
        code="BCS", defaults={"school": school, "name": "Computer Science", "level": "bachelor"}
    )
    intake, _ = Intake.objects.get_or_create(
        code="2025-OCT", defaults={"name": "October 2025", "start_date": date(2025, 10, 1)}
    )
    user = create_user(email, "Str0ng-pass-99", full_name=email, role=role)
    if role == UserRole.STUDENT:
        profile = user.student_profile
        profile.school, profile.programme, profile.intake = school, programme, intake
        profile.save()
    SourceMember.objects.create(source=group, user=user)
    return user


@pytest.fixture
def group():
    return Source.objects.create(
        platform=Source.Platform.WHATSAPP_GROUP,
        external_id="123@g.us",
        title="SCI Year 1",
        status=Source.Status.ACTIVE,
    )


def xlsx():
    workbook = openpyxl.Workbook()
    workbook.active.title = "BBA Mar 2025"
    workbook.active.append(["Tuesday", time(8), "MGT1001"])
    workbook.create_sheet("BCS Oct 2025").append(["Monday", time(10), "CDE2313"])
    buffer = BytesIO()
    workbook.save(buffer)
    return SimpleUploadedFile("SCI timetable.xlsx", buffer.getvalue())


def share(group, upload, capture):
    """A file arrives in the group through the WhatsApp connector."""
    message = Message.objects.create(
        source=group, external_id="M1", sender_name="Office", sent_at=timezone.now()
    )
    with capture(execute=True):
        connector.attach_file(message, upload)
    return message


def test_members_without_classes_get_is_this_your_timetable(
    term, group, django_capture_on_commit_callbacks
):
    ali = student("ali@student.aiu.edu.my", group)
    sara = student("sara@student.aiu.edu.my", group)  # already has her classes
    course = Course.objects.create(school=sara.student_profile.school, code="X1", name="X")
    section = CourseSection.objects.create(course=course, term=term, code="A")
    SectionEnrollment.objects.create(user=sara, section=section)
    student("lee@aiu.edu.my", group, role=UserRole.LECTURER)  # not a student
    fake_provider().answers.extend([classes("MGT1001", "tuesday"), classes("CDE2313", "monday")])

    share(group, xlsx(), django_capture_on_commit_callbacks)

    offered = TimetableImport.objects.get()
    assert offered.user == ali
    assert offered.status == "ready"
    assert offered.tab == "BCS Oct 2025"  # Ali's programme and intake
    assert len(fake_provider().calls) == 2  # each tab read once

    api = APIClient()
    api.force_authenticate(ali)
    [shown] = api.get(IMPORTS).json()
    assert (shown["status"], shown["group"]) == ("ready", "SCI Year 1")
    assert [row["course_code"] for row in shown["rows"]] == ["CDE2313"]

    confirmed = api.post(f"{IMPORTS}{shown['id']}/confirm/", {}, format="json").json()
    assert confirmed["status"] == "confirmed"
    assert SectionEnrollment.objects.filter(user=ali, section__course__code="CDE2313").exists()


def test_nobody_needs_it_so_the_ai_is_not_asked(term, group, django_capture_on_commit_callbacks):
    share(group, xlsx(), django_capture_on_commit_callbacks)  # the group has no members
    assert TimetableImport.objects.count() == 0
    assert fake_provider().calls == []


def test_a_photo_that_is_not_a_timetable_is_ignored(
    term, group, django_capture_on_commit_callbacks
):
    student("ali@student.aiu.edu.my", group)
    fake_provider().answers.append({"classes": []})  # e.g. a photo of a poster

    share(group, SimpleUploadedFile("poster.png", PNG), django_capture_on_commit_callbacks)

    assert TimetableImport.objects.count() == 0


def test_offered_once_and_my_own_uploads_show_no_group(
    term, group, django_capture_on_commit_callbacks
):
    ali = student("ali@student.aiu.edu.my", group)
    fake_provider().answers.extend([classes("MGT1001", "tuesday"), classes("CDE2313", "monday")])
    message = share(group, xlsx(), django_capture_on_commit_callbacks)

    assert timetable_reading.offer_to_group(message.files.get()) == []  # already offered
    assert TimetableImport.objects.filter(user=ali).count() == 1

    api = APIClient()
    api.force_authenticate(ali)
    fake_provider().answers.extend([classes("MGT1001", "tuesday"), classes("CDE2313", "monday")])
    with django_capture_on_commit_callbacks(execute=True):
        own = api.post(IMPORTS, {"file": xlsx()}, format="multipart").json()
    assert api.get(f"{IMPORTS}{own['id']}/").json()["group"] == ""
