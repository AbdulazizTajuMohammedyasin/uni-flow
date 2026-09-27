"""Who may manage what — the single place that decides it (docs/06-auth-and-permissions.md).

A capability is a yes/no permission such as "announcements.manage". The same rules drive:
- the API's permission checks (`HasCapability`), and
- `capabilities` / `publishers` in users/me/, so the website only shows allowed actions.
Which *items* a school staff member may touch (their own school) is checked per feature later.
"""

from rest_framework.permissions import BasePermission

from apps.academics.models import School

from .models import UserRole

# Content that staff manage in the staff dashboard.
CONTENT_CAPABILITIES = [
    "announcements.manage",
    "events.manage",
    "documents.manage",
    "applications.manage",
    "communities.manage",
    "timetable.manage",
]
ALL_CAPABILITIES = [*CONTENT_CAPABILITIES, "academics.manage", "users.manage"]

ADMIN_ROLES = {UserRole.UNIVERSITY_ADMIN, UserRole.SUPER_ADMIN}


def staff_school_id(user) -> int | None:
    profile = getattr(user, "staff_profile", None)
    return profile.school_id if profile else None


def capabilities_for(user) -> dict[str, bool]:
    """Every capability as True/False for this user."""
    granted: set[str] = set()
    if user and user.is_authenticated:
        if user.role in ADMIN_ROLES:
            granted.update(CONTENT_CAPABILITIES)
            granted.add("academics.manage")
        elif user.role == UserRole.SCHOOL_STAFF and staff_school_id(user):
            # School staff without a school get nothing: a half-set-up account can't act.
            granted.update(CONTENT_CAPABILITIES)
        if user.role == UserRole.SUPER_ADMIN:
            granted.add("users.manage")
    return {name: name in granted for name in ALL_CAPABILITIES}


def publishers_for(user) -> list[dict]:
    """Who this user may publish as: the university and/or a school."""
    if not (user and user.is_authenticated):
        return []
    if user.role in ADMIN_ROLES:
        schools = School.objects.filter(is_active=True).order_by("name")
        return [
            {"type": "university", "id": None, "name": "Albukhary International University"},
            *({"type": "school", "id": s.id, "name": s.name} for s in schools),
        ]
    if user.role == UserRole.SCHOOL_STAFF and staff_school_id(user):
        school = user.staff_profile.school
        return [{"type": "school", "id": school.id, "name": school.name}]
    return []


def HasCapability(name: str) -> type[BasePermission]:  # noqa: N802 (reads like a class)
    """DRF permission: `permission_classes = [HasCapability("announcements.manage")]`."""
    if name not in ALL_CAPABILITIES:
        raise ValueError(f"Unknown capability: {name}")

    class _HasCapability(BasePermission):
        message = "You do not have permission to manage this."

        def has_permission(self, request, view):
            return capabilities_for(request.user)[name]

    _HasCapability.__name__ = f"HasCapability[{name}]"
    return _HasCapability
