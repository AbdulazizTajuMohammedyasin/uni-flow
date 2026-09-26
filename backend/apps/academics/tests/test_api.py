from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.academics.models import Intake, Programme, School
from apps.accounts.models import User

pytestmark = pytest.mark.django_db

SCHOOLS_URL = "/api/v1/academics/schools/"
PROGRAMMES_URL = "/api/v1/academics/programmes/"
INTAKES_URL = "/api/v1/academics/intakes/"


@pytest.fixture
def client():
    """A client logged in as a student (login itself arrives in M1.6)."""
    user = User.objects.create_user(
        "student@student.aiu.edu.my", "pw-123456!", full_name="Test Student"
    )
    api_client = APIClient()
    api_client.force_authenticate(user)
    return api_client


@pytest.fixture
def structure():
    computing = School.objects.create(code="SCI", name="School of Computing and Informatics")
    business = School.objects.create(code="SBSS", name="School of Business & Social Sciences")
    closed = School.objects.create(code="OLD", name="Closed School", is_active=False)

    Programme.objects.create(
        school=computing,
        code="BCS",
        name="Bachelor in Computer Science (Honours)",
        level="bachelor",
    )
    Programme.objects.create(
        school=computing, code="MCOMP", name="Master of Computing", level="master"
    )
    Programme.objects.create(
        school=business,
        code="BBA",
        name="Bachelor of Business Administration (Honours)",
        level="bachelor",
    )
    Programme.objects.create(
        school=computing,
        code="RETIRED",
        name="Retired Programme",
        level="bachelor",
        is_active=False,
    )
    Programme.objects.create(
        school=closed, code="INCLOSED", name="Programme in a closed school", level="bachelor"
    )
    return {"computing": computing, "business": business}


@pytest.mark.parametrize("url", [SCHOOLS_URL, PROGRAMMES_URL, INTAKES_URL])
def test_login_is_required(url):
    response = APIClient().get(url)

    # No login method exists until M1.6, so DRF answers 403 "permission_denied".
    # From M1.6 (JWT) this becomes 401 "not_authenticated": update this test then.
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_schools_lists_active_schools_sorted_by_name(client, structure):
    response = client.get(SCHOOLS_URL)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": structure["business"].id,
            "code": "SBSS",
            "name": "School of Business & Social Sciences",
        },
        {
            "id": structure["computing"].id,
            "code": "SCI",
            "name": "School of Computing and Informatics",
        },
    ]


def test_programmes_lists_only_active_programmes_of_active_schools(client, structure):
    response = client.get(PROGRAMMES_URL)

    assert response.status_code == 200
    codes = [programme["code"] for programme in response.json()]
    # Sorted by name ("Bachelor in ..." before "Bachelor of ..."); retired and
    # closed-school programmes are hidden.
    assert codes == ["BCS", "BBA", "MCOMP"]


def test_programme_fields(client, structure):
    bcs = next(p for p in client.get(PROGRAMMES_URL).json() if p["code"] == "BCS")

    assert bcs["name"] == "Bachelor in Computer Science (Honours)"
    assert bcs["level"] == "bachelor"
    assert bcs["level_label"] == "Bachelor"
    assert bcs["school"] == structure["computing"].id


def test_programmes_can_be_filtered_by_school(client, structure):
    response = client.get(PROGRAMMES_URL, {"school": structure["computing"].id})

    assert [programme["code"] for programme in response.json()] == ["BCS", "MCOMP"]


def test_programmes_filter_rejects_non_numeric_school(client, structure):
    response = client.get(PROGRAMMES_URL, {"school": "abc"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    assert "school" in response.json()["error"]["fields"]


def test_intakes_lists_active_intakes_newest_first(client):
    Intake.objects.create(code="2023-SEP", name="September 2023", start_date=date(2023, 9, 1))
    Intake.objects.create(code="2024-SEP", name="September 2024", start_date=date(2024, 9, 1))
    Intake.objects.create(
        code="2019-SEP", name="September 2019", start_date=date(2019, 9, 1), is_active=False
    )

    response = client.get(INTAKES_URL)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": response.json()[0]["id"],
            "code": "2024-SEP",
            "name": "September 2024",
            "start_date": "2024-09-01",
        },
        {
            "id": response.json()[1]["id"],
            "code": "2023-SEP",
            "name": "September 2023",
            "start_date": "2023-09-01",
        },
    ]
