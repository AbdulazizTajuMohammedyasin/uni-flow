"""Registration rules on top of Djoser's serializers."""

from django.conf import settings
from django.db import transaction
from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers

from .managers import normalize_email_address
from .services import create_user


class UserCreateSerializer(UserCreatePasswordRetypeSerializer):
    """POST /api/v1/auth/users/ — fields: email, full_name, password, re_password.

    Only emails from ALLOWED_EMAIL_DOMAINS (student.aiu.edu.my) may register.
    The account starts inactive until the student clicks the activation email.
    """

    def validate_email(self, value: str) -> str:
        email = normalize_email_address(value)
        domain = email.rsplit("@", 1)[-1]
        if domain not in settings.ALLOWED_EMAIL_DOMAINS:
            allowed = ", ".join(f"@{d}" for d in settings.ALLOWED_EMAIL_DOMAINS)
            raise serializers.ValidationError(f"Only {allowed} email addresses can register.")
        return email

    def perform_create(self, validated_data):
        # Same as Djoser's version, but through create_user() so the student gets a profile.
        with transaction.atomic():
            user = create_user(**validated_data)
            user.is_active = False  # becomes True when the activation link is used
            user.save(update_fields=["is_active"])
        return user
