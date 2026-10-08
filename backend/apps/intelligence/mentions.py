"""Which student is "Ali"? (docs/12-intelligence.md, "Direct mentions")

The AI copies the names of students a message asks to do something ("Ali Hassan and Sara,
please see me"). Plain code then looks for each name:
1. among the students who added that group (SourceMember),
2. then among the students the group is for (its school, programme, intake, course…).
A name matches a student's full name, part of it ("Ali" for "Ali Hassan"), or a nickname
from their profile. A name that fits two students is NOT a mention: UniFlow never guesses.
Phone numbers are never used.
"""

import re

from django.db.models import Q

from apps.accounts.models import User, UserRole

from .models import Insight, InsightMention, Source

# Words people put before a name ("Bro Ali", "Sis Sara") that aren't part of it.
TITLES = {"mr", "mrs", "ms", "miss", "dr", "bro", "brother", "sis", "sister", "sir", "madam"}


def _words(text: str) -> list[str]:
    """ "  Sara-Lim, " -> ["sara", "lim"]; letters only, any language."""
    return re.sub(r"[^\w\s]|\d|_", " ", text.casefold()).split()


def _name_words(name: str) -> list[str]:
    return [word for word in _words(name) if word not in TITLES]


def is_match(name: str, user: User) -> bool:
    """Every word of the name is a word of the student's full name, or the name is one of
    their nicknames (exactly)."""
    wanted = _name_words(name)
    if not wanted:
        return False
    if set(wanted) <= set(_words(user.full_name)):
        return True
    aliases = getattr(getattr(user, "student_profile", None), "aliases", "")
    return any(wanted == _words(alias) for alias in aliases.split(",") if alias.strip())


def _candidates(name: str, students) -> list[User]:
    """Students whose name or nicknames contain the name's first word (a quick database
    filter), then checked exactly."""
    first = _name_words(name)[0]
    possible = students.filter(
        Q(full_name__icontains=first) | Q(student_profile__aliases__icontains=first)
    ).select_related("student_profile")
    return [user for user in possible.distinct() if is_match(name, user)]


def _scope_students(source: Source, students):
    """The students the group is for (its school, programme, intake, course or section),
    or nobody if it has no scope: a name is never looked up among all students."""
    wanted = {
        "student_profile__school_id": source.school_id,
        "student_profile__programme_id": source.programme_id,
        "student_profile__intake_id": source.intake_id,
        "section_enrollments__section__course_id": source.course_id,
        "section_enrollments__section_id": source.section_id,
    }
    filters = {column: value for column, value in wanted.items() if value}
    return students.filter(**filters).distinct() if filters else students.none()


def find_student(name: str, source: Source) -> User | None:
    """The one student this name means, or None (nobody, or more than one)."""
    if not _name_words(name):
        return None
    students = User.objects.filter(role=UserRole.STUDENT, is_active=True, is_suspended=False)
    members = students.filter(source_memberships__source=source)
    for group in (members, _scope_students(source, students)):
        found = _candidates(name, group)
        if len(found) == 1:
            return found[0]
        if len(found) > 1:
            return None  # two people fit: don't guess, and don't look further
    return None


def record_mentions(insight: Insight, names: list[str], source: Source) -> list[InsightMention]:
    """Save a mention for each name that means exactly one student."""
    mentions = []
    for name in names:
        user = find_student(name, source)
        if user is not None:
            mention, _ = InsightMention.objects.get_or_create(
                insight=insight, user=user, defaults={"matched_text": name[:100]}
            )
            mentions.append(mention)
    return mentions
