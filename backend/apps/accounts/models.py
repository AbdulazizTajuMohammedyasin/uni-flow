from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager, normalize_email_address


class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    LECTURER = "lecturer", "Lecturer"
    SCHOOL_STAFF = "school_staff", "School staff"
    UNIVERSITY_ADMIN = "university_admin", "University admin"
    SUPER_ADMIN = "super_admin", "Super admin"


class User(AbstractUser):
    """UniFlow user: signs in with email, has exactly one role.

    - `is_active` means "email verified" (Djoser sets it on activation, from M1.5).
    - `is_suspended` blocks an account and is kept separate from `is_active`,
      so a blocked user cannot reactivate themselves through the resend-activation flow.
    - `is_staff` only gates the Django admin back-office (super admins).
      React staff-dashboard access comes from capabilities (M2.1), not from `is_staff`.
    """

    Role = UserRole

    # Replace username/first/last name with email + a single full name.
    username = None
    first_name = None
    last_name = None

    email = models.EmailField("email address", unique=True)
    full_name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=32, choices=UserRole, default=UserRole.STUDENT, db_index=True
    )
    is_suspended = models.BooleanField(
        default=False,
        help_text="Blocks sign-in without affecting email verification (is_active).",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=UserRole.values),
                name="accounts_user_role_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.email

    def clean(self):
        super().clean()
        self.email = normalize_email_address(self.email)

    def get_full_name(self) -> str:
        return self.full_name

    def get_short_name(self) -> str:
        return self.full_name.split(" ", 1)[0] if self.full_name else self.email
