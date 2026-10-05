from datetime import date, time
from io import BytesIO

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.academics.models import Intake, Programme, School, Term
from apps.accounts import semesters
from apps.accounts.services import create_user
from apps.intelligence import files
from apps.intelligence.providers import fake_provider
from apps.timetable.models import CourseSection, SectionEnrollment

pytestmark = pytest.mark.django_db

IMPORTS = "/api/v1/timetable/imports/"


def classes(code, day):
    return {
        "classes": [
            {
                "course_code": code,
                "course_name": code,
                "section": "A",
                "meetings": [{"day": day, "start": "10:00", "end": "12:00", "room": "B2"}],
            }
        ]
    }


@pytest.fixture(autouse=True)
def setting(settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = tmp_path
    monkeypatch.setattr(semesters, "today", lambda: date(2025, 11, 1))
    Term.objects.create(
        name="T1",
        academic_session="2025/2026",
        number=1,
        starts_on=date(2025, 10, 27),
        ends_on=date(2026, 2, 27),
    )


def student(email="ali@student.aiu.edu.my"):
    school, _ = School.objects.get_or_create(code="SCI", defaults={"name": "Computing"})
    programme, _ = Programme.objects.get_or_create(
        code="BCS", defaults={"school": school, "name": "Computer Science", "level": "bachelor"}
    )
    intake, _ = Intake.objects.get_or_create(
        code="2025-OCT", defaults={"name": "October 2025", "start_date": date(2025, 10, 1)}
    )
    user = create_user(email, "Str0ng-pass-99", full_name=email)
    profile = user.student_profile
    profile.school, profile.programme, profile.intake = school, programme, intake
    profile.save()
    api = APIClient()
    api.force_authenticate(user)
    return user, api


def timetable_xlsx():
    workbook = openpyxl.Workbook()
    workbook.active.title = "BBA Mar 2025"
    workbook.active.append(["Tuesday", time(8), "MGT1001"])
    other = workbook.create_sheet("BCS Oct 2025")
    other.append(["Monday", time(10), "CDE2313"])
    buffer = BytesIO()
    workbook.save(buffer)
    return SimpleUploadedFile("SCI timetable.xlsx", buffer.getvalue())


def upload(api, django_capture_on_commit_callbacks):
    """Upload the sheet and let the background reading run (with the fake AI)."""
    fake_provider().answers.extend([classes("MGT1001", "tuesday"), classes("CDE2313", "monday")])
    with django_capture_on_commit_callbacks(execute=True):
        response = api.post(IMPORTS, {"file": timetable_xlsx()}, format="multipart")
    assert response.status_code == 201, response.json()
    assert response.json()["status"] == "reading"
    return api.get(f"{IMPORTS}{response.json()['id']}/").json()


def test_upload_and_see_my_tab(django_capture_on_commit_callbacks):
    _, api = student()
    body = upload(api, django_capture_on_commit_callbacks)

    assert body["status"] == "ready"
    assert body["file_name"] == "SCI timetable.xlsx"
    assert body["tab"] == "BCS Oct 2025"
    assert body["tabs"] == ["BBA Mar 2025", "BCS Oct 2025"]
    assert [row["course_code"] for row in body["rows"]] == ["CDE2313"]
    assert [item["id"] for item in api.get(IMPORTS).json()] == [body["id"]]


def test_switch_tab_keep_some_classes_and_confirm(django_capture_on_commit_callbacks):
    user, api = student()
    body = upload(api, django_capture_on_commit_callbacks)
    url = f"{IMPORTS}{body['id']}/"

    switched = api.patch(url, {"tab": "BBA Mar 2025"}, format="json").json()
    assert [row["course_code"] for row in switched["rows"]] == ["MGT1001"]
    assert api.patch(url, {"tab": "Nope"}, format="json").status_code == 400

    api.patch(url, {"tab": "BCS Oct 2025"}, format="json")
    confirmed = api.post(f"{url}confirm/", {}, format="json").json()

    assert confirmed["status"] == "confirmed"
    assert confirmed["report"]["created_sections"] == ["CDE2313 Section A"]
    assert SectionEnrollment.objects.filter(user=user, section__course__code="CDE2313").exists()
    assert api.post(f"{url}confirm/", {}, format="json").status_code == 400  # only once


def test_discard_saves_nothing(django_capture_on_commit_callbacks):
    _, api = student()
    body = upload(api, django_capture_on_commit_callbacks)
    response = api.post(f"{IMPORTS}{body['id']}/discard/")
    assert response.json()["status"] == "discarded"
    assert CourseSection.objects.count() == 0


def test_other_students_cannot_see_my_import(django_capture_on_commit_callbacks):
    _, api = student()
    body = upload(api, django_capture_on_commit_callbacks)
    _, sara = student("sara@student.aiu.edu.my")
    assert sara.get(f"{IMPORTS}{body['id']}/").status_code == 404
    assert sara.post(f"{IMPORTS}{body['id']}/confirm/", {}, format="json").status_code == 404


def test_a_link_that_only_opens_with_an_aiu_account(monkeypatch):
    _, api = student()
    # Google answers with its sign-in page instead of the file.
    monkeypatch.setattr(files, "_http_get", lambda url: (None, b"<html>Sign in</html>"))
    link = "https://docs.google.com/spreadsheets/d/1Uy5/edit?gid=124#gid=124"

    response = api.post(IMPORTS, {"link": link}, format="json")
    assert response.status_code == 400
    message = str(response.json()["error"]["fields"]["link"])
    assert "File → Download → Microsoft Excel (.xlsx)" in message


def test_a_file_or_a_link_is_needed():
    _, api = student()
    assert api.post(IMPORTS, {}, format="json").status_code == 400
    assert APIClient().get(IMPORTS).status_code == 401
