"""Account actions. Always create users through `create_user` so they get a profile."""

from django.db import transaction
from djoser.email import PasswordResetEmail

from .models import StaffProfile, StudentProfile, User, UserRole

# Roles a super admin can give in the staff area (students register themselves).
STAFF_ROLES = [
    UserRole.LECTURER,
    UserRole.SCHOOL_STAFF,
    UserRole.UNIVERSITY_ADMIN,
    UserRole.SUPER_ADMIN,
]


@transaction.atomic
def create_user(email: str, password: str | None = None, **fields) -> User:
    """Create a user plus the matching profile (students get a StudentProfile,
    every other role gets a StaffProfile)."""
    user = User.objects.create_user(email, password, **fields)
    if user.role == UserRole.STUDENT:
        StudentProfile.objects.create(user=user)
    else:
        StaffProfile.objects.create(user=user)
    return user


def sync_admin_flags(user: User) -> None:
    """Only super admins may open the Django admin back-office."""
    is_super = user.role == UserRole.SUPER_ADMIN
    user.is_staff = is_super
    user.is_superuser = is_super


@transaction.atomic
def create_staff_user(*, email, full_name, role, school=None, position_title="", request=None):
    """A super admin creates a staff account; the person gets a "set your password" email.

    The account is active straight away (an admin vouched for it) but has no usable
    password until the person follows the link.
    """
    user = create_user(email, None, full_name=full_name, role=role)
    sync_admin_flags(user)
    user.save(update_fields=["is_staff", "is_superuser"])
    user.staff_profile.school = school
    user.staff_profile.position_title = position_title
    user.staff_profile.save()
    PasswordResetEmail(request, {"user": user}).send([user.email])
    return user


@transaction.atomic
def update_staff_details(user: User, **changes) -> User:
    """Change name / role / suspension / school / position from the staff area."""
    for field in ("full_name", "role", "is_suspended"):
        if field in changes:
            setattr(user, field, changes[field])
    sync_admin_flags(user)
    user.save()
    profile, _ = StaffProfile.objects.get_or_create(user=user)
    for field in ("school", "position_title"):
        if field in changes:
            setattr(profile, field, changes[field])
    profile.save()
    user.staff_profile = profile  # so the response shows the saved values
    return user
