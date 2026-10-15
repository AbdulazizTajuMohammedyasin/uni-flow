"""Running online on Render behind Vercel's forwarding (M9.6b)."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from config.env import postgres_from_url

LOGIN = "/api/v1/auth/jwt/create/"
VERCEL = "76.76.21.21"  # what Django sees as the sender: Vercel, not the student


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
