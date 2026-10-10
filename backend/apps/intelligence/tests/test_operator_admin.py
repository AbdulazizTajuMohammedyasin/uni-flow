"""The operator's admin (M9.4): actions do the same as the services."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.intelligence.models import AICall, Delivery, Insight, Message, Source, SourceMember
from apps.intelligence.providers import AIBusy, AIRateLimited, ask, fake_provider
from apps.intelligence.services import clear_old_messages
from apps.publishing.models import PublisherType, Status

pytestmark = pytest.mark.django_db

DRAFTS = "/django-admin/intelligence/draftinsight/"
SOURCES = "/django-admin/intelligence/source/"


@pytest.fixture
def operator(client):
    client.force_login(
        User.objects.create_superuser("root@aiu.edu.my", "Str0ng-pass-99", full_name="Root")
    )
    return client


def insight(title, status=Status.DRAFT, origin=Insight.Origin.AI, confidence=0.3):
    return Insight.objects.create(
        audience=Audience.objects.create(),  # everyone
        kind="academic_notice",
        title=title,
        summary="…",
        status=status,
        origin=origin,
        confidence=confidence,
        importance=80,
        published_at=timezone.now() if status == Status.PUBLISHED else None,
    )


def test_the_drafts_page_lists_only_ai_drafts(operator):
    insight("Maybe an exam change?")
    insight("Already published", status=Status.PUBLISHED, confidence=0.9)
    insight("A staff post being written", origin=Insight.Origin.STAFF)

    page = operator.get(DRAFTS).content.decode()

    assert "Maybe an exam change?" in page and "30%" in page
    assert "Already published" not in page and "A staff post being written" not in page


def test_publishing_a_draft_delivers_it_like_everywhere_else(
    operator, django_capture_on_commit_callbacks
):
    student = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    group = Source.objects.create(platform="manual", title="SCI Year 1")
    SourceMember.objects.create(source=group, user=student)
    draft = insight("Exam moved to Monday")
    # An AI item for nobody in particular reaches its group's members.
    draft.publisher_type, draft.publisher_source = PublisherType.SOURCE, group
    draft.save()

    with django_capture_on_commit_callbacks(execute=True):
        operator.post(DRAFTS, {"action": "publish_selected", "_selected_action": [draft.pk]})

    draft.refresh_from_db()
    assert draft.status == Status.PUBLISHED
    assert Delivery.objects.filter(insight=draft, user=student).exists()  # as publish_insight


def test_rejecting_a_draft(operator):
    draft = insight("Rumour")
    operator.post(DRAFTS, {"action": "reject_selected", "_selected_action": [draft.pk]})
    draft.refresh_from_db()
    assert draft.status == Status.ARCHIVED


def test_reviewing_groups(operator):
    group = Source.objects.create(platform="whatsapp_group", title="SCI Year 1", status="active")
    SourceMember.objects.create(
        source=group, user=create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    )
    assert operator.get(SOURCES).status_code == 200  # with member and message counts

    def act(action):
        operator.post(SOURCES, {"action": action, "_selected_action": [group.pk]})
        group.refresh_from_db()

    act("confirm_scope")
    assert group.scope_confirmed
    act("mark_official")
    assert group.trust == Source.Trust.OFFICIAL
    act("mark_normal")
    assert group.trust == Source.Trust.NORMAL
    act("disconnect")
    assert group.status == Source.Status.DISCONNECTED
    act("reconnect")
    assert group.status == Source.Status.ACTIVE


def test_every_ai_request_is_recorded(settings, operator):
    settings.AI_FAST_MODELS = ["fast-a", "fast-b", "fast-c"]
    fake_provider().answers.extend(
        [AIRateLimited("429", retry_after=600), AIBusy("503"), {"ok": True}]
    )

    ask("fast", instructions="…", prompt="…", schema={})

    rows = list(AICall.objects.order_by("id").values_list("model", "outcome"))
    assert rows == [("fast-a", "used_up"), ("fast-b", "busy"), ("fast-c", "answered")]
    assert AICall.objects.first().kind == "fast"
    assert operator.get("/django-admin/intelligence/aicall/").status_code == 200


def test_old_ai_requests_are_cleaned_up_at_night():
    old = AICall.objects.create(kind="fast", model="m", outcome="answered")
    AICall.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=91))
    AICall.objects.create(kind="fast", model="m", outcome="answered")

    assert clear_old_messages()["ai_calls_deleted"] == 1
    assert AICall.objects.count() == 1


def test_admin_lists_with_data_open_on_mysql_without_time_zone_tables(operator):
    """Regression: the year/month/day bar crashed these pages once they had rows."""
    group = Source.objects.create(platform="manual", title="G")
    Message.objects.create(source=group, external_id="1", text="hi", sent_at=timezone.now())
    insight("Something")
    AICall.objects.create(kind="fast", model="m", outcome="answered")
    for page in ("message", "insight", "aicall", "draftinsight", "source"):
        assert operator.get(f"/django-admin/intelligence/{page}/").status_code == 200
