"""Account API, mounted at /api/v1/auth/ — Djoser's own URLs.

users/                     register (POST), current user (users/me/)
users/activation/          activate with {uid, token} from the email
users/resend_activation/   send the activation email again
jwt/create/                log in -> {access, refresh}
jwt/refresh/               new access token from the refresh token
jwt/verify/                check that a token is still valid
"""

from django.urls import include, path

urlpatterns = [
    path("", include("djoser.urls")),
    path("", include("djoser.urls.jwt")),
]
