# 01 — Product Definition

> **Legend used throughout the docs:** **[MVP]** means it is built in the milestones of [11-roadmap.md](11-roadmap.md) before the first release. **[Later]** means it is designed and documented but not built until after the MVP.

## 1. Product definition

**UniFlow is an AI-powered student information assistant.**

It continuously processes the university's academic communication channels (WhatsApp groups, Telegram groups and channels, and official staff posts), understands what information matters to each student, and brings that information into one personalized place.

> **Core promise:** "No fluff. No information overload. Just the information that matters to you."

**Central objective:** students should not need to manually check dozens of academic WhatsApp and Telegram groups every day to stay informed.

UniFlow is **not primarily a portal or a content-management system**. It is an **information intelligence layer** between university communication channels and students. It understands information, filters noise, identifies what matters, and delivers personalized updates in one place.

### The problem

University information is fragmented across many groups: programme, intake, course, section, school and university-wide groups, Telegram channels and other academic channels. Students belong to many of them at once.

Important information is hidden inside large conversations with hundreds of unrelated messages, so students miss things such as:

- internship opportunities, bootcamps and industry visits,
- academic and student-affairs announcements,
- timetable changes, class cancellations and room changes,
- mandatory events,
- requests directed at specific students ("Abdulaziz, please come to the dean's office").

### What UniFlow does

For every connected source, the AI:

1. understands **conversation context**, not just single messages,
2. determines **who is affected**,
3. determines **relevance** for each student,
4. determines **importance**,
5. detects **action-required** items,
6. detects **timetable-related** updates,
7. detects **direct mentions** of individual students,
8. writes short **summaries**,
9. links every insight back to its **original source**.

How this works is described in [12-intelligence.md](12-intelligence.md).

### Product positioning

```
                 ┌──────────────────────────────────────────────────┐
 Communication   │  WhatsApp / Telegram groups and channels         │  students keep talking here
 (conversation)  │  (programme, intake, course, section, school…)   │
                 └───────────────────────┬──────────────────────────┘
                                         │ connected sources (read)
                 ┌───────────────────────▼──────────────────────────┐
 Intelligence    │  UniFlow                                         │  ← UniFlow
                 │  understand → who is affected → relevance and    │
                 │  importance → personal feed, timetable, alerts   │
                 └───────────────────────┬──────────────────────────┘
                                         │ one personalized place
                                      Students

 Not UniFlow:  the LMS / Student Hub (grades, submissions), and chat itself.
```

UniFlow does **not** replace WhatsApp or Telegram. Students keep using them to talk. UniFlow removes the need to *monitor* them.

## 2. Key concepts

### Personalization

Every student has:

| Kind | Examples | Where it is stored |
|---|---|---|
| **Academic context** | School, programme, intake, semester, courses, sections | `StudentProfile` and `SectionEnrollment` ([03](03-data-model.md)) |
| **Interest preferences** | Artificial Intelligence, Data Science, Software Engineering, Cybersecurity, Networking | `StudentProfile.interests` |
| **Information preferences** | Internships, bootcamps, industry visits, competitions, academic notices, student-affairs updates | `StudentProfile.info_types` |

Both academic context and preferences decide what is surfaced.

### Relevance and importance are separate

| Concept | Meaning | Decided for |
|---|---|---|
| **Relevance** | How much a piece of information applies to *this* student | Each (insight, student) pair |
| **Importance** | How urgent or significant the information is | Each insight |

Examples:

- A cybersecurity workshop: medium importance, **low relevance** for a student interested only in AI.
- A direct message from the dean to a student: **very high relevance and importance** for that student.
- A timetable change for the student's own class: **high relevance and high importance**.

### Priority tiers

Every insight a student receives is placed in one tier:

| Tier | Meaning | Examples | Notification |
|---|---|---|---|
| **Direct attention** | Directed at this specific student | "Abdulaziz, please come to the dean's office" | Immediate |
| **Action required** | The student should do something | Apply for an internship, register for an industry visit, attend a mandatory briefing | Immediate if relevant and important, otherwise in the feed |
| **Important update** | Significant change affecting them | Timetable change, class cancellation, room change, major academic announcement | Immediate |
| **Digest** | Lower priority, summarized | General notices, events outside their interests | Daily digest only |

Anything below the student's relevance threshold is not surfaced, but stays searchable.

### Timetable intelligence

The timetable represents **the student's current reality**, not only the original university timetable.

1. The official timetable (terms, courses, sections, weekly classes) is the baseline.
2. When a message says a class moved, was cancelled, changed room, or that a mandatory academic session was added, the AI **proposes** a change.
3. UniFlow shows the student **the evidence** (the original message, its group and time).
4. **The student confirms or rejects.** The AI never changes a timetable by itself.
5. After confirmation, the student's timetable shows the change.

### Direct mentions

When a message names a specific student (by name, known nickname or phone number), UniFlow notifies that student **immediately**, with access to the original message.

### Every insight links to its source

Every card, summary and notification shows where it came from (group or channel, sender, time) and lets the student open the original message.

## 3. Information sources

Messaging platforms are **primary information sources**, not just links in a directory.

| Source | How UniFlow reads it | Detail |
|---|---|---|
| **WhatsApp groups** | The **UniFlow WhatsApp connector**: a dedicated UniFlow WhatsApp number joins academic groups through invite links that students submit | An unofficial connector, chosen knowingly. Risks and safeguards in [08](08-messaging-integrations.md). |
| **Telegram groups and channels** | The official **UniFlow Telegram bot**, added by the group or channel admin | Official Bot API |
| **Staff posts** | Authorized staff post directly in the staff dashboard | An **official** source with the highest trust |
| **Manual input** | Pasting a message, or uploading a WhatsApp "Export chat" file | Useful before connectors exist, and as a fallback |

Students **connect** a group by submitting its invite link. A group is connected once and shared: every student in it benefits.

## 4. Scope

### In scope: academic and university information only

Internships, bootcamps, industry visits, competitions, academic announcements, student-affairs notices, timetable updates, class changes and mandatory academic events.

### MVP

| Area | In the MVP |
|---|---|
| Authentication and profile | University-email registration, activation, login, password reset; onboarding for school, programme, intake and semester (done in M1) |
| Academic structure | Schools, programmes, intakes, courses, terms, sections, weekly class meetings; students choose their sections |
| Preferences | Interests and information types, chosen at onboarding and editable |
| Sources | Connecting WhatsApp and Telegram groups, staff posts, manual paste and chat-export upload |
| Intelligence | Understanding messages in context, insights with importance, per-student relevance and tiers, action detection, timetable detection, direct mentions, summaries, source links, duplicate merging |
| Timetable | Official baseline plus AI-proposed changes the student confirms; today and week views |
| Personal feed | One home screen with the four tiers, plus search |
| Notifications | In-app: immediate for direct attention, action required and important updates; a daily digest |
| Staff and admin | User management, reference data, source management, reviewing and correcting insights, official staff posts |

### Later

| Area | Later |
|---|---|
| Notifications | Push notifications (React Native app), email digests, per-tier quiet hours |
| Sources | Attachments and images from messages (posters, PDFs), voice notes, more platforms |
| Intelligence | Learning from student feedback ("not relevant"), per-student summaries on demand ("what did I miss this week?") |
| Timetable | Official import adapters (once the university's format is known), lecturer-confirmed changes, ICS export |
| Directories | Document library, applications directory and community directory as browsable lists (the information itself already reaches students through insights) |
| Platform | React Native app, S3 storage, full-text search, audit log, data export and account anonymization, SSO |

### Out of scope

| Out of scope | Why |
|---|---|
| Marketplaces, buying and selling, room rentals | Not academic information |
| Casual social conversation and entertainment groups | Not academic information. UniFlow only connects academic groups. |
| Reading students' personal (one-to-one) chats | Never. Only groups and channels that were explicitly connected. |
| Replacing chat | Students keep talking in WhatsApp and Telegram |
| Grades, submissions, official enrolment | The LMS and Student Hub already do this |
| Changing a timetable without the student's confirmation | Trust: messages can be wrong, old or jokes |
| Infrastructure without a demonstrated need (Redis, Celery, Docker, Kubernetes, Elasticsearch, microservices) | Complexity without benefit at this scale. Background work uses a database job table (see [02](02-system-architecture.md)). |

## 5. User roles

Every user has exactly **one role**.

| Role | What they do |
|---|---|
| `student` | Receives the personal feed, confirms timetable changes, sets preferences, connects groups, chooses sections |
| `lecturer` | Read-only in the MVP. *[Later]*: confirm changes for the sections they teach, post to them. |
| `school_staff` | Posts official information for their own school, and reviews and corrects insights from their school's sources |
| `university_admin` | Everything school staff do, for every school; manages sources and reference data |
| `super_admin` | Everything, plus staff accounts, roles, suspension and the Django admin |

## 6. Feature breakdown

| # | Feature | MVP |
|---|---|---|
| F1 | Auth and profile | Djoser registration (university domain), activation, JWT login, password reset and change, onboarding (done) |
| F2 | Academic structure and sections | Courses, terms, sections, class meetings; students choose sections |
| F3 | Preferences | Interests and information types |
| F4 | Sources and connectors | WhatsApp connector, Telegram bot, staff posts, manual paste and chat-export upload; connecting a group |
| F5 | Intelligence pipeline | Triage, conversation-aware extraction, insights, duplicate merging, direct mentions ([12](12-intelligence.md)) |
| F6 | Relevance and tiers | Per-student relevance, the four tiers, reasons ("because you are in CDE2313 section A") |
| F7 | Timetable intelligence | Proposed changes with evidence, student confirmation, the student's current timetable |
| F8 | Personal feed | Home feed by tier, insight detail with source, "not relevant" feedback, search |
| F9 | Notifications | Immediate in-app alerts and the daily digest |
| F10 | Staff and admin | Users, reference data, sources, insight review, official posts |

## 7. Decisions already made that stay

- The stack: Django + DRF + MySQL backend, React web app now, React Native later, one `/api/v1/` for every client.
- All logic lives in the backend. The frontend is never the security boundary.
- Accounts: only `@student.aiu.edu.my` can self-register; staff accounts are created by a super admin.
- AIU is organized into **Schools**; a Programme is a degree; a Course is a subject (for example CDE2313).
- Minimal infrastructure: no Redis, Celery or Docker for now.
