from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.academics.models import School
from apps.accounts.services import create_user
from apps.audiences.models import Audience
from apps.publishing.selectors import published_q
from apps.publishing.services import archive, publish

from .models import SamplePost

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin():
    return create_user("ua@aiu.edu.my", "Str0ng-pass-99", full_name="UA", role="university_admin")


def make_post(**fields):
    fields.setdefault("publisher_type", "university")
    return SamplePost.objects.create(audience=Audience.objects.create(), **fields)


# --- Rules the database enforces --------------------------------------------------------


def test_school_post_must_name_its_school():
    school = School.objects.create(code="SCI", name="Computing")
    make_post(publisher_type="school", publisher_school=school)  # fine
    make_post(publisher_type="university")  # fine

    with transaction.atomic(), pytest.raises(IntegrityError):
        make_post(publisher_type="school")
    with transaction.atomic(), pytest.raises(IntegrityError):
        make_post(publisher_type="university", publisher_school=school)


def test_expiry_must_be_after_publishing():
    now = timezone.now()
    make_post(published_at=now, expires_at=now + timedelta(days=1))  # fine
    make_post(expires_at=now)  # fine: not published yet

    with transaction.atomic(), pytest.raises(IntegrityError):
        make_post(published_at=now, expires_at=now)


def test_new_posts_start_as_drafts():
    post = make_post()
    assert post.status == "draft"
    assert post.published_at is None


# --- publish / archive ----------------------------------------------------------------


def test_publish_sets_the_time_and_who(admin):
    post = publish(make_post(), admin)
    post.refresh_from_db()

    assert post.status == "published"
    assert abs(post.published_at - timezone.now()) < timedelta(seconds=5)
    assert post.updated_by == admin


def test_publishing_twice_keeps_the_first_time(admin):
    post = publish(make_post(), admin)
    first = post.published_at
    publish(post, admin)
    assert SamplePost.objects.get(pk=post.pk).published_at == first


def test_cannot_publish_with_an_expiry_in_the_past(admin):
    post = make_post(expires_at=timezone.now() - timedelta(minutes=1))
    with pytest.raises(ValidationError):
        publish(post, admin)
    assert SamplePost.objects.get(pk=post.pk).status == "draft"


def test_archive_and_publish_again(admin):
    post = publish(make_post(), admin)
    archive(post, admin)
    assert SamplePost.objects.get(pk=post.pk).status == "archived"

    publish(post, admin)
    assert SamplePost.objects.get(pk=post.pk).status == "published"


# --- "live right now" -----------------------------------------------------------------


def test_published_q_expiry_boundaries():
    now = timezone.now()
    past = now - timedelta(days=2)
    live = make_post(status="published", published_at=past)
    live_until_later = make_post(
        status="published", published_at=past, expires_at=now + timedelta(seconds=1)
    )
    expired = make_post(status="published", published_at=past, expires_at=now)  # at the limit
    make_post(status="draft")
    make_post(status="archived", published_at=past)

    visible = set(SamplePost.objects.filter(published_q(now)))

    assert visible == {live, live_until_later}
    assert expired.is_expired is True
    assert live.is_expired is False
