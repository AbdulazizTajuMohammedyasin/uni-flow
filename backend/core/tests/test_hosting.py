"""Running online on Render behind Vercel's forwarding (M9.6b), with files in Supabase (M9.6h)."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle
from storages.backends.s3 import S3Storage

from config.env import postgres_from_url, s3_storage_from_env

LOGIN = "/api/v1/auth/jwt/create/"
VERCEL = "76.76.21.21"  # what Django sees as the sender: Vercel, not the student
SUPABASE = "https://abcdefgh.storage.supabase.co/storage/v1/s3"


def test_render_database_address_becomes_postgresql_settings():
    settings = postgres_from_url(
        "postgresql://uniflow_user:p%40ss%2Fword@dpg-abc123-a.oregon-postgres.render.com:5432/uniflow?sslmode=require"
    )
    assert settings == {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "uniflow",
        "USER": "uniflow_user",
        "PASSWORD": "p@ss/word",  # special characters in the password are decoded
        "HOST": "dpg-abc123-a.oregon-postgres.render.com",
        "PORT": "5432",
        "OPTIONS": {"sslmode": "require"},
        "TEST": {"NAME": "test_uniflow"},
    }
    assert postgres_from_url("postgres://u:p@internal-host/db")["PORT"] == "5432"


@pytest.mark.parametrize("url", ["mysql://u:p@host/db", "postgresql://u:p@host/", "not an address"])
def test_wrong_database_addresses_are_refused(url):
    with pytest.raises(ImproperlyConfigured):
        postgres_from_url(url)


def test_files_stay_on_the_disk_without_a_bucket(monkeypatch):
    monkeypatch.delenv("S3_BUCKET", raising=False)
    assert s3_storage_from_env() is None


def test_files_go_to_a_private_supabase_bucket(monkeypatch):
    for name, value in {
        "S3_BUCKET": "uniflow-files",
        "S3_ENDPOINT_URL": SUPABASE,
        "S3_REGION": "ap-southeast-1",
        "S3_ACCESS_KEY_ID": "test-key-id",
        "S3_SECRET_ACCESS_KEY": "test-secret",
    }.items():
        monkeypatch.setenv(name, value)

    settings = s3_storage_from_env()
    assert settings["BACKEND"] == "storages.backends.s3.S3Storage"
    storage = S3Storage(**settings["OPTIONS"])  # nothing is sent to Supabase here
    assert storage.default_acl is None  # no public files
    assert storage.file_overwrite is False

    # Supabase's address style: <endpoint>/<bucket>/<file>, and any link is signed.
    link = storage.url("message_files/2026/10/abc.png")
    assert link.startswith(f"{SUPABASE}/uniflow-files/message_files/2026/10/abc.png?")
    assert "X-Amz-Signature=" in link


def test_a_bucket_without_its_keys_is_refused(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "uniflow-files")
    for name in ("S3_ENDPOINT_URL", "S3_REGION", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ImproperlyConfigured):
        s3_storage_from_env()


@pytest.mark.django_db
def test_api_answers_are_never_cached():
    response = APIClient().get("/api/v1/health/")
    assert response["Cache-Control"] == "private, no-store"


@pytest.mark.django_db
def test_other_pages_keep_their_own_caching():
    response = APIClient().get("/django-admin/login/")
    assert response["Cache-Control"] != "private, no-store"


@pytest.mark.django_db
def test_login_limits_are_per_student_through_vercel(monkeypatch):
    """Through Vercel every request comes from Vercel's address; X-Forwarded-For still names
    the student first, so one student's failed logins never block everyone else."""
    # DRF reads its limits once at startup: lower the login limit to 3 for this test.
    monkeypatch.setattr(
        ScopedRateThrottle,
        "THROTTLE_RATES",
        {"anon": "100/min", "user": "300/min", "auth": "3/min"},
    )

    def login(student_ip):
        return APIClient().post(
            LOGIN,
            {"email": "ali@student.aiu.edu.my", "password": "wrong"},
            format="json",
            REMOTE_ADDR=VERCEL,
            HTTP_X_FORWARDED_FOR=f"{student_ip}, {VERCEL}",
        )

    for _ in range(3):
        assert login("1.1.1.1").status_code == 401
    assert login("1.1.1.1").status_code == 429  # this student is slowed down…
    assert login("2.2.2.2").status_code == 401  # …but another student can still log in
