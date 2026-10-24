"""Online email: Brevo's HTTPS API (Render's free plan blocks SMTP). See docs/deployment.md."""

import json
from unittest import mock

import pytest
import requests
from django.test import override_settings
from rest_framework.test import APIClient

from core.tests.test_inngest import SIGNING_KEY, start_production

BREVO = {
    "EMAIL_BACKEND": "anymail.backends.brevo.EmailBackend",
    "ANYMAIL": {"BREVO_API_KEY": "test-brevo-key"},
    "DEFAULT_FROM_EMAIL": "UniFlow <uniflow.team@example.com>",
}


def brevo_accepts(*args, **kwargs):
    response = requests.Response()
    response.status_code = 201
    response._content = b'{"messageId": "<test@smtp-relay.brevo.com>"}'
    return response


@pytest.mark.django_db
@override_settings(**BREVO)
def test_registration_email_is_sent_through_brevo():
    with mock.patch("requests.Session.request", side_effect=brevo_accepts) as send:
        response = APIClient().post(
            "/api/v1/auth/users/",
            {
                "email": "ali.hassan@student.aiu.edu.my",
                "full_name": "Ali Hassan",
                "password": "Str0ng-pass-99",
                "re_password": "Str0ng-pass-99",
            },
            format="json",
        )

    assert response.status_code == 201
    assert send.call_count == 1
    request = send.call_args.kwargs
    assert (request["method"], request["url"]) == ("POST", "https://api.brevo.com/v3/smtp/email")
    assert request["headers"]["api-key"] == "test-brevo-key"
    payload = json.loads(request["data"])
    assert payload["to"] == [{"email": "ali.hassan@student.aiu.edu.my"}]
    assert payload["sender"] == {"email": "uniflow.team@example.com", "name": "UniFlow"}
    assert "http://localhost:5173/verify-email/" in payload["textContent"]


def test_online_with_brevo_the_site_refuses_to_start_without_its_key():
    keys = {"INNGEST_SIGNING_KEY": SIGNING_KEY, "INNGEST_EVENT_KEY": "event-key"}
    brevo = {"EMAIL_BACKEND": BREVO["EMAIL_BACKEND"], "BREVO_API_KEY": ""}

    missing = start_production(**keys, **brevo)
    assert missing.returncode != 0
    assert "Missing required environment variable: BREVO_API_KEY" in missing.stderr

    ready = start_production(**keys, **brevo | {"BREVO_API_KEY": "brevo-key"})
    assert ready.returncode == 0, ready.stderr
