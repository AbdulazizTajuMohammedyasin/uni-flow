import pytest
from rest_framework.test import APIClient

from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

LOGIN = "/api/v1/auth/jwt/create/"
REFRESH = "/api/v1/auth/jwt/refresh/"
VERIFY = "/api/v1/auth/jwt/verify/"
PROTECTED = "/api/v1/academics/schools/"  # any login-only endpoint
EMAIL = "ali@student.aiu.edu.my"
PASSWORD = "Str0ng-pass-99"


@pytest.fixture
def student():
    return create_user(EMAIL, PASSWORD, full_name="Ali Hassan")  # active by default


@pytest.fixture
def client():
    return APIClient()


def login(client, email=EMAIL, password=PASSWORD):
    return client.post(LOGIN, {"email": email, "password": password}, format="json")


def test_login_returns_access_and_refresh_tokens(client, student):
    response = login(client)

    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}


def test_access_token_opens_login_only_endpoints(client, student):
    access = login(client).json()["access"]

    assert client.get(PROTECTED).status_code == 401
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert client.get(PROTECTED).status_code == 200


def test_wrong_password_is_refused(client, student):
    response = login(client, password="wrong-password")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "no_active_account"


def test_account_must_be_activated_before_login(client, student):
    student.is_active = False  # has not clicked the activation email yet
    student.save()

    assert login(client).status_code == 401


def test_refresh_gives_new_tokens_and_old_refresh_token_stops_working(client, student):
    old_refresh = login(client).json()["refresh"]

    response = client.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert response.status_code == 200
    assert set(response.json()) == {"access", "refresh"}

    reused = client.post(REFRESH, {"refresh": old_refresh}, format="json")
    assert reused.status_code == 401


def test_verify_checks_a_token(client, student):
    access = login(client).json()["access"]

    assert client.post(VERIFY, {"token": access}, format="json").status_code == 200
    assert client.post(VERIFY, {"token": "not-a-token"}, format="json").status_code == 401
