"""Fixtures shared by every backend test."""

import pytest
from django.core.cache import cache
from django.db import connection

from apps.publishing.tests.models import SamplePost


@pytest.fixture(autouse=True)
def _clear_cache():
    """Throttle counters live in the cache; start every test with a clean slate."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(scope="session", autouse=True)
def _sample_post_table(django_db_setup, django_db_blocker):
    """Create the test-only SamplePost table (see apps/publishing/tests/models.py)."""
    with django_db_blocker.unblock():
        with connection.schema_editor() as editor:
            editor.create_model(SamplePost)
        yield
        with connection.schema_editor() as editor:
            editor.delete_model(SamplePost)
