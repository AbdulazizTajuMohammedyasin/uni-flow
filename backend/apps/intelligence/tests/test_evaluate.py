"""The evaluation command, with the fake AI (the real run is by hand: see tests/eval/)."""

import json
from io import StringIO

from django.core.management import call_command

from apps.intelligence.management.commands import evaluate_intelligence as evaluate
from apps.intelligence.providers import fake_provider

MONDAY, WEDNESDAY = ["monday", "14:00", "16:00"], ["wednesday", "11:00", "13:00"]


def run(*args) -> str:
    out = StringIO()
    call_command("evaluate_intelligence", *args, stdout=out)
    return out.getvalue()


def change(message_id=1, **fields):
    return {
        "kind": "class_moved",
        "course_code": "CDE2313",
        "section": "A",
        "date": "2026-10-06",
        "new_start": "14:00",
        "title": "Moved",
        "summary": "Moved.",
        "confidence": 0.9,
        "evidence": [{"message_id": message_id, "quote": "moves to 2pm"}],
    } | fields


def test_the_evaluation_set_is_valid():
    cases = evaluate._load("changes.json")
    assert len(cases) >= 10
    assert all(case["messages"] and "expected" in case for case in cases)
    assert {e["kind"] for case in cases for e in case["expected"]} == set(
        evaluate.extraction.TIMETABLE_KINDS
    )
    assert all(sheet["expected"] for sheet in evaluate._load("timetables.json"))


def test_changes_are_scored_per_kind(monkeypatch, tmp_path):
    cases = [
        {
            "name": "moved",
            "group": "CDE2313 Section A",
            "messages": [{"sender": "Dr Lee", "sent": "2026-10-05 09:00", "text": "2pm"}],
            "expected": [{"kind": "class_moved", "date": "2026-10-06", "new_start": "14:00"}],
        },
        {
            "name": "wrong time",
            "group": "CDE2313 Section A",
            "messages": [{"sender": "Dr Lee", "sent": "2026-10-05 09:00", "text": "3pm"}],
            "expected": [{"kind": "class_moved", "new_start": "15:00"}],
        },
        {
            "name": "rumour",
            "group": "SCI",
            "messages": [{"sender": "Ali", "sent": "2026-10-05 09:00", "text": "maybe?"}],
            "expected": [],
        },
    ]
    (tmp_path / "changes.json").write_text(json.dumps(cases))
    monkeypatch.setattr(evaluate, "EVAL_DIR", tmp_path)
    fake_provider().answers.extend(
        [
            {"changes": [change()]},
            {"changes": [change()]},  # 14:00, not 15:00
            {"changes": [change(), change(message_id=99)]},  # 99: not a message shown
        ]
    )

    output = run("--only", "changes")

    assert "class_moved       1/2" in output
    assert "no change         0/1" in output
    assert "all               1/3" in output
    assert "Changes found that were not expected: 2" in output
    assert "wrong time: found class_moved CDE2313 A 2026-10-06 14:00" in output
    question = fake_provider().calls[0]
    assert "* [1] Dr Lee (Mon 05/10/2026 09:00): 2pm" in question["prompt"]


def test_timetable_reading_is_scored_per_class(monkeypatch, tmp_path):
    sheets = [
        {
            "name": "list",
            "tab": "BCS",
            "text": "CDE3101 | 1 | Mon | 2-4pm",
            "expected": [
                {"course_code": "CDE3101", "section": "1", "meetings": [MONDAY]},
                {"course_code": "CDE3205", "section": "2", "meetings": [WEDNESDAY]},
            ],
        }
    ]
    (tmp_path / "timetables.json").write_text(json.dumps(sheets))
    monkeypatch.setattr(evaluate, "EVAL_DIR", tmp_path)
    meeting = {"day": "monday", "start": "14:00", "end": "16:00"}
    fake_provider().answers.append(
        {
            "classes": [
                {"course_code": "CDE3101", "section": "Grp 1", "meetings": [meeting]},
                {"course_code": "XYZ9999", "section": "", "meetings": [meeting]},
            ]
        }
    )

    output = run("--only", "timetables")

    assert "classes           1/2" in output
    assert "missing CDE3205 section 2" in output
    assert "not in the sheet: XYZ9999 section 1" in output
