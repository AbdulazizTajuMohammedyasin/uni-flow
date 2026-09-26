"""Account actions. Always create users through `create_user` so they get a profile."""

from django.db import transaction

from .models import StaffProfile, StudentProfile, User, UserRole


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
