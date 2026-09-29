"""Who sees what. Both functions follow the rules in models.py and must always agree.

- visible_audience_q(user): which posts a user may see (used by the read API, M3+).
- students_matching(audience): which students a post is for (used by notifications, M9).
"""

from django.db.models import Exists, OuterRef, Q, QuerySet

from apps.accounts.models import User, UserRole

from .models import Audience

# (Audience field, the matching StudentProfile field)
FIELDS = [("schools", "school_id"), ("programmes", "programme_id"), ("intakes", "intake_id")]


def visible_audience_q(user, via: str = "audience") -> Q:
    """A filter for posts that `user` may see.

    `via` is the name of the post's audience field, e.g.
    Announcement.objects.filter(visible_audience_q(request.user)).
    Each check is an Exists() subquery, so a post is never returned twice.
    """
    if not user.is_authenticated:
        return Q(pk__in=[])
    if user.role != UserRole.STUDENT:
        return Q()  # MVP: every staff role sees all published content

    profile = user.student_profile if user.profile_complete else None
    visible = Q()
    for field, profile_field in FIELDS:
        links = getattr(Audience, field).through.objects.filter(audience_id=OuterRef(via))
        chosen_nothing = ~Exists(links)
        if profile is None:
            visible &= chosen_nothing  # incomplete profile: only "all students" posts
        else:
            # e.g. "this post's school list contains the student's school"
            matches = links.filter(**{profile_field: getattr(profile, profile_field)})
            visible &= chosen_nothing | Exists(matches)
    return visible


def students_matching(audience: Audience) -> QuerySet[User]:
    """The active students that `audience` covers."""
    students = User.objects.filter(role=UserRole.STUDENT, is_active=True, is_suspended=False)
    chosen = {
        field: list(getattr(audience, field).values_list("id", flat=True)) for field, _ in FIELDS
    }
    if not any(chosen.values()):
        return students  # all students

    # A narrowed audience only reaches students who finished their profile.
    students = students.filter(
        student_profile__school__isnull=False,
        student_profile__programme__isnull=False,
        student_profile__intake__isnull=False,
    )
    for field, profile_field in FIELDS:
        if chosen[field]:
            students = students.filter(**{f"student_profile__{profile_field}__in": chosen[field]})
    return students
