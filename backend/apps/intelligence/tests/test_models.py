from datetime import UTC, datetime

import pytest
from django.db import IntegrityError, transaction

from apps.accounts.services import create_user
from apps.intelligence.models import Message, Source, SourceMember

pytestmark = pytest.mark.django_db

SENT = datetime(2026, 10, 1, 9, 12, tzinfo=UTC)


@pytest.fixture
def group():
    return Source.objects.create(
        platform="whatsapp_group", external_id="1203630@g.us", title="CDE2313 Sec A"
    )


def test_a_new_source_waits_to_be_joined_and_is_not_official(group):
    assert group.status == "pending"
    assert group.trust == "normal"
    assert group.scope_confirmed is False
    assert str(group) == "CDE2313 Sec A (WhatsApp group)"


def test_a_chat_is_connected_only_once_per_platform(group):
    with transaction.atomic(), pytest.raises(IntegrityError):
        Source.objects.create(platform="whatsapp_group", external_id="1203630@g.us", title="Copy")
    # Sources without a chat id (manual, or not joined yet) never clash.
    Source.objects.create(platform="manual", title="Pasted A")
    Source.objects.create(platform="manual", title="Pasted B")


def test_a_student_is_a_member_once(group):
    student = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    SourceMember.objects.create(source=group, user=student)
    with transaction.atomic(), pytest.raises(IntegrityError):
        SourceMember.objects.create(source=group, user=student)
    assert list(group.members.values_list("user__email", flat=True)) == [student.email]


def test_a_message_is_stored_once_and_starts_untriaged(group):
    first = Message.objects.create(
        source=group,
        external_id="ABC123",
        sender_name="Dr Lee",
        text="Tomorrow's CDE2313 class has been moved from 10 AM to 2 PM.",
        sent_at=SENT,
    )
    assert first.triage == "pending"
    assert str(first) == "Dr Lee: Tomorrow's CDE2313 class has been moved from 10 AM…"

    with transaction.atomic(), pytest.raises(IntegrityError):
        Message.objects.create(source=group, external_id="ABC123", text="again", sent_at=SENT)

    # Replies point at the message they answer.
    reply = Message.objects.create(
        source=group, external_id="ABC124", text="Which room?", sent_at=SENT, reply_to=first
    )
    assert list(first.replies.all()) == [reply]


def test_deleting_a_source_deletes_its_messages_and_members(group):
    Message.objects.create(source=group, external_id="1", text="hi", sent_at=SENT)
    student = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    SourceMember.objects.create(source=group, user=student)

    group.delete()
    assert Message.objects.count() == 0
    assert SourceMember.objects.count() == 0
