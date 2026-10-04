from datetime import UTC, datetime, timedelta

import pytest
from django.conf import settings
from django.core.files.base import ContentFile

from apps.accounts.services import create_user
from apps.intelligence import tasks
from apps.intelligence.models import Message, MessageFile, Source
from apps.intelligence.services import clear_old_messages

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 10, 4, 3, 0, tzinfo=UTC)
OLD = NOW - timedelta(days=61)
RECENT = NOW - timedelta(days=59)


@pytest.fixture(autouse=True)
def private_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def group():
    return Source.objects.create(platform="manual", title="CDE2313 Sec A")


def message(group, sent_at, text="Class moved to 2 PM.", external_id=None):
    return Message.objects.create(
        source=group,
        external_id=external_id or str(sent_at),
        sender_name="Dr Lee",
        text=text,
        raw={"id": "x"},
        sent_at=sent_at,
    )


def stored_file(message=None, user=None, created_at=NOW):
    item = MessageFile(
        message=message, uploaded_by=user, kind="pdf", mime_type="application/pdf", size_bytes=4
    )
    item.file.save("file.pdf", ContentFile(b"%PDF"), save=False)
    item.save()
    MessageFile.objects.filter(pk=item.pk).update(created_at=created_at)
    item.refresh_from_db()
    return item


def test_old_message_text_is_cleared_but_the_message_stays(group):
    old = message(group, OLD)
    recent = message(group, RECENT, text="Room B2")

    assert clear_old_messages(NOW) == {"messages_cleared": 1, "files_deleted": 0}

    old.refresh_from_db()
    assert (old.text, old.raw, old.text_deleted_at) == ("", {}, NOW)
    assert (old.sender_name, old.sent_at) == ("Dr Lee", OLD)  # who and when stay
    recent.refresh_from_db()
    assert recent.text == "Room B2"
    assert recent.text_deleted_at is None


def test_old_files_are_deleted_from_the_disk(group):
    student = create_user("ali@student.aiu.edu.my", "Str0ng-pass-99", full_name="Ali")
    from_old_message = stored_file(message=message(group, OLD))
    old_upload = stored_file(user=student, created_at=OLD)
    recent_upload = stored_file(user=student, created_at=RECENT)
    old_path = settings.MEDIA_ROOT / from_old_message.file.name

    result = clear_old_messages(NOW)

    assert result["files_deleted"] == 2
    assert not old_path.exists()
    for item in (from_old_message, old_upload):
        item.refresh_from_db()
        assert item.file.name == ""
        assert item.file_deleted_at == NOW
    recent_upload.refresh_from_db()
    assert recent_upload.file_deleted_at is None
    assert (settings.MEDIA_ROOT / recent_upload.file.name).exists()


def test_running_twice_changes_nothing_more(group):
    message(group, OLD)
    clear_old_messages(NOW)
    assert clear_old_messages(NOW) == {"messages_cleared": 0, "files_deleted": 0}


def test_the_retention_period_is_a_setting(group, settings):
    settings.MESSAGE_RETENTION_DAYS = 30
    message(group, NOW - timedelta(days=31))
    assert clear_old_messages(NOW)["messages_cleared"] == 1


def test_the_daily_job_runs_the_clean_up(group):
    message(group, datetime(2020, 1, 1, tzinfo=UTC))
    assert tasks.clear_old_messages.delay().get() == {"messages_cleared": 1, "files_deleted": 0}
    schedule = settings.CELERY_BEAT_SCHEDULE["clear-old-messages"]
    assert schedule["task"] == "apps.intelligence.tasks.clear_old_messages"
