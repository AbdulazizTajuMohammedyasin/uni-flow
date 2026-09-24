import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_auth_user_model_is_the_custom_user():
    assert get_user_model() is User
    assert User.USERNAME_FIELD == "email"
    assert not hasattr(User, "username") or User.username is None


def test_create_user_defaults():
    user = User.objects.create_user(
        "Student@Student.AIU.edu.my", "s3cure-pass!", full_name="Ali Hassan"
    )

    assert user.email == "student@student.aiu.edu.my"  # whole address lowercased
    assert user.check_password("s3cure-pass!")
    assert user.role == User.Role.STUDENT
    assert user.is_active is True
    assert user.is_suspended is False
    assert user.is_staff is False
    assert user.is_superuser is False
    assert str(user) == "student@student.aiu.edu.my"
    assert user.get_full_name() == "Ali Hassan"
    assert user.get_short_name() == "Ali"


def test_create_user_requires_email():
    with pytest.raises(ValueError, match="email"):
        User.objects.create_user("", "pass", full_name="No Email")


def test_create_user_without_password_is_unusable():
    user = User.objects.create_user("nopass@example.com", full_name="No Password")
    assert user.has_usable_password() is False


def test_email_is_unique_case_insensitively():
    User.objects.create_user("dup@example.com", "pass", full_name="First")

    # Bypass the manager's lowercasing: the database itself must reject a case variant
    # (MySQL utf8mb4_0900_ai_ci is case-insensitive).
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(email="DUP@example.com", full_name="Second")


def test_role_check_constraint_rejects_unknown_role():
    user = User.objects.create_user("role@example.com", "pass", full_name="Role Test")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=user.pk).update(role="not_a_role")


def test_create_superuser():
    admin = User.objects.create_superuser(
        "Admin@Example.com", "adm1n-pass!", full_name="Site Admin"
    )

    assert admin.email == "admin@example.com"
    assert admin.role == User.Role.SUPER_ADMIN
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.is_active is True


@pytest.mark.parametrize(
    "overrides",
    [{"is_staff": False}, {"is_superuser": False}, {"role": User.Role.STUDENT}],
)
def test_create_superuser_rejects_inconsistent_flags(overrides):
    with pytest.raises(ValueError):
        User.objects.create_superuser("bad@example.com", "pass", full_name="Bad", **overrides)


def test_clean_lowercases_email():
    user = User(email="  Mixed@Example.COM ", full_name="Clean Test")
    user.clean()
    assert user.email == "mixed@example.com"
