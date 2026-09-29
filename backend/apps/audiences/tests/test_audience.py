from datetime import date

import pytest

from apps.academics.models import Intake, Programme, School
from apps.audiences.models import Audience
from apps.audiences.serializers import AudienceSerializer

pytestmark = pytest.mark.django_db


@pytest.fixture
def data():
    computing = School.objects.create(code="SCI", name="Computing")
    business = School.objects.create(code="SBSS", name="Business")
    return {
        "computing": computing,
        "business": business,
        "bcs": Programme.objects.create(
            school=computing, code="BCS", name="Computer Science", level="bachelor"
        ),
        "oct24": Intake.objects.create(
            code="2024-OCT", name="October 2024", start_date=date(2024, 10, 1)
        ),
        "mar25": Intake.objects.create(
            code="2025-MAR", name="March 2025", start_date=date(2025, 3, 1)
        ),
    }


def audience(schools=(), programmes=(), intakes=()):
    item = Audience.objects.create()
    item.schools.set(schools)
    item.programmes.set(programmes)
    item.intakes.set(intakes)
    return item


@pytest.mark.parametrize(
    ("schools", "programmes", "intakes", "expected"),
    [
        ([], [], [], "All students"),
        (["computing"], [], [], "Computing"),
        (["business", "computing"], [], [], "Business or Computing"),
        ([], ["bcs"], [], "Computer Science"),
        ([], [], ["oct24"], "Intake October 2024"),
        ([], [], ["mar25", "oct24"], "Intakes March 2025 or October 2024"),
        (["computing"], [], ["oct24"], "Computing · Intake October 2024"),
        (["computing"], ["bcs"], ["oct24"], "Computing · Computer Science · Intake October 2024"),
    ],
)
def test_summary(data, schools, programmes, intakes, expected):
    item = audience(
        [data[k] for k in schools], [data[k] for k in programmes], [data[k] for k in intakes]
    )
    assert item.summary() == expected
    assert str(item) == expected


def test_serializer_saves_and_shows_an_audience(data):
    serializer = AudienceSerializer(
        data={"schools": [data["computing"].id], "intakes": [data["oct24"].id]}
    )
    assert serializer.is_valid(), serializer.errors
    item = serializer.save()

    assert AudienceSerializer(item).data == {
        "schools": [data["computing"].id],
        "programmes": [],
        "intakes": [data["oct24"].id],
        "summary": "Computing · Intake October 2024",
    }


def test_serializer_refuses_inactive_choices(data):
    data["oct24"].is_active = False
    data["oct24"].save()

    serializer = AudienceSerializer(data={"intakes": [data["oct24"].id]})
    assert not serializer.is_valid()
    assert "intakes" in serializer.errors
