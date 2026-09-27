"""Account API, mounted at /api/v1/auth/ — Djoser's own URLs.

users/                     register (POST), current user (users/me/)
users/activation/          activate with {uid, token} from the email
users/resend_activation/   send the activation email again
jwt/create/                log in -> {access} + refresh-token cookie
jwt/refresh/               new access token from the refresh-token cookie
jwt/logout/                cancel the refresh token and delete the cookie
jwt/verify/                check that a token is still valid
"""

from django.urls import include, path

from .cookie_jwt import CookieLoginView, CookieRefreshView, LogoutView

urlpatterns = [
    # Login/refresh keep the refresh token in an httpOnly cookie (listed first so they
    # replace Djoser's jwt/create/ and jwt/refresh/).
    path("jwt/create/", CookieLoginView.as_view(), name="jwt-create"),
    path("jwt/refresh/", CookieRefreshView.as_view(), name="jwt-refresh"),
    path("jwt/logout/", LogoutView.as_view(), name="jwt-logout"),
    path("", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
]
