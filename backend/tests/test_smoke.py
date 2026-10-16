"""Smoke tests: the test settings load and the test database is usable.

CI runs every test on MySQL (on your computer) and on PostgreSQL (online, Render).
"""

import pytest
from django.conf import settings
from django.db import connection

mysql_only = pytest.mark.skipif(connection.vendor != "mysql", reason="MySQL settings")
postgresql_only = pytest.mark.skipif(
    connection.vendor != "postgresql", reason="PostgreSQL settings"
)


def test_uses_test_settings():
    assert settings.SETTINGS_MODULE == "config.settings.test"
    assert settings.DEBUG is False


@mysql_only
def test_uses_mysql_with_utf8mb4():
    assert settings.DATABASES["default"]["OPTIONS"]["charset"] == "utf8mb4"


@mysql_only
@pytest.mark.django_db
def test_database_query_runs_on_test_database():
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE(), @@character_set_database")
        database_name, charset = cursor.fetchone()

    assert database_name == "test_uniflow"
    assert charset == "utf8mb4"


@postgresql_only
@pytest.mark.django_db
def test_postgresql_query_runs_on_test_database():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT datname, pg_encoding_to_char(encoding) FROM pg_database"
            " WHERE datname = current_database()"
        )
        database_name, charset = cursor.fetchone()

    assert database_name == "test_uniflow"
    assert charset == "UTF8"
