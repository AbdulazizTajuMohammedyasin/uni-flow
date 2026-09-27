"""Account serializers used by Djoser: registration rules and the "my profile" (users/me/) shape."""

from django.conf import settings
from django.db import transaction
from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers

from apps.academics.models import Intake, Programme, School

from .capabilities import capabilities_for, publishers_for
from .managers import normalize_email_address
from .models import StaffProfile, StudentProfile, User, UserRole
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


class StudentProfileSerializer(serializers.ModelSerializer):
    # Only active schools, programmes and intakes can be chosen.
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True), allow_null=True, required=False
    )
    programme = serializers.PrimaryKeyRelatedField(
        queryset=Programme.objects.filter(is_active=True), allow_null=True, required=False
    )
    intake = serializers.PrimaryKeyRelatedField(
        queryset=Intake.objects.filter(is_active=True), allow_null=True, required=False
    )

    class Meta:
        model = StudentProfile
        fields = ["student_number", "school", "programme", "intake"]

    def validate(self, attrs):
        # Combine the new values with the current ones (PATCH may send only some fields).
        current = self.instance
        school = attrs.get("school", current.school if current else None)
        programme = attrs.get("programme", current.programme if current else None)
        if school and programme and programme.school_id != school.id:
            raise serializers.ValidationError(
                {"programme": "This programme does not belong to the chosen school."}
            )
        return attrs


class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffProfile
        fields = ["school", "position_title"]
        read_only_fields = fields


class MeSerializer(serializers.ModelSerializer):
    """GET/PATCH /api/v1/auth/users/me/ — the logged-in user's own details.

    Students may update their name and student profile; email and role are read-only.
    """

    profile_complete = serializers.BooleanField(read_only=True)
    student_profile = StudentProfileSerializer(required=False)
    staff_profile = StaffProfileSerializer(read_only=True)
    # What the website may show this user (the API checks again on every action).
    capabilities = serializers.SerializerMethodField()
    publishers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "profile_complete",
            "student_profile",
            "staff_profile",
            "capabilities",
            "publishers",
        ]
        read_only_fields = ["id", "email", "role"]

    def get_capabilities(self, user) -> dict[str, bool]:
        return capabilities_for(user)

    def get_publishers(self, user) -> list[dict]:
        return publishers_for(user)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Let the nested profile compare against the saved profile (for the
        # student_number uniqueness check and partial updates).
        user = self.instance if isinstance(self.instance, User) else None
        profile = getattr(user, "student_profile", None) if user else None
        self.fields["student_profile"].instance = profile

    def validate_student_profile(self, value):
        if self.instance and self.instance.role != UserRole.STUDENT:
            raise serializers.ValidationError("Only students have a student profile.")
        return value

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("student_profile", None)
        instance = super().update(instance, validated_data)  # full_name
        if profile_data is not None:
            profile, _ = StudentProfile.objects.get_or_create(user=instance)
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()
            instance.student_profile = profile
        return instance
