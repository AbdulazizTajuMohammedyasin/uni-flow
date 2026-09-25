# 01 — Product Definition

> **Legend used throughout the docs:** **[MVP]** means it is built in milestones M0–M10. **[Later]** means it is designed and documented but not built until after the MVP.

## 1. Product definition

**UniFlow is the single place a student opens to find out what is happening on campus.**

Today, campus information is scattered across dozens of WhatsApp groups and channels, Telegram groups and channels, university and school notices, club pages and posters. Students have to check many places, miss important things, and cannot tell what matters from what is noise.

UniFlow organizes that information. It does not replace where it was created. Authorized staff publish information to UniFlow once, through the UniFlow **staff dashboard**. The backend decides who it is relevant to. Every client (the web app now, a React Native app later) shows each student the part that applies to them.

When students open UniFlow, they should be able to answer these questions within seconds:

| Question | Answered by |
|---|---|
| What is important right now? | Pinned and important announcements |
| What has just been published? | The recent announcements and documents |
| What is coming up? | Upcoming events |
| What classes do I have today or this week? | Timetable |
| Which groups and communities should I be in? | Community directory with WhatsApp and Telegram links |
| What can I apply for right now? | Open applications and forms |
| Where is the document everyone keeps asking about? | Document library |

### Product positioning

```
                 ┌───────────────────────────────────────────┐
 Academic work   │  Student Hub / LMS / Academic portal      │  ← NOT UniFlow
 (grades, subs,  │  grades, submissions, deadlines, courses  │
  deadlines)     └───────────────────────────────────────────┘
                 ┌───────────────────────────────────────────┐
 Communication   │  WhatsApp / Telegram                      │  ← NOT UniFlow
 (conversation)  │  discussion, chat, replies                │    (UniFlow links to them)
                 └───────────────────────────────────────────┘
                 ┌───────────────────────────────────────────┐
 Information     │  UniFlow                                  │  ← UniFlow
 (what's on,     │  announcements, events, timetable view,   │
  where, links)  │  communities directory, forms, documents  │
                 └───────────────────────────────────────────┘
```

UniFlow is an **information layer**. WhatsApp and Telegram remain the places where students talk. UniFlow links students to them. It also links out to the Student Hub and to official application portals instead of copying what they do.

## 2. Scope

### MVP (milestones M0–M10)

| Area | In the MVP |
|---|---|
| Authentication | Registration restricted to university email domains, email activation, JWT login, refresh and logout (the web app keeps the refresh token in an httpOnly cookie), password reset and change |
| Profile and onboarding | Students choose their school, programme and intake, and can edit their profile |
| **Staff dashboard (React)** | Authorized staff create, edit, publish and archive announcements, events, documents, applications, communities and timetable data. Staff see only the actions their role allows. |
| Student dashboard | One personalized home page |
| Announcements | Categories, `normal` or `important` priority, pinning, audience targeting, attachments, optional expiry, source link |
| Events | List view, month calendar, poster, location, organizer, registration link, audience targeting |
| Timetable | Timetable data comes from the university and is maintained by staff. Students select their sections and see today's and this week's classes. |
| Communities | Directory with WhatsApp, Telegram and web links, filters, follow and unfollow |
| Applications and forms | Listings with opening and closing dates, a derived status and an external link |
| Documents | A library of documents any logged-in user can download, and attachments |
| Notifications | In-app notifications for important announcements and new events |
| Search | Filters and `?search=` on every list, plus a simple global search |
| Django admin | A **back-office tool for developers and super admins only**. It is not the staff interface. |

### Later (documented, not built in the MVP)

| Area | Later |
|---|---|
| Publishing | Community managers (such as club leaders) publishing for their community, lecturer publishing, an approval workflow for community posts, scheduled publishing |
| Targeting | Course, section, community-follower and semester targeting, and audience targeting for documents |
| Notifications | Reminders (such as "applications closing soon"), timetable and event change notifications, push (Expo), email digests, per-user preferences |
| Timetable | Automated import adapters (the format is not yet known), one-off class cancellations or room changes, ICS export, lecturer edits |
| Content | Read tracking, event "interested" markers, ICS export, document versioning |
| Integrations | A Telegram bot that pulls posts from the university's own channels into a review inbox, and optional posting from UniFlow to a Telegram channel |
| Platform | React Native app, S3 storage, full-text search, audit log, data export and account anonymization, SSO |

### Out of scope (not planned)

| Out of scope | Why |
|---|---|
| Assignment or project deadlines, submissions and grades | The LMS and Student Hub already do this. A deadline that appears *inside* an announcement is just text. |
| Other LMS or Student Hub functions, including official enrolment | Those systems already exist. The UniFlow timetable is informational only. |
| Internal chat | WhatsApp and Telegram already do this. UniFlow links to them. |
| Scraping WhatsApp or Telegram, unofficial APIs, automatic ingestion from them | It breaks the platforms' terms. See [08](08-messaging-integrations.md). |
| Processing applications | Official form systems already do this. UniFlow only lists and links. |
| RSVP and ticketing | Events link to an external registration URL instead. |
| AI features, complex recommendation systems | Premature. |
| Infrastructure without a demonstrated need (Redis, Celery, Docker, Kubernetes, Elasticsearch, microservices) | It would add complexity without a matching benefit at this scale. |

## 3. User roles

Every user has exactly **one role**.

| Role | MVP permissions | Later |
|---|---|---|
| `student` | Read content targeted at them, manage their profile and timetable sections, follow communities, receive notifications | Can also publish if they are a community manager |
| `lecturer` | **Read-only** (the same as a student, plus they can see all published content) | Publish to the sections they teach, edit their own timetable entries |
| `school_staff` | Use the staff dashboard to manage announcements, events, documents, applications, communities and timetable data that **belong to their own school and are targeted within it**. They cannot target all students or another school. | A university admin may explicitly grant wider reach |
| `university_admin` | Manage content across all schools and for the university as a whole, send it to any audience, and archive any item | Manage community managers, and grant wider reach to school staff |
| `super_admin` | Everything, plus assigning roles, suspending users and using the Django admin | |

**Community manager [Later]** will be a per-community permission rather than a role. For example, a student who leads the Robotics Club would stay a `student` and be recorded as that club's manager.

## 4. Feature breakdown

| # | Feature | MVP | Later |
|---|---|---|---|
| F1 | Auth and profile | Djoser registration limited to university email domains, activation, JWT login with the web cookie, password reset and change, onboarding, the "me" endpoint | Self-service account deletion (anonymized), SSO |
| F2 | Student dashboard | One aggregated endpoint and page | Personalization |
| F3 | Announcements | Student feed, detail, filters; staff create, edit, publish, archive; targeting; attachments; pinning; expiry; source link | Read tracking, scheduling, approval workflow |
| F4 | Events | Student list, calendar and detail; staff create, edit, publish, archive; poster; registration link | "Interested" markers, ICS export, change notifications |
| F5 | Timetable | Terms, courses, sections and weekly meetings maintained by staff; students select sections; today and week views; an import service that works with any file format | The first import adapter (once the university's format is known), one-off changes, lecturer edits |
| F6 | Communities | Directory, links, follow; staff manage communities | Community managers, publishing as a club, follower targeting, a Telegram bot connection |
| F7 | Applications and forms | Listings with a derived status; staff management | Reminders |
| F8 | Documents | Library, logged-in-only download, file checks, attachments; staff management | Targeting, versioning, S3 |
| F9 | Notifications | In-app notifications for important announcements and new events: bell, list, mark as read | Push, email, reminders, preferences |
| F10 | Search | Filters on every list, plus a global `/search/` | Full-text search |
| F11 | **Staff dashboard** | A `/staff` area in the React app. Its navigation and actions depend on the user's permissions. | Community-manager views |
| F-INT | Messaging integrations | Deep links, source attribution, manual publishing through the staff dashboard | Telegram bot inbox, outbound posting |

### Shared behaviours for content

Announcements, events, documents and applications all share these behaviours, and they are implemented once:

- **Publisher [MVP].** Content is published on behalf of the `university` or a `school`. This is separate from the user who typed it. The publisher decides who may manage the item and what byline students see. The `community` publisher type comes later.
- **Audience [MVP].** Who the content is for: all students, or specific schools, programmes or intakes. Documents have no audience in the MVP, so every logged-in user can see them. See [03](03-data-model.md#audiences--audience-targeting).
- **Lifecycle [MVP].** Content moves from `draft` to `published` to `archived`. Publishing takes effect immediately and sets `published_at`. An optional `expires_at` hides the item once it passes. Scheduled publishing comes later.
- **Source [MVP].** An optional `source_platform` and `source_url` point to the original WhatsApp or Telegram post, portal page or other source.
