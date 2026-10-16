from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower

from core.models import TimeStampedModel

from . import semesters
from .managers import UserManager, normalize_email_address


class UserRole(models.TextChoices):
    STUDENT = "student", "Student"
    LECTURER = "lecturer", "Lecturer"
    SCHOOL_STAFF = "school_staff", "School staff"
    UNIVERSITY_ADMIN = "university_admin", "University admin"
    SUPER_ADMIN = "super_admin", "Super admin"


class Interest(models.TextChoices):
    """Subjects a student is interested in (used to rank opportunities and events)."""

    AI = "ai", "Artificial Intelligence"
    DATA_SCIENCE = "data_science", "Data Science"
    SOFTWARE_ENGINEERING = "software_engineering", "Software Engineering"
    CYBERSECURITY = "cybersecurity", "Cybersecurity"
    NETWORKING = "networking", "Networking"
    BUSINESS = "business", "Business"
    FINANCE = "finance", "Finance"
    EDUCATION = "education", "Education"
    PSYCHOLOGY = "psychology", "Psychology"
    ENTREPRENEURSHIP = "entrepreneurship", "Entrepreneurship"


class InfoType(models.TextChoices):
    """Kinds of information a student wants to receive. None chosen means "all"."""

    INTERNSHIP = "internship", "Internships"
    BOOTCAMP = "bootcamp", "Bootcamps"
    INDUSTRY_VISIT = "industry_visit", "Industry visits"
    COMPETITION = "competition", "Competitions"
    SCHOLARSHIP = "scholarship", "Scholarships"
    ACADEMIC_NOTICE = "academic_notice", "Academic notices"
    STUDENT_AFFAIRS = "student_affairs", "Student affairs updates"


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
            # One account per email whatever the capitals, on MySQL and PostgreSQL alike
            # (PostgreSQL compares text case-sensitively).
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_unique_ci"),
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

    @property
    def profile_complete(self) -> bool:
        """Students must choose their school, programme and intake before using UniFlow.

        Other roles have nothing to fill in, so they always count as complete.
        """
        if self.role != UserRole.STUDENT:
            return True
        profile = getattr(self, "student_profile", None)
        return bool(profile and profile.school_id and profile.programme_id and profile.intake_id)


class StudentProfile(TimeStampedModel):
    """Where a student belongs. Chosen during onboarding; used for audience targeting."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="student_profile"
    )
    student_number = models.CharField(max_length=32, unique=True, null=True, blank=True)
    school = models.ForeignKey("academics.School", on_delete=models.PROTECT, null=True, blank=True)
    programme = models.ForeignKey(
        "academics.Programme", on_delete=models.PROTECT, null=True, blank=True
    )
    intake = models.ForeignKey("academics.Intake", on_delete=models.PROTECT, null=True, blank=True)
    # Normally empty: the semester is worked out from the intake (see semesters.py).
    semester_override = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Set only if the worked-out semester is wrong."
    )
    interests = models.JSONField(default=list, blank=True, help_text="Interest values.")
    info_types = models.JSONField(
        default=list, blank=True, help_text="InfoType values. Empty means all."
    )
    aliases = models.CharField(
        max_length=200, blank=True, help_text="Nicknames, comma-separated (for name mentions)."
    )

    def __str__(self) -> str:
        return f"Student profile of {self.user}"

    @property
    def current_semester(self) -> int | None:
        """The override if set, otherwise worked out from the intake (None without one)."""
        if self.semester_override:
            return self.semester_override
        if self.intake_id is None:
            return None
        calendar = semesters.calendar_for(self.programme)
        return semesters.semester_for(self.intake.start_date, semesters.today(), calendar)

    def clean(self):
        super().clean()
        if self.programme_id and self.school_id and self.programme.school_id != self.school_id:
            raise ValidationError({"programme": "This programme does not belong to that school."})


class StaffProfile(TimeStampedModel):
    """Which school a staff member works for; decides what they may manage (M2)."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="staff_profile"
    )
    school = models.ForeignKey("academics.School", on_delete=models.PROTECT, null=True, blank=True)
    position_title = models.CharField(max_length=150, blank=True)

    def __str__(self) -> str:
        return f"Staff profile of {self.user}"
