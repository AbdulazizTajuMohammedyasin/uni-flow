"""Account serializers used by Djoser: registration rules and the "my profile" (users/me/) shape."""

from django.conf import settings
from django.db import transaction
from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import serializers

from apps.academics.models import Intake, Programme, School

from .capabilities import capabilities_for, publishers_for
from .managers import normalize_email_address
from .models import InfoType, Interest, StaffProfile, StudentProfile, User, UserRole
from .services import STAFF_ROLES, create_staff_user, create_user, update_staff_details


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
    # Worked out from the intake unless the student sets semester_override.
    current_semester = serializers.IntegerField(read_only=True)
    semester_override = serializers.IntegerField(
        min_value=1, max_value=15, allow_null=True, required=False
    )
    interests = serializers.ListField(
        child=serializers.ChoiceField(choices=Interest.choices), required=False
    )
    info_types = serializers.ListField(
        child=serializers.ChoiceField(choices=InfoType.choices), required=False
    )

    class Meta:
        model = StudentProfile
        fields = [
            "student_number",
            "school",
            "programme",
            "intake",
            "current_semester",
            "semester_override",
            "interests",
            "info_types",
            "aliases",
        ]

    def validate_interests(self, value):
        return list(dict.fromkeys(value))  # drop repeats, keep order

    def validate_info_types(self, value):
        return list(dict.fromkeys(value))

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


# --- Staff area: user management (super admins, /api/v1/manage/users/) ----------------

STAFF_ROLE_CHOICES = [(role.value, role.label) for role in STAFF_ROLES]


class ManagedUserSerializer(serializers.ModelSerializer):
    """How a user is shown in the staff area."""

    school = serializers.SerializerMethodField()
    position_title = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "school",
            "position_title",
            "is_active",
            "is_suspended",
            "date_joined",
            "last_login",
        ]

    def get_school(self, user) -> int | None:
        profile = getattr(user, "staff_profile", None)
        return profile.school_id if profile else None

    def get_position_title(self, user) -> str:
        profile = getattr(user, "staff_profile", None)
        return profile.position_title if profile else ""


class StaffDetailsSerializer(serializers.Serializer):
    """Shared checks: staff roles only, and school staff must belong to a school."""

    role = serializers.ChoiceField(choices=STAFF_ROLE_CHOICES)
    school = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.filter(is_active=True), allow_null=True, required=False
    )
    position_title = serializers.CharField(max_length=150, allow_blank=True, required=False)

    def validate(self, attrs):
        profile = getattr(self.instance, "staff_profile", None)
        role = attrs.get("role", getattr(self.instance, "role", None))
        school = attrs.get("school", profile.school if profile else None)
        if role == UserRole.SCHOOL_STAFF and school is None:
            raise serializers.ValidationError({"school": "School staff must belong to a school."})
        return attrs


class CreateStaffUserSerializer(StaffDetailsSerializer):
    """POST /api/v1/manage/users/ — creates a staff account and emails a password link."""

    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=150)

    def validate_email(self, value):
        email = normalize_email_address(value)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def create(self, validated_data):
        return create_staff_user(request=self.context.get("request"), **validated_data)


class UpdateStaffUserSerializer(StaffDetailsSerializer):
    """PATCH /api/v1/manage/users/{id}/ — change name, role, school, position, suspension."""

    full_name = serializers.CharField(max_length=150, required=False)
    role = serializers.ChoiceField(choices=STAFF_ROLE_CHOICES, required=False)
    is_suspended = serializers.BooleanField(required=False)

    def validate(self, attrs):
        request = self.context.get("request")
        if request is not None and request.user.pk == self.instance.pk:
            if "role" in attrs or attrs.get("is_suspended"):
                raise serializers.ValidationError(
                    "You cannot change your own role or suspend yourself."
                )
        if self.instance.role == UserRole.STUDENT and "role" in attrs:
            raise serializers.ValidationError({"role": "A student's role is not changed here."})
        return super().validate(attrs)

    def update(self, instance, validated_data):
        return update_staff_details(instance, **validated_data)
