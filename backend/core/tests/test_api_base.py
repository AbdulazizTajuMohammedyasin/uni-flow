"""Tests for the /api/v1/ foundation: health, error format, pagination, CORS, OpenAPI."""

from unittest import mock

import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.management import call_command
from django.db import OperationalError
from django.http import Http404
from django.test import override_settings
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.test import APIClient, APIRequestFactory

from core.exceptions import api_exception_handler
from core.pagination import StandardPagination


@pytest.fixture
def client():
    return APIClient()


# --- Health ---------------------------------------------------------------


@pytest.mark.django_db
def test_health_is_public_and_reports_database_ok(client):
    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_reports_503_when_database_is_unreachable(client):
    with mock.patch("core.views.connection.cursor", side_effect=OperationalError("down")):
        response = client.get("/api/v1/health/")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": "unavailable"}


# --- Error format -----------------------------------------------------------


def test_unknown_api_path_returns_json_404_in_error_format(client):
    response = client.get("/api/v1/does-not-exist/")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "This API endpoint does not exist.",
            "fields": {},
        }
    }


def test_validation_error_with_fields():
    exc = exceptions.ValidationError({"title": ["This field is required."]})
    response = api_exception_handler(exc, {})

    assert response.status_code == 400
    assert response.data == {
        "error": {
            "code": "validation_error",
            "message": "Invalid input.",
            "fields": {"title": ["This field is required."]},
        }
    }


def test_validation_error_without_field_goes_to_non_field_errors():
    response = api_exception_handler(exceptions.ValidationError("Dates overlap."), {})

    assert response.data["error"]["fields"] == {"non_field_errors": ["Dates overlap."]}


@pytest.mark.parametrize(
    ("exc", "status_code", "code"),
    [
        (exceptions.NotAuthenticated(), 401, "not_authenticated"),
        (exceptions.PermissionDenied(), 403, "permission_denied"),
        (DjangoPermissionDenied(), 403, "permission_denied"),
        (Http404(), 404, "not_found"),
        (exceptions.Throttled(wait=30), 429, "throttled"),
    ],
)
def test_other_errors_use_the_same_format(exc, status_code, code):
    response = api_exception_handler(exc, {})

    assert response.status_code == status_code
    assert set(response.data["error"]) == {"code", "message", "fields"}
    assert response.data["error"]["code"] == code
    assert response.data["error"]["fields"] == {}
    assert response.data["error"]["message"]


def test_unexpected_exceptions_are_left_to_django():
    assert api_exception_handler(RuntimeError("bug"), {}) is None


# --- Pagination ----------------------------------------------------------


def _paginate(query: str):
    request = Request(APIRequestFactory().get(f"/items/{query}"))
    paginator = StandardPagination()
    page = paginator.paginate_queryset(list(range(250)), request)
    return page, paginator.get_paginated_response(page).data


def test_pagination_defaults_to_20_items():
    page, data = _paginate("")

    assert len(page) == 20
    assert data["count"] == 250
    assert set(data) == {"count", "next", "previous", "results"}


def test_pagination_page_size_is_capped_at_100():
    page, _ = _paginate("?page_size=500")
    assert len(page) == 100


# --- CORS ----------------------------------------------------------------


@override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:5173"])
def test_cors_preflight_allows_the_frontend_origin(client):
    response = client.options(
        "/api/v1/health/",
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="x-client",
    )

    assert response["access-control-allow-origin"] == "http://localhost:5173"
    assert response["access-control-allow-credentials"] == "true"
    assert "x-client" in response["access-control-allow-headers"]


@override_settings(CORS_ALLOWED_ORIGINS=["http://localhost:5173"])
def test_cors_rejects_unknown_origins(client):
    response = client.options(
        "/api/v1/health/",
        HTTP_ORIGIN="https://evil.example",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
    )

    assert "access-control-allow-origin" not in response


# --- OpenAPI ---------------------------------------------------------------


def test_openapi_schema_generates_without_warnings(tmp_path):
    call_command(
        "spectacular", "--validate", "--fail-on-warn", "--file", str(tmp_path / "schema.yml")
    )
    assert "/api/v1/health/" in (tmp_path / "schema.yml").read_text(encoding="utf-8")
