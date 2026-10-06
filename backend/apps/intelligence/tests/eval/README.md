# AI evaluation set

Labelled examples for `pipenv run python manage.py evaluate_intelligence`, which runs the
**real** AI on them and prints how many it got right. Run it by hand when the AI
instructions or models change; it is not run in CI (it needs the API key).

- `changes.json`: group conversations and the timetable changes they contain (an empty
  `expected` list means "no change", e.g. a rumour or a question). Messages with
  `"new": true` are the ones being checked; the others are earlier context. Times are
  Malaysia time; "today" is the date of each message.
- `timetables.json`: timetable sheets (as text, one tab each, the way UniFlow reads an
  Excel tab) and the classes in them.

The examples are made up in the style of AIU groups. When the AI gets a real message
wrong, add it here **with names and phone numbers removed**.

In `expected`, a field that is left out is not checked (e.g. leave out `course_code`
when the message doesn't name the course and the group does).
