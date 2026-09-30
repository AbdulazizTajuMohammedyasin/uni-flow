"""The school boundary: which posts a staff member may manage (docs/06-auth-and-permissions.md).

- University admins and super admins: everything.
- School staff: only posts from their own school, sent to their own school's students.
- Everyone else (lecturers, students): nothing.

Views check the capability first (HasCapability); these functions decide *which* posts.
"""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from apps.accounts.capabilities import ADMIN_ROLES, publishers_for, staff_school_id
from apps.accounts.models import UserRole

__all__ = [
    "CanManageObject",
    "can_manage",
    "manageable_queryset",
    "publishers_for",  # from M2.1 (apps/accounts/capabilities.py)
    "validate_audience",
    "validate_publisher",
]


def _own_school_id(user) -> int | None:
    """The school a school-staff member works for (None for every other role)."""
    if user.is_authenticated and user.role == UserRole.SCHOOL_STAFF:
        return staff_school_id(user)
    return None


def _is_admin(user) -> bool:
    return user.is_authenticated and user.role in ADMIN_ROLES


def manageable_queryset(user, model):
    """The posts of `model` this user may see in the staff area."""
    posts = model.objects.all()
    if _is_admin(user):
        return posts
    school_id = _own_school_id(user)
    if school_id:
        return posts.filter(publisher_school_id=school_id)
    return posts.none()


def can_manage(user, post) -> bool:
    """May this user edit / publish / archive this one post?"""
    if _is_admin(user):
        return True
    school_id = _own_school_id(user)
    return bool(school_id) and post.publisher_school_id == school_id


def validate_publisher(user, publisher_type, publisher_school=None) -> None:
    """Refuse (403) posting as anyone not in publishers_for(user)."""
    school_id = publisher_school.id if publisher_school else None
    allowed = {(p["type"], p["id"]) for p in publishers_for(user)}
    if (publisher_type, school_id) not in allowed:
        raise PermissionDenied("You cannot publish as this publisher.")


def validate_audience(user, audience: dict) -> None:
    """School staff may only target students of their own school (403 otherwise).

    `audience` is the checked data from AudienceSerializer, e.g.
    {"schools": [School], "programmes": [Programme, ...], "intakes": [...]}.
    """
    if _is_admin(user):
        return
    school_id = _own_school_id(user)
    school_ids = [school.id for school in audience.get("schools", [])]
    programmes = audience.get("programmes", [])
    if (
        not school_id
        or school_ids != [school_id]
        or any(programme.school_id != school_id for programme in programmes)
    ):
        raise PermissionDenied("You can only send posts to students of your own school.")


class CanManageObject(BasePermission):
    """DRF object permission: `permission_classes = [HasCapability(...), CanManageObject]`."""

    message = "You cannot manage this item."

    def has_object_permission(self, request, view, obj):
        return can_manage(request.user, obj)
