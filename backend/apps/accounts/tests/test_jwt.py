import pytest
from rest_framework.test import APIClient

from apps.accounts.services import create_user

pytestmark = pytest.mark.django_db

LOGIN = "/api/v1/auth/jwt/create/"
REFRESH = "/api/v1/auth/jwt/refresh/"
LOGOUT = "/api/v1/auth/jwt/logout/"
VERIFY = "/api/v1/auth/jwt/verify/"
PROTECTED = "/api/v1/academics/schools/"  # any login-only endpoint
COOKIE = "uniflow_refresh"
EMAIL = "ali@student.aiu.edu.my"
PASSWORD = "Str0ng-pass-99"


@pytest.fixture
def student():
    return create_user(EMAIL, PASSWORD, full_name="Ali Hassan")  # active by default


@pytest.fixture
def client():
    return APIClient()  # keeps cookies between requests, like a browser


def login(client, email=EMAIL, password=PASSWORD):
    return client.post(LOGIN, {"email": email, "password": password}, format="json")


def test_login_returns_access_token_and_sets_httponly_refresh_cookie(client, student):
    response = login(client)

    assert response.status_code == 200
    assert set(response.json()) == {"access"}  # refresh token is NOT in the body
    cookie = response.cookies[COOKIE]
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/api/v1/auth/jwt/"


def test_access_token_opens_login_only_endpoints(client, student):
    access = login(client).json()["access"]

    assert client.get(PROTECTED).status_code == 401
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert client.get(PROTECTED).status_code == 200


def test_wrong_password_is_refused(client, student):
    response = login(client, password="wrong-password")

    assert response.status_code == 401
    assert COOKIE not in response.cookies


def test_account_must_be_activated_before_login(client, student):
    student.is_active = False  # has not clicked the activation email yet
    student.save()

    assert login(client).status_code == 401


def test_refresh_uses_the_cookie_and_rotates_it(client, student):
    login(client)
    old_cookie = client.cookies[COOKIE].value

    response = client.post(REFRESH)  # no body: the browser sends the cookie

    assert response.status_code == 200
    assert set(response.json()) == {"access"}
    assert response.cookies[COOKIE].value != old_cookie  # a new refresh token

    client.cookies[COOKIE] = old_cookie  # the old one must no longer work
    assert client.post(REFRESH).status_code == 401


def test_refresh_without_cookie_is_refused(client):
    assert client.post(REFRESH).status_code == 400


def test_logout_deletes_the_cookie_and_cancels_the_token(client, student):
    login(client)
    token = client.cookies[COOKIE].value

    response = client.post(LOGOUT)

    assert response.status_code == 204
    assert response.cookies[COOKIE].value == ""  # browser deletes it
    client.cookies[COOKIE] = token
    assert client.post(REFRESH).status_code == 401  # cancelled


def test_verify_checks_a_token(client, student):
    access = login(client).json()["access"]

    assert client.post(VERIFY, {"token": access}, format="json").status_code == 200
    assert client.post(VERIFY, {"token": "not-a-token"}, format="json").status_code == 401
