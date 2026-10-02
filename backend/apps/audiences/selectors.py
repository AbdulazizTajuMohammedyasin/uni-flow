"""Who sees what. Both functions follow the rules in models.py and must always agree.

- visible_audience_q(user): which posts a user may see.
- students_matching(audience): which students a post is for (used by notifications).
"""

from django.db.models import Exists, OuterRef, Q, QuerySet

from apps.academics.models import Programme, Term
from apps.accounts import semesters
from apps.accounts.models import User, UserRole
from apps.timetable.models import SectionEnrollment

from .models import Audience

# Audience field -> its column in the Audience-to-X link table.
LINK_COLUMNS = {
    "schools": "school_id",
    "programmes": "programme_id",
    "intakes": "intake_id",
    "courses": "course_id",
    "sections": "coursesection_id",
}
PROFILE_FIELDS = ("schools", "programmes", "intakes")  # stored on StudentProfile


def _current_enrollments(user_ref):
    """Enrolments in sections of the current term (`user_ref` is a user or OuterRef)."""
    return SectionEnrollment.objects.filter(user=user_ref, section__term__is_current=True)


def _student_values(user) -> dict[str, list[int]]:
    """For each audience field, the ids this student has (e.g. their school id)."""
    profile = user.student_profile
    return {
        "schools": [profile.school_id],
        "programmes": [profile.programme_id],
        "intakes": [profile.intake_id],
        "courses": list(_current_enrollments(user).values_list("section__course_id", flat=True)),
        "sections": list(
            SectionEnrollment.objects.filter(user=user).values_list("section_id", flat=True)
        ),
    }


def visible_audience_q(user, via: str = "audience") -> Q:
    """A filter for posts that `user` may see.

    `via` is the name of the post's audience field, e.g.
    Insight.objects.filter(visible_audience_q(request.user)).
    Each check is an Exists() subquery, so a post is never returned twice.
    """
    if not user.is_authenticated:
        return Q(pk__in=[])
    if user.role != UserRole.STUDENT:
        return Q()  # MVP: every staff role sees all published content

    values = _student_values(user) if user.profile_complete else None
    visible = Q()
    for field, column in LINK_COLUMNS.items():
        links = getattr(Audience, field).through.objects.filter(audience_id=OuterRef(via))
        chosen_nothing = ~Exists(links)
        if values is None:
            visible &= chosen_nothing  # incomplete profile: only "all students" posts
        else:
            # e.g. "this post's school list contains the student's school"
            matches = links.filter(**{f"{column}__in": values[field]})
            visible &= chosen_nothing | Exists(matches)

    # Semester range: the post's own fields (prefixed when filtering posts, not audiences).
    p = "" if via == "pk" else f"{via}__"
    if values is None:
        visible &= Q(**{f"{p}semester_min__isnull": True, f"{p}semester_max__isnull": True})
    else:
        semester = user.student_profile.current_semester
        visible &= Q(**{f"{p}semester_min__isnull": True}) | Q(
            **{f"{p}semester_min__lte": semester}
        )
        visible &= Q(**{f"{p}semester_max__isnull": True}) | Q(
            **{f"{p}semester_max__gte": semester}
        )
    return visible


def _students_with(field: str, ids: list[int]) -> Q:
    """Students who match one audience field. Exists() keeps each student once."""
    if field in PROFILE_FIELDS:
        return Q(**{f"student_profile__{LINK_COLUMNS[field]}__in": ids})
    if field == "courses":
        return Q(Exists(_current_enrollments(OuterRef("pk")).filter(section__course_id__in=ids)))
    return Q(Exists(SectionEnrollment.objects.filter(user=OuterRef("pk"), section_id__in=ids)))


def _students_in_semesters(low: int | None, high: int | None) -> Q:
    """Students whose semester is within low..high (either may be None for no limit).

    Without an override the semester comes from the intake date and the student's calendar
    (Foundation or Undergraduate), so the range is turned into a range of intake start
    dates per calendar (no per-student calculation needed).
    """
    is_foundation = Q(student_profile__programme__level=Programme.Level.FOUNDATION)
    by_intake = Q()
    for calendar, in_calendar in [
        (Term.Calendar.FOUNDATION, is_foundation),
        (Term.Calendar.UNDERGRADUATE, ~is_foundation),
    ]:
        earliest, latest = semesters.intake_start_range(low, high, semesters.today(), calendar)
        dates = Q()
        if earliest:
            dates &= Q(student_profile__intake__start_date__gte=earliest)
        if latest:
            dates &= Q(student_profile__intake__start_date__lte=latest)
        by_intake |= in_calendar & dates
    by_intake &= Q(student_profile__semester_override__isnull=True)
    by_override = Q(student_profile__semester_override__isnull=False)
    if low:
        by_override &= Q(student_profile__semester_override__gte=low)
    if high:
        by_override &= Q(student_profile__semester_override__lte=high)
    return by_intake | by_override


def students_matching(audience: Audience) -> QuerySet[User]:
    """The active students that `audience` covers."""
    students = User.objects.filter(role=UserRole.STUDENT, is_active=True, is_suspended=False)
    chosen = {
        field: list(getattr(audience, field).values_list("id", flat=True)) for field in LINK_COLUMNS
    }
    has_semesters = audience.semester_min is not None or audience.semester_max is not None
    if not any(chosen.values()) and not has_semesters:
        return students  # all students

    # A narrowed audience only reaches students who finished their profile.
    students = students.filter(
        student_profile__school__isnull=False,
        student_profile__programme__isnull=False,
        student_profile__intake__isnull=False,
    )
    for field, ids in chosen.items():
        if ids:
            students = students.filter(_students_with(field, ids))
    if has_semesters:
        students = students.filter(
            _students_in_semesters(audience.semester_min, audience.semester_max)
        )
    return students
