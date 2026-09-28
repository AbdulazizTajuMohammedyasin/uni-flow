from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.academics.models import Intake, Programme, School
from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

MANAGE = "/api/v1/manage/academics/"
PASSWORD = "Str0ng-pass-99"


def logged_in(role, email):
    api = APIClient()
    api.force_authenticate(create_user(email, PASSWORD, full_name="Someone", role=role))
    return api


@pytest.fixture
def admin():
    return logged_in("university_admin", "ua@aiu.edu.my")


@pytest.fixture
def computing():
    return School.objects.create(code="SCI", name="School of Computing and Informatics")


def test_only_admins_can_manage_academics(computing):
    assert APIClient().get(f"{MANAGE}schools/").status_code == 401
    student = logged_in("student", "ali@student.aiu.edu.my")
    assert student.get(f"{MANAGE}schools/").status_code == 403
    lecturer = logged_in("lecturer", "lee@aiu.edu.my")
    assert lecturer.post(f"{MANAGE}schools/", {"code": "X", "name": "X"}).status_code == 403
    super_admin = logged_in("super_admin", "root@aiu.edu.my")
    assert super_admin.get(f"{MANAGE}schools/").status_code == 200


def test_create_and_edit_a_school(admin):
    created = admin.post(f"{MANAGE}schools/", {"code": "SOE", "name": "School of Education"})
    assert created.status_code == 201
    school_id = created.json()["id"]

    edited = admin.patch(f"{MANAGE}schools/{school_id}/", {"name": "School of Ed"}, format="json")
    assert edited.status_code == 200
    assert School.objects.get(pk=school_id).name == "School of Ed"


def test_codes_must_be_unique(admin, computing):
    response = admin.post(f"{MANAGE}schools/", {"code": "SCI", "name": "Another"})
    assert response.status_code == 400
    assert "code" in response.json()["error"]["fields"]


def test_deactivating_hides_the_item_from_the_read_lists(admin, computing):
    student = logged_in("student", "ali@student.aiu.edu.my")
    programme = Programme.objects.create(
        school=computing, code="BCS", name="Computer Science", level="bachelor"
    )
    intake = Intake.objects.create(
        code="2024-OCT", name="October 2024", start_date=date(2024, 10, 1)
    )

    admin.patch(f"{MANAGE}programmes/{programme.id}/", {"is_active": False}, format="json")
    admin.patch(f"{MANAGE}intakes/{intake.id}/", {"is_active": False}, format="json")
    admin.patch(f"{MANAGE}schools/{computing.id}/", {"is_active": False}, format="json")

    assert student.get("/api/v1/academics/schools/").json() == []
    assert student.get("/api/v1/academics/programmes/").json() == []
    assert student.get("/api/v1/academics/intakes/").json() == []
    # The staff area still lists them, so they can be switched back on.
    assert admin.get(f"{MANAGE}schools/").json()["results"][0]["is_active"] is False


def test_programmes_filter_by_school_and_search(admin, computing):
    business = School.objects.create(code="SBSS", name="School of Business")
    Programme.objects.create(
        school=computing, code="BCS", name="Computer Science", level="bachelor"
    )
    Programme.objects.create(school=business, code="BBA", name="Business Admin", level="bachelor")

    by_school = admin.get(f"{MANAGE}programmes/", {"school": computing.id}).json()["results"]
    assert [p["code"] for p in by_school] == ["BCS"]
    searched = admin.get(f"{MANAGE}programmes/", {"search": "business"}).json()["results"]
    assert [p["code"] for p in searched] == ["BBA"]


def test_nothing_can_be_deleted(admin, computing):
    assert admin.delete(f"{MANAGE}schools/{computing.id}/").status_code == 405
    assert School.objects.filter(pk=computing.id).exists()
