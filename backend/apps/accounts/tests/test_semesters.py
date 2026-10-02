from datetime import date, timedelta

import pytest
from django.core.management import call_command

from apps.accounts import semesters
from apps.accounts.semesters import range_from_starts, semester_for, semester_from_starts

# Official undergraduate term starts (2024/2025 and 2025/2026), newest first.
OFFICIAL_STARTS = [
    date(2026, 8, 3),
    date(2026, 3, 23),
    date(2025, 10, 27),
    date(2025, 8, 4),
    date(2025, 3, 17),
    date(2024, 10, 28),
]


def started_by(on):
    return [start for start in OFFICIAL_STARTS if start <= on]


@pytest.mark.parametrize(
    ("on", "expected"),
    [
        (date(2024, 10, 15), 1),  # orientation, before Semester 1 starts
        (date(2024, 11, 1), 1),
        (date(2025, 3, 16), 1),
        (date(2025, 3, 17), 2),
        (date(2025, 8, 4), 3),  # short semester
        (date(2025, 10, 27), 4),  # year 2 starts
        (date(2026, 3, 23), 5),
        (date(2026, 8, 3), 6),
    ],
)
def test_semester_for_an_october_2024_intake(on, expected):
    assert semester_from_starts(date(2024, 10, 1), started_by(on)) == expected


@pytest.mark.parametrize(
    ("low", "high"), [(1, 1), (2, 3), (4, 6), (2, None), (None, 3), (6, None), (7, None)]
)
def test_intake_range_agrees_with_the_semester(low, high):
    """For every intake start over 4 years, the date range and the calculation agree."""
    starts = started_by(date(2026, 10, 15))
    earliest, latest = range_from_starts(low, high, starts)
    intake = date(2023, 1, 1)
    while intake <= date(2027, 1, 31):
        in_range = (earliest is None or intake >= earliest) and (latest is None or intake <= latest)
        semester = semester_from_starts(intake, starts)
        in_semesters = (low is None or semester >= low) and (high is None or semester <= high)
        assert in_range == in_semesters, intake
        intake += timedelta(days=1)


@pytest.mark.django_db
def test_semester_for_reads_the_term_table():
    call_command("seed_academics", stdout=None)
    assert semester_for(date(2025, 10, 1), date(2026, 8, 10)) == 3  # Oct 2025 intake
    assert semester_for(date(2025, 10, 1), date(2025, 10, 20)) == 1  # before term starts
    # Foundation terms start earlier (13 Oct 2025, 9 Feb 2026, 8 Jun 2026):
    assert semester_for(date(2025, 10, 1), date(2026, 7, 1), "foundation") == 3


def test_today_is_a_date():
    assert isinstance(semesters.today(), date)
