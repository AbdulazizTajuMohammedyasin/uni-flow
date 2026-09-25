"""Fixtures shared by every backend test."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache():
    """Throttle counters live in the cache; start every test with a clean slate."""
    cache.clear()
    yield
    cache.clear()
