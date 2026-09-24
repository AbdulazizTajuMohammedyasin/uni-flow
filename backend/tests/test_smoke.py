"""Smoke tests: the test settings load and the MySQL test database is usable."""

import pytest
from django.conf import settings
from django.db import connection


def test_uses_test_settings():
    assert settings.SETTINGS_MODULE == "config.settings.test"
    assert settings.DEBUG is False


def test_uses_mysql_with_utf8mb4():
    assert connection.vendor == "mysql"
    assert settings.DATABASES["default"]["OPTIONS"]["charset"] == "utf8mb4"


@pytest.mark.django_db
def test_database_query_runs_on_test_database():
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE(), @@character_set_database")
        database_name, charset = cursor.fetchone()

    assert database_name == "test_uniflow"
    assert charset == "utf8mb4"
