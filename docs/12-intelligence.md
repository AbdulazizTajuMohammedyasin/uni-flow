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

Each step runs as a **Celery job** (see [02](02-system-architecture.md#background-jobs)), so a slow or failed AI call never blocks a web request, and failed steps are retried.

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
- If a later message retracts the change ("sorry, class stays at 10"), the proposal is marked `retracted` and pending confirmations are withdrawn; confirmed students are told.

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
- **Spreadsheets** are converted to text before being sent to the model.
- A timetable shared in a group creates a ready import for each **member** of that group who has no sections yet, so most students only need to press Confirm.
- Once one student has confirmed a section, other students simply pick it (or confirm it from their own import); nobody has to type it again.
- If an import disagrees with classes that already exist, the existing classes stay and the difference is shown to the admin.
- Fallback: a student can add a missing class by hand.

## Direct mentions

- Names are matched against students' full names and their optional aliases (nicknames they add in their profile), **among the members of that group first** (`SourceMember`), then within the source's scope. "Abdulaziz, please come to the dean's office" in a group with one Abdulaziz is a clear mention.
- WhatsApp @-mentions are matched by the name shown in the message, like any other name; UniFlow never uses phone numbers.
- A name that matches two people in the group is **not** a mention; it becomes a normal insight.
- A matched mention creates a `direct_request` insight and an immediate notification.

## Summaries

- Every insight has a one-sentence summary written by the model.
- The daily digest groups digest-tier insights by info type.
- *[Later]* "What did I miss?" summaries on demand.

## AI provider

- All model calls go through **one small module**, `apps/intelligence/providers.py`, with a single interface (`triage(messages)`, `extract(window, context)`). The rest of the code never imports a vendor SDK.
- **Proposed:** Anthropic Claude through the official `anthropic` Python SDK, using a small, fast model for triage (Claude Haiku 4.5) and a stronger model for understanding (Claude Sonnet 5), with structured output (tool use or JSON schema). **The library and the provider are approved in the task that first needs them**, as with every dependency.
- Every insight records the model and prompt version that produced it.
- Messages can be in English, Malay, Arabic or a mix; the model handles this, and summaries are written in English.
- Reading timetables needs a model that accepts images and PDFs (the proposed Claude models do).

## Quality and evaluation

- An **evaluation set** of real, anonymized messages with the expected results is kept in the repository (`apps/intelligence/tests/eval/`). A command runs the pipeline against it and reports accuracy per kind. It is re-run when prompts or models change.
- Unit tests never call the real provider: the provider module is replaced by a fake that returns fixed outputs.
- In the pilot, you check drafts and fix or retract insights in the **Django admin**; corrections are recorded (`corrected_by`) and added to the evaluation set. React review pages come after the pilot.

## Cost control

- Only connected **academic** groups are processed.
- Triage drops most messages before the expensive step.
- Messages are processed in batches per source, not one call per message.
- Relevance is computed by code, not by the model.
- A daily spend limit in settings pauses processing (with an alert to admins) if exceeded.
