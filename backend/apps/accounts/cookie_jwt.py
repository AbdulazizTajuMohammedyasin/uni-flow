"""Login tokens for the website: the refresh token lives in a secure httpOnly cookie.

Page scripts can never read that cookie, so it cannot be stolen by injected JavaScript.
The access token is returned in the body and kept only in the website's memory.
These are SimpleJWT's own views with the refresh token moved from the body to a cookie.
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

COOKIE_NAME = "uniflow_refresh"
COOKIE_PATH = "/api/v1/auth/jwt/"  # the browser only sends it to the login/refresh/logout URLs


def move_refresh_token_to_cookie(response):
    refresh = response.data.pop("refresh", None)
    if refresh:
        response.set_cookie(
            COOKIE_NAME,
            refresh,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            httponly=True,  # invisible to page scripts
            secure=not settings.DEBUG,  # HTTPS-only outside local development
            samesite="Lax",  # not sent by other websites' forms or scripts
            path=COOKIE_PATH,
        )
    return response


class CookieLoginView(TokenObtainPairView):
    """POST {email, password} -> {access}; the refresh token is set as a cookie."""

    def post(self, request, *args, **kwargs):
        return move_refresh_token_to_cookie(super().post(request, *args, **kwargs))


class CookieRefreshView(TokenRefreshView):
    """POST (no body needed) -> {access}; reads and rotates the refresh-token cookie."""

    def get_serializer(self, *args, **kwargs):
        data = kwargs.get("data")
        if data is not None and "refresh" not in data and COOKIE_NAME in self.request.COOKIES:
            kwargs["data"] = {"refresh": self.request.COOKIES[COOKIE_NAME]}
        return super().get_serializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        return move_refresh_token_to_cookie(super().post(request, *args, **kwargs))


@extend_schema(request=None, responses={204: None})
class LogoutView(APIView):
    """POST -> cancels the refresh token and deletes the cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.COOKIES.get(COOKIE_NAME)
        if token:
            try:
                RefreshToken(token).blacklist()
            except TokenError:
                pass  # already expired or invalid
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH, samesite="Lax")
        return response
