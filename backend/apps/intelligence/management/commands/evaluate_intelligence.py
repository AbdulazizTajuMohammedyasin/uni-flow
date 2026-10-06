"""How accurate is the AI? `pipenv run python manage.py evaluate_intelligence`

Runs the REAL AI on the labelled examples in apps/intelligence/tests/eval/ and prints how
many it got right per kind. Nothing is saved. Run it by hand when the AI instructions or
models change (not in CI: it needs the API key). See tests/eval/README.md.
"""

import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.intelligence import extraction, timetable_reading
from apps.intelligence.extraction import Change
from apps.intelligence.models import Message, Source
from apps.intelligence.providers import AIError, AIRateLimited, get_provider
from apps.timetable.importing import section_code

EVAL_DIR = Path(__file__).resolve().parents[2] / "tests" / "eval"
NO_CHANGE = "no change"


def _load(name: str) -> list[dict]:
    return json.loads((EVAL_DIR / name).read_text(encoding="utf-8"))


def _with_retries(ask, attempts: int = 3, wait: int = 30):
    """Ask again after a pause when the AI is busy or says "too many requests"."""
    for attempt in range(attempts):
        try:
            return ask()
        except AIError as error:
            if attempt == attempts - 1:
                raise
            time.sleep(wait if isinstance(error, AIRateLimited) else wait // 3)
    return None


# --- Timetable changes --------------------------------------------------------------------


def _same_room(expected: str, found: str) -> bool:
    a, b = (value.lower().replace(" ", "") for value in (expected, found))
    return bool(b) and (a in b or b in a)


def matches(expected: dict, found: Change) -> bool:
    """Every field given in `expected` must agree (fields left out aren't checked)."""
    checks = {
        "kind": lambda v: found.kind == v,
        "course_code": lambda v: found.course_code == v.upper().replace(" ", ""),
        "section": lambda v: found.section == section_code(v),
        "date": lambda v: found.day.isoformat() == v,
        "new_date": lambda v: (found.new_date.isoformat() if found.new_date else "") == v,
        "new_start": lambda v: found.new_start == v,
        "new_end": lambda v: found.new_end == v,
        "new_room": lambda v: _same_room(v, found.new_room),
    }
    return all(checks[field](value) for field, value in expected.items())


def find_changes(case: dict) -> list[Change]:
    """What the AI finds in one conversation, checked like in the real pipeline."""
    source = Source(title=case["group"])
    window, new_ids = [], set()
    for number, item in enumerate(case["messages"], start=1):
        sent = datetime.fromisoformat(item["sent"])
        window.append(
            Message(
                id=number,
                sender_name=item["sender"],
                text=item["text"],
                sent_at=timezone.make_aware(sent),
            )
        )
        if item.get("new", True):
            new_ids.add(number)
    answer = get_provider().ask_json(
        model=settings.AI_SMART_MODEL,
        instructions=extraction.INSTRUCTIONS,
        prompt=extraction._prompt(source, window, new_ids),
        schema=extraction.SCHEMA,
    )
    return [
        change
        for item in answer.get("changes", [])
        if (change := extraction.check(item, window)) is not None
    ]


def score_case(case: dict, found: list[Change]) -> tuple[Counter, Counter, list[Change]]:
    """(right per kind, total per kind, changes found that weren't expected)."""
    right, total = Counter(), Counter()
    extra = list(found)
    if not case["expected"]:
        total[NO_CHANGE] += 1
        right[NO_CHANGE] += not found
        return right, total, extra
    for expected in case["expected"]:
        total[expected["kind"]] += 1
        hit = next((change for change in extra if matches(expected, change)), None)
        if hit is not None:
            right[expected["kind"]] += 1
            extra.remove(hit)
    return right, total, extra


def _describe(change: Change) -> str:
    parts = [change.kind, change.course_code, change.section, change.day.isoformat()]
    if change.new_date:
        parts.append(f"-> {change.new_date.isoformat()}")
    parts += [change.new_start, change.new_end, change.new_room]
    return " ".join(part for part in parts if part)


# --- Timetable reading --------------------------------------------------------------------


def _class_key(row: dict) -> tuple[str, str]:
    # No section shown: UniFlow saves it as section "1" (see rows_from_json).
    return row["course_code"].upper().replace(" ", ""), section_code(row["section"]) or "1"


def score_sheet(sheet: dict, rows: list[dict]) -> tuple[int, int, list[str]]:
    """(classes read correctly, classes expected, problems). A class is correct when its
    code, section and every weekly meeting (day, start, end) are right."""
    found = {_class_key(row): row for row in rows}
    problems, right = [], 0
    for expected in sheet["expected"]:
        key = _class_key(expected)
        row = found.pop(key, None)
        wanted = sorted(tuple(meeting) for meeting in expected["meetings"])
        if row is None:
            problems.append(f"missing {key[0]} section {key[1]}")
            continue
        got = sorted((m["day"], m["start"], m["end"]) for m in row["meetings"])
        if got == wanted:
            right += 1
        else:
            problems.append(f"{key[0]}: expected {wanted}, got {got}")
    problems += [f"not in the sheet: {code} section {section}" for code, section in found]
    return right, len(sheet["expected"]), problems


class Command(BaseCommand):
    help = "Run the real AI on the labelled examples and print its accuracy per kind."

    def add_arguments(self, parser):
        parser.add_argument("--only", choices=["changes", "timetables"], help="Run one part.")

    def handle(self, *args, **options):
        if options["only"] != "timetables":
            self.evaluate_changes()
        if options["only"] != "changes":
            self.evaluate_timetables()

    def _line(self, label: str, right: int, total: int) -> None:
        style = self.style.SUCCESS if right == total else self.style.WARNING
        self.stdout.write(style(f"  {label:<18}{right}/{total}"))

    def evaluate_changes(self) -> None:
        cases = _load("changes.json")
        model, prompt = settings.AI_SMART_MODEL, extraction.PROMPT_VERSION
        self.stdout.write(f"Timetable changes: {model} ({prompt}), {len(cases)} conversations")
        right, total, extra_count = Counter(), Counter(), 0
        for case in cases:
            problem = ""
            try:
                found = _with_retries(lambda case=case: find_changes(case))
            except AIError as error:
                found, problem = [], f" (AI error: {error})"
            case_right, case_total, extra = score_case(case, found)
            right.update(case_right)
            total.update(case_total)
            extra_count += len(extra)
            if problem or case_right != case_total or extra:
                got = "; ".join(_describe(change) for change in found) or "nothing"
                line = f"  WRONG {case['name']}: found {got}{problem}"
                self.stdout.write(self.style.WARNING(line))
            else:
                self.stdout.write(f"  OK    {case['name']}")
        for kind in [*extraction.TIMETABLE_KINDS, NO_CHANGE]:
            if total[kind]:
                self._line(kind, right[kind], total[kind])
        self._line("all", sum(right.values()), sum(total.values()))
        self.stdout.write(f"  Changes found that were not expected: {extra_count}")

    def evaluate_timetables(self) -> None:
        sheets = _load("timetables.json")
        model, prompt = settings.AI_SMART_MODEL, timetable_reading.PROMPT_VERSION
        self.stdout.write(f"Timetable reading: {model} ({prompt}), {len(sheets)} sheets")
        right = total = 0
        for sheet in sheets:
            prompt_text = f'Timetable tab "{sheet["tab"]}":\n{sheet["text"]}'
            try:
                rows = _with_retries(lambda text=prompt_text: timetable_reading._ask(text))
            except AIError as error:
                rows = []
                self.stdout.write(self.style.WARNING(f"  WRONG {sheet['name']}: AI error: {error}"))
            sheet_right, sheet_total, problems = score_sheet(sheet, rows)
            right, total = right + sheet_right, total + sheet_total
            for problem in problems:
                self.stdout.write(self.style.WARNING(f"  WRONG {sheet['name']}: {problem}"))
            if not problems:
                self.stdout.write(f"  OK    {sheet['name']}")
        self._line("classes", right, total)
