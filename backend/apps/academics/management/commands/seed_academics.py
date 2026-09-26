"""Load AIU's real schools and programmes (plus sample intakes) into the database.

Source: https://aiu.edu.my/academic-programmes/ (the page shows no codes, so the short
codes below are UniFlow's own). Safe to run many times: existing rows are updated, never
duplicated.

    pipenv run python manage.py seed_academics
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.academics.models import Intake, Programme, School

# (school code, school name, [(programme code, programme name, level), ...])
AIU_STRUCTURE = [
    (
        "SBSS",
        "School of Business & Social Sciences",
        [
            ("BBA", "Bachelor of Business Administration (Honours)", "bachelor"),
            ("BBA-MKT", "Bachelor of Business Administration (Honours) (Marketing)", "bachelor"),
            (
                "BBA-HRM",
                "Bachelor of Business Administration (Honours) (Human Resource Management)",
                "bachelor",
            ),
            ("BECON", "Bachelor of Economics (Honours)", "bachelor"),
            ("BSD", "Bachelor of Social Development (Honours)", "bachelor"),
            ("BFIN-IF", "Bachelor of Finance (Islamic Finance) (Honours)", "bachelor"),
            ("BPIR", "Bachelor of Politics and International Relations (Honours)", "bachelor"),
            (
                "BBA-CS",
                "Bachelor of Business Administration with Computer Science (Honours)",
                "bachelor",
            ),
            ("MBM", "Master of Business Management", "master"),
            ("MSB", "Master in Social Business", "master"),
            ("PHD-SBSS", "Doctor of Philosophy", "phd"),
        ],
    ),
    (
        "SEHS",
        "School of Education & Human Sciences",
        [
            ("BEE", "Bachelor of Elementary Education (Honours)", "bachelor"),
            ("BECE", "Bachelor in Early Childhood Education (Honours)", "bachelor"),
            ("BMC", "Bachelor of Media and Communication (Honours)", "bachelor"),
            ("MED", "Master of Education", "master"),
            ("PHD-SEHS", "Doctor of Philosophy", "phd"),
        ],
    ),
    (
        "SCI",
        "School of Computing and Informatics",
        [
            ("BCS", "Bachelor in Computer Science (Honours)", "bachelor"),
            ("BDS", "Bachelor in Data Science (Honours)", "bachelor"),
            ("BIT-CYB", "Bachelor in Information Technology (Cybersecurity) (Honours)", "bachelor"),
            ("MCOMP", "Master of Computing", "master"),
            ("PHD-CS", "Doctor of Philosophy in Computer Science", "phd"),
        ],
    ),
    (
        "CFGS",
        "Centre for Foundation and General Studies",
        [
            ("FCOMP", "Foundation in Computing", "foundation"),
            ("FARTS", "Foundation in Arts", "foundation"),
        ],
    ),
]

# AIU has two intakes a year: March and October (start dates are the 1st of the month).
SAMPLE_INTAKES = [
    ("2023-MAR", "March 2023", date(2023, 3, 1)),
    ("2023-OCT", "October 2023", date(2023, 10, 1)),
    ("2024-MAR", "March 2024", date(2024, 3, 1)),
    ("2024-OCT", "October 2024", date(2024, 10, 1)),
    ("2025-MAR", "March 2025", date(2025, 3, 1)),
    ("2025-OCT", "October 2025", date(2025, 10, 1)),
    ("2026-MAR", "March 2026", date(2026, 3, 1)),
    ("2026-OCT", "October 2026", date(2026, 10, 1)),
]


class Command(BaseCommand):
    help = "Load AIU's schools and programmes (and sample intakes). Safe to run repeatedly."

    @transaction.atomic
    def handle(self, *args, **options):
        for school_code, school_name, programmes in AIU_STRUCTURE:
            school, _ = School.objects.update_or_create(
                code=school_code, defaults={"name": school_name}
            )
            for code, name, level in programmes:
                Programme.objects.update_or_create(
                    code=code, defaults={"school": school, "name": name, "level": level}
                )

        for code, name, start_date in SAMPLE_INTAKES:
            Intake.objects.update_or_create(
                code=code, defaults={"name": name, "start_date": start_date}
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {School.objects.count()} schools, {Programme.objects.count()} programmes, "
                f"{Intake.objects.count()} intakes."
            )
        )
