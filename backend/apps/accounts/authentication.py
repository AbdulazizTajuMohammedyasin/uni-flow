"""Blocks suspended accounts (the one rule SimpleJWT cannot know on its own)."""

from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


def can_log_in(user) -> bool:
    """SimpleJWT USER_AUTHENTICATION_RULE: who may get or refresh tokens."""
    return user is not None and user.is_active and not user.is_suspended


class ActiveUserJWTAuthentication(JWTAuthentication):
    """SimpleJWT's normal check, plus: a suspended user's tokens stop working at once."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.is_suspended:
            raise AuthenticationFailed("This account is suspended.", code="account_suspended")
        return user


class ActiveUserJWTScheme(SimpleJWTScheme):
    """Tells the API docs this works like SimpleJWT (keeps the Swagger "Authorize" button)."""

    target_class = "apps.accounts.authentication.ActiveUserJWTAuthentication"
