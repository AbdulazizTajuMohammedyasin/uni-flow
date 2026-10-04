from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.admin.sites import site
from django.db import IntegrityError, transaction
from django.test import Client, RequestFactory

from apps.academics.models import School
from apps.accounts.models import User
from apps.audiences.models import Audience
from apps.intelligence.models import Insight, Message, Source
from apps.intelligence.services import clear_old_messages, save_ai_insight

pytestmark = pytest.mark.django_db

SENT = datetime(2026, 10, 1, 9, 12, tzinfo=UTC)


@pytest.fixture
def group():
    return Source.objects.create(platform="whatsapp_group", external_id="g1", title="CDE2313 Sec A")


@pytest.fixture
def message(group):
    return Message.objects.create(
        source=group,
        external_id="m1",
        sender_name="Dr Lee",
        text="Hi all. Tomorrow's CDE2313 class has been moved from 10 AM to 2 PM.",
        sent_at=SENT,
    )


def found(group, message, confidence, **extra):
    return save_ai_insight(
        source=group,
        kind="class_moved",
        title="CDE2313 class moved to 2 PM tomorrow",
        summary="Tomorrow's CDE2313 lecture moves from 10:00 to 14:00.",
        confidence=confidence,
        evidence=[(message, "Tomorrow's CDE2313 class has been moved from 10 AM to 2 PM.")],
        **extra,
    )


# --- The "how sure" rule ----------------------------------------------------------------


def test_a_sure_insight_is_published(group, message):
    insight = found(group, message, 0.9, importance=80)

    assert insight.status == "published"
    assert insight.published_at is not None
    assert insight.is_unconfirmed is False
    assert (insight.origin, insight.publisher_type, insight.publisher_source) == (
        "ai",
        "source",
        group,
    )
    assert insight.audience.summary() == "All students"


def test_an_unsure_insight_is_published_but_marked_not_confirmed(group, message):
    insight = found(group, message, 0.6)
    assert insight.status == "published"
    assert insight.is_unconfirmed is True


def test_a_very_unsure_insight_waits_as_a_draft(group, message):
    insight = found(group, message, 0.3)
    assert insight.status == "draft"
    assert insight.published_at is None


def test_the_audience_the_ai_worked_out_is_saved(group, message):
    school = School.objects.create(code="SCI", name="Computing")
    insight = found(group, message, 0.9, audience={"schools": [school], "semester_min": 4})
    assert insight.audience.summary() == "Computing · Semester 4 and above"


# --- Evidence ---------------------------------------------------------------------------


def test_the_quote_stays_after_the_privacy_clean_up(group, message):
    insight = found(group, message, 0.9)
    clear_old_messages(SENT + timedelta(days=61))

    message.refresh_from_db()
    assert message.text == ""
    assert (
        insight.evidence.get().quote
        == "Tomorrow's CDE2313 class has been moved from 10 AM to 2 PM."
    )


# --- Database rules ---------------------------------------------------------------------


def test_publisher_rules(group):
    def insight(**fields):
        return Insight.objects.create(
            audience=Audience.objects.create(),
            kind="academic_notice",
            title="T",
            summary="S",
            **fields,
        )

    with transaction.atomic(), pytest.raises(IntegrityError):
        insight(publisher_type="source")  # which group?
    with transaction.atomic(), pytest.raises(IntegrityError):
        insight(publisher_type="university", publisher_source=group)
    with transaction.atomic(), pytest.raises(IntegrityError):
        insight(publisher_type="university", confidence=1.5)
    insight(publisher_type="university")  # fine


# --- Official staff posts in the Django admin ---------------------------------------------


@pytest.fixture
def admin_client():
    admin = User.objects.create_superuser("root@aiu.edu.my", "Str0ng-pass-99", full_name="Root")
    client = Client()
    client.force_login(admin)
    return client, admin


def test_staff_write_a_post_in_the_admin_and_publish_it(admin_client):
    client, admin = admin_client
    response = client.post(
        "/django-admin/intelligence/insight/add/",
        {
            "kind": "industry_visit",
            "title": "Industry visit to Intel",
            "summary": "Visit Intel Penang on Friday. Register by Wednesday.",
            "importance": "70",
            "action_text": "",
            "info_type": "industry_visit",
            "topics": "[]",
            "location": "",
            "link": "",
            "audience": "",
            "publisher_type": "university",
            "publisher_school": "",
            "evidence-TOTAL_FORMS": "0",
            "evidence-INITIAL_FORMS": "0",
        },
    )
    assert response.status_code == 302, response.content.decode()[:2000]

    post = Insight.objects.get(title="Industry visit to Intel")
    assert (post.origin, post.confidence, post.status, post.created_by) == (
        "staff",
        1.0,
        "draft",
        admin,
    )
    assert post.audience.summary() == "All students"  # left empty

    client.post(
        "/django-admin/intelligence/insight/",
        {"action": "publish_selected", "_selected_action": [post.id]},
    )
    post.refresh_from_db()
    assert post.status == "published"


def test_retracting_and_correcting_an_ai_insight(admin_client, group, message):
    client, admin = admin_client
    insight = found(group, message, 0.6)
    client.post(
        "/django-admin/intelligence/insight/",
        {"action": "retract_selected", "_selected_action": [insight.id]},
    )
    insight.refresh_from_db()
    assert insight.status == "archived"
    assert client.get(f"/django-admin/intelligence/insight/{insight.id}/change/").status_code == 200

    # Saving a fix to an AI insight records who corrected it.
    request = RequestFactory().post("/")
    request.user = admin
    insight.title = "CDE2313 class moved to 3 PM tomorrow"
    site._registry[Insight].save_model(request, insight, form=None, change=True)
    insight.refresh_from_db()
    assert insight.corrected_by == admin
    assert insight.corrected_at is not None
    assert insight.origin == "ai"  # still the AI's finding, now corrected
