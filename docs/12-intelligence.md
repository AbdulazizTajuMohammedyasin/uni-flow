# 12 — Intelligence Pipeline

How UniFlow turns raw messages into personal, prioritized information. The product rules are in [01](01-product.md); the tables are in [03](03-data-model.md); the sources are in [08](08-messaging-integrations.md).

## The rule that shapes everything

**The AI reads and proposes. Ordinary Django code decides and acts.**

- The AI model does the language work: is this message academic, what does it say, what kind of information is it, what are the dates, courses and names in it.
- Plain, tested Django code does everything else: matching "CDE2313" to a real course, finding the affected students, scoring relevance, choosing tiers, sending notifications and changing a timetable (only after the student confirms).

This keeps the system explainable, testable, cheap and safe: a strange or malicious message can at worst create a wrong *proposal*, never a wrong action.

## Pipeline

```
 Source (WhatsApp group, Telegram group/channel, staff post, pasted text)
   │
 1 Receive      Message row (raw text, sender, time, reply-to)                  apps/intelligence
   │            → job "triage" queued
 2 Triage       cheap model: academic information or noise?                   apps/intelligence
   │            noise → message marked, nothing else
 3 Understand   stronger model, with the conversation window around it:
   │            kind, title, summary, structured fields, topics, importance,
   │            action required, people mentioned, courses/sections/dates
   │            → validated against a schema; invalid output is rejected
 4 Resolve      plain code: course code → Course/sections; date → ClassMeeting;
   │            names → Users; affected scope → Audience
 5 Merge        same information already known (forwarded to 10 groups)?
   │            → attach as more evidence instead of a new insight
 6 Deliver      for each affected student: relevance score, tier, reason
   │            → Delivery rows; timetable kinds → ClassChange proposals
 7 Notify       immediate (direct attention, action required, important) or digest
```

Each step runs as a **background job on Inngest** (see [02](02-system-architecture.md#background-jobs)), so a slow or failed AI call never blocks a web request, and failed steps are retried.

## Step details

### 1. Receive

Connectors and the manual paste form create `Message` rows. Images, PDFs, spreadsheets and Google Drive links in a message are stored as `MessageFile` rows (other attachments are ignored). Nothing is interpreted yet. Raw text and files are kept only for the retention period (see [09](09-security.md)).

### 2. Triage

A small, cheap model answers one question per batch of messages: *does this contain academic or university information?* Greetings, jokes, "thanks", stickers and marketplace posts are dropped here. This keeps cost low because most group traffic is noise.

### 3. Understand (conversation-aware)

Messages are never read alone. The model receives:

- the new message(s),
- the previous messages from the same source within a time window (default: the last 30 messages or 24 hours),
- the message being replied to, if any,
- the source's context: its name and scope (for example "CDE2313 Section A group, School of Computing").

**Built so far (M5.6):** `apps/intelligence/extraction.py` handles the four timetable kinds (`class_moved`, `class_cancelled`, `room_changed`, `extra_session`). Up to 10 new academic messages (marked `*`) are sent with the earlier messages of the last 24 hours (up to 30) to the smart model. Every change must quote a message that was shown, or it is rejected; dates like "tomorrow" are worked out from the message's own date. Each message is marked `extracted_at` so it is never sent twice. The reply-to message and the other kinds come in M7.1.

**Built (M7.1):** the same single request also returns `items`: every other kind (opportunities, notices, `direct_request`) with title, summary, importance (0–100), action needed and what to do, deadline and event date/time, place, link (only `http(s)`), topics (from the interest list), who it is for (course, school and programme codes and a semester range such as "Year 2" = 4–6) and, for requests, the names of the students asked. Plain code checks every field like user input; unknown codes are ignored; if the message names nobody, the group's own scope is used (or everyone, narrowed per student in M7.4). The message being replied to is added to the window even when it is older. Names are kept in the insight's `data` and matched to students in M7.2. **M9.18:** a course named without its code (and not among the group's courses) comes back in `course_names`; plain code looks the name up in AIU's course list (whole words, any case), and a name shared by two courses means both.

It returns **structured output** that must match a fixed schema, for example:

```json
{
  "kind": "class_moved",
  "title": "CDE2313 class moved to 2 PM tomorrow",
  "summary": "Tomorrow's CDE2313 lecture moves from 10:00 to 14:00.",
  "importance": 80,
  "action_required": false,
  "course_codes": ["CDE2313"],
  "sections": [],
  "date": "2026-10-02",
  "old_start": "10:00", "new_start": "14:00",
  "mentions": [],
  "topics": [],
  "info_type": "academic_notice",
  "confidence": 0.86,
  "evidence_message_ids": [5512]
}
```

Output that does not match the schema, or refers to messages outside the window, is rejected and logged.

**Insight kinds (MVP):**

| Group | Kinds |
|---|---|
| Timetable | `class_moved`, `class_cancelled`, `room_changed`, `extra_session` (mandatory academic session added) |
| Opportunities | `internship`, `bootcamp`, `industry_visit`, `competition`, `scholarship` |
| Notices | `academic_notice`, `student_affairs`, `mandatory_event`, `deadline` |
| Timetable files | `timetable_shared` (a message carries a full timetable: image, PDF, spreadsheet or link); see [Reading timetables](#reading-timetables) |
| People | `direct_request` (a named student is asked to do something) |

### 4. Resolve (plain code)

| Extracted | Resolved to | If it can't be resolved |
|---|---|---|
| Course code "CDE2313" | `Course`, then its sections in the current term | Uses the source's own scope; otherwise the insight waits for staff review |
| Section "A" or the source's section | `CourseSection` | Applies to all sections of the course, with lower confidence |
| Date + time | The matching `ClassMeeting` | A `ClassChange` without a meeting (for example an extra session) |
| A name | `User`: first among the **students who added that group** (`SourceMember`), then the source's scope; by full name or nickname | No mention is recorded; a name that matches two people is never guessed |
| "Year 2 students", "all SCI students" | `Audience` (schools, programmes, intakes, semesters, courses, sections) | Falls back to the group's members, then the source's scope |

### 5. Merge duplicates

The same announcement is often forwarded to many groups. A new insight is compared with recent insights of the same kind (same course and date for timetable kinds; similar title and link for others). A match adds the message as **extra evidence** and can raise confidence; it does not create a second card or a second notification.

**Built (M7.3):** `apps/intelligence/merging.py`, checked before each AI insight is saved, against AI insights of the same kind from the last 14 days (retracted ones excluded):
- **Timetable changes** merge only on the exact `merge_key`: course, sections, date, new date, new start and end, new room. "Moved to 2 PM" and "moved to 3 PM" stay two insights, so a conflict is visible.
- **Other kinds** merge on the same link (`kind|link`); otherwise on the same date (deadline or event) and a similar title (60% of words in common; 75% when neither has a date). An item with a different link never merges, and a copy's link is adopted by an insight that had none. **M9.19:** two requests merge only when they name the same students, and items for different courses never merge (Assignment 1 of two courses, due the same day).
- The insight keeps the **higher confidence**; an unsure draft that reaches the "unsure" threshold this way is published (a timetable change with an unknown course, or naming a section its course doesn't have this term, still waits for an admin; such a change is held as a draft from the start and never sent to the whole course instead, M9.19). Names in the copy are matched as mentions too.

### How sure must the AI be?

Every AI insight has a `confidence` from 0 to 1. It decides what students see:

| Confidence | What happens | Example |
|---|---|---|
| **0.8 or more** | Published and delivered normally | "CDE2313 class moved from 10 AM to 2 PM tomorrow." |
| **0.5 to 0.8** | Published, but **only in the daily digest**, marked **"Not confirmed"** | "I think the class might be moved tomorrow?" |
| **Below 0.5** | Kept as a **draft**, not shown to students, until someone checks it in the Django admin | A half-sentence reply that may or may not be about class |

Two exceptions:

- **Timetable changes** always go to the affected students as a proposal they confirm (0.5 or more), because the student is the one who decides.
- **Staff posts** have confidence 1 and are published when the staff member publishes them.

### 6. Deliver: relevance and tiers

The AI scores **importance once per insight**. **Relevance is computed by code per student**, because asking the AI about every student would be slow and expensive, and code can explain its reasons.

**Who can receive it at all (hard filter):** students matched by the insight's `Audience` through `audiences.selectors.students_matching` (built in M2.5, extended with courses, sections and semesters), plus any mentioned students. When the audience is just "this group", the hard filter is the group's members (`SourceMember`).

**Relevance score (0–100) for each of those students:**

| Signal | Effect |
|---|---|
| Named directly | 100 |
| A member of the group the message came from | high |
| In the targeted section or course | high |
| In the targeted programme, intake or school | medium |
| Insight topic matches the student's interests | raises |
| Insight info type matches the student's information preferences | raises |
| Info type the student switched off | lowers strongly |
| Student marked similar insights "not relevant" *[Later]* | lowers |

**Tier rules:**

| Tier | Rule |
|---|---|
| Direct attention | The student is mentioned |
| Action required | `action_required` and relevance above the threshold |
| Important update | Importance ≥ 70 and relevance above the threshold. A timetable change for one of the student's own sections is **always** an important update. |
| Digest | Relevance above the lower threshold |
| Not surfaced | Below the lower threshold (still searchable) |

Every delivery stores a short **reason** shown to the student, for example "You are in CDE2313 Section A" or "Matches your interest: Artificial Intelligence".

**Built (M7.4):** `apps/intelligence/delivery.py`, run when an insight is published, after names are matched, and when a forwarded copy adds evidence (it never undoes read or dismissed).
- **Who:** mentioned students; for a `direct_request`, **only** the mentioned students: it is about them, so nobody else gets it, not even in the digest, and nobody at all if no name could be matched (M9.17); for timetable changes, the students of the affected sections or course; otherwise the audience plus the members of every group the insight came from. Being in the group never beats what the message says: an insight for certain courses skips students who saved this term's timetable without any of them (M9.18), and one for a school, programme, intake or semester range skips group members outside it (M9.19). Students with no timetable, or an incomplete profile, still get it, since UniFlow can't tell. An AI insight with no audience goes to those members only; a staff post with no audience goes to every student. Never staff.
- **Score:** the strongest reason: named 100, your section 90, your course 85, your group 80, your programme 65, intake 60, school or semester range 55, everyone 40; then +10 for a shared interest (it becomes the reason when the base is weak), +10 for an information type the student chose, −40 for one they left out (an empty choice means everything).
- **Level:** named → `direct`; a timetable change for your own section or course → `important`; below 30 → not shown; unsure (0.5–0.8) → `digest` only; must act and score ≥ 50 → `action`; importance ≥ 70 and score ≥ 50 → `important`; otherwise `digest`.

### 7. Notify

See [07](07-notifications.md). Direct attention, action required and important updates notify immediately; the digest is sent once a day.

## Timetable intelligence

```
 insight kind class_moved / class_cancelled / room_changed / extra_session
   └─► ClassChange (proposal: section, meeting, date, new time/room, evidence)
         └─► for each affected student: ClassChangeConfirmation (pending)
               └─► student sees "Proposed change" with the original message
                     ├─ Confirm → their timetable shows the change on that date
                     └─ Reject  → nothing changes for them
```

- The official weekly timetable is never edited by the AI.
- A student's view of a day = official meetings + their **confirmed** changes.
- Pending proposals appear on the timetable page as a banner with the evidence, and in the feed as an important update.
- If the insight is retracted (in the admin now; from a later message such as "sorry, class stays at 10" from M7), its proposals are marked `retracted` and leave every timetable; confirmed students are told (M8).
- **Built (M5.7):** `apps/timetable/changes.py`. Publishing a timetable insight (`publish_insight`) creates one proposal per section; a student's answer is saved only when they confirm or reject. A moved class with only a new start keeps its length. A draft (for example an unknown course) has no proposal until it is published.

## Reading timetables

At the start of a semester, timetables are shared in groups as images, PDFs, spreadsheets or Google Drive links, and students can also upload one themselves.

```
 timetable image / PDF / spreadsheet / Google Drive link
   (shared in a group, or uploaded or pasted by a student on the Timetable page)
   └─► AI (a model that can read images and PDFs) → rows: course code, course name,
       section, day, start, end, room, lecturer
         └─► TimetableImport (status "ready") shown to the student: "Is this your timetable?"
               ├─ the student fixes any wrong row, removes classes they don't take, then Confirm
               │    └─► import service (dry run, then apply): creates missing courses, sections
               │        and weekly classes, enrols the student; never overwrites existing ones
               └─ Discard → nothing is saved
```

- **Google Drive links:** only public ("anyone with the link") files are read. UniFlow downloads them as PDF or spreadsheet; private files are reported as "can't open this link".
- **Spreadsheets** are converted to text before being sent to the model (`openpyxl`).
- **PDFs** are sent as they are, together with their grid as text (`pdfplumber`): every cell is numbered by its column, so the model matches a class to the time with the same number in the header row instead of judging it by eye. This matters when the time columns have different widths. A scanned PDF has no grid to take out and is read as a picture, like an image.
- **One file, many batches:** staff usually share one Google Sheet per school (for example SCI), with **one tab per batch** (programme and intake). Downloading it as Excel keeps every tab. The AI reads **each tab once per file**, and the result is reused for every student, so a school-wide file costs one reading, not one per student.
- Each student is shown **the tab that matches their programme and intake** (matched by the tab's name); they can switch to another tab if the guess is wrong. Only the classes they confirm are saved for them.
- A timetable shared in a group creates a ready import for each **member** of that group who has no sections yet, so most students only need to press Confirm.
- **Built (M6.5):** when a file from a group message is saved (Telegram or the WhatsApp connector), `offer_to_group` finds the members (students who added the group) without classes this term. Only if there are any does the AI read the file (once, stored on the file); a file with no classes, such as a poster photo, is ignored. Each of those members gets one ready import with the tab matching their programme and intake, shown on the Timetable page as "A timetable was shared in *group*".
- Once one student has confirmed a section, other students simply pick it (or confirm it from their own import); nobody has to type it again.
- If an import disagrees with classes that already exist, the existing classes stay and the difference is shown to the admin.
- Fallback: a student can add a missing class by hand.

## Direct mentions

- Names are matched against students' full names and their optional aliases (nicknames they add in their profile), **among the members of that group first** (`SourceMember`), then within the source's scope. "Abdulaziz, please come to the dean's office" in a group with one Abdulaziz is a clear mention.
- WhatsApp @-mentions are matched by the name shown in the message, like any other name; UniFlow never uses phone numbers.
- A name that matches two people in the group is **not** a mention; it becomes a normal insight.
- A matched mention creates a `direct_request` insight and an immediate notification.
- **Built (M7.2):** `apps/intelligence/mentions.py`. For each name the AI copied from a `direct_request`, plain code looks among the students who added the group, then among the students the group is for (its school, programme, intake, course or section); a group with no scope is never searched beyond its members. A name matches when all its words are words of the student's full name ("Ali" → "Ali Hassan"; titles such as "Bro", "Sis", "Dr" are ignored) or it equals one of their nicknames. Two possible students at the first place found → no mention, and the search stops there. **M9.20:** in a group with no scope, a one-word name (a first name or a one-word nickname) is never a mention: UniFlow only knows the members who use it, so "Abdulaziz" could be another student in the group; the message must give at least two words of the name ("Abdulaziz Taju"). Each match is an `InsightMention`; the notification comes with M8.

## Summaries

- Every insight has a one-sentence summary written by the model.
- The daily digest groups digest-tier insights by info type.
- *[Later]* "What did I miss?" summaries on demand.

## AI provider

- All model calls go through **one small module**, `apps/intelligence/providers.py`, with a single interface (`triage(messages)`, `extract(window, context)`). The rest of the code never imports a vendor SDK.
- **Model fallback (free tier, October 2026):** the code asks `ask("fast" | "smart", …)`, and the provider tries the models of `AI_FAST_MODELS` / `AI_SMART_MODELS` in order. On Gemini's free tier each model has its **own daily allowance**. A model that answers "too many requests" rests for as long as Google's `retryDelay` says (in the cache), and a busy one (500/503) for a minute; the next model answers instead. Only when every model of the list is resting is `AIRateLimited` raised, and the background job (Inngest) waits as long as the soonest model needs (at most an hour). Each insight records the model that actually answered (`model_version`). Defaults, checked with a new free key: fast `gemini-3.1-flash-lite`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite-preview`, `gemini-flash-lite-latest`; smart `gemini-3.5-flash`, `gemini-3-flash-preview`, `gemini-flash-latest`. `manage.py check_ai` tries every listed model. Backup models may be less accurate: compare them with `evaluate_intelligence`.
- **Gemini** (Google), through Google's official `google-genai` library, chosen by the developer in M5.1:
  - `AI_FAST_MODEL` = **`gemini-3.1-flash-lite`** for triage ("is this message academic?"),
  - `AI_SMART_MODEL` = **`gemini-3.5-flash`** for understanding messages and reading timetable images, PDFs and sheets.

  These are the **oldest models that still work for a new key** (checked in M5.3: the Gemini 2.5 models answer "no longer available to new users"), because on the free tier older models usually allow many more requests than the newest ones (the developer's experience; the exact limits are shown per project in Google AI Studio). Both are settings, so other models can be used without code changes. Answers are requested as JSON matching a schema (`ask_json`).
- **Free tier for now (developer's choice).** On Gemini's free tier, Google may use what is sent to improve its products ("Used to improve our products: Yes"; the paid tier says "No"). Decide on the paid tier before real students' messages are processed.
- **Limits:** the free tier has per-minute and daily request limits (shown in Google AI Studio). When Gemini answers "too many requests", `providers.AIRateLimited` is raised and Inngest tries the job again later (at least 1, 2, 4… minutes).
- Tests never call Gemini: `AI_PROVIDER = "fake"` uses `providers.FakeProvider` with prepared answers. `manage.py check_ai` sends one tiny question to each model to check the key.
- Messages can be in English, Malay, Arabic or a mix; the model handles this, and summaries are written in English.
- Reading timetables needs a model that accepts images and PDFs (Gemini Flash models do).

## Quality and evaluation

- An **evaluation set** of real, anonymized messages with the expected results is kept in the repository (`apps/intelligence/tests/eval/`). A command runs the pipeline against it and reports accuracy per kind. It is re-run when prompts or models change.
- **Built (M5.9):** `pipenv run python manage.py evaluate_intelligence` (add `--only changes` or `--only timetables`). The set starts with 15 made-up conversations in the style of AIU groups (every change kind, plus a rumour, a question, an "ignore the rules" message, a change taken back, and an answer that needs the question before it) and 2 timetable sheets (grid and list layouts). It prints OK or WRONG for each example, then right/total per kind. Nothing is saved.
- Unit tests never call the real provider: the provider module is replaced by a fake that returns fixed outputs.
- In the pilot, you check drafts and fix or retract insights in the **Django admin**; corrections are recorded (`corrected_by`) and added to the evaluation set. React review pages come after the pilot.

## Cost control

- Only connected **academic** groups are processed.
- Triage drops most messages before the expensive step.
- Messages are processed in batches per source, not one call per message.
- Relevance is computed by code, not by the model.
- *[With a paid tier]* a daily spend limit in settings pauses processing (with an alert to admins) if exceeded. On the free tier, Google's own limits apply.
