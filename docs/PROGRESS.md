# UniFlow Progress

This is the **simple overview** of where UniFlow is. It is updated after every task.
(The detailed plan is [11-roadmap.md](11-roadmap.md). You do not need to read it to follow progress.)

**What UniFlow is (updated after M2.8):** an **AI assistant** that reads academic WhatsApp and Telegram groups, works out what matters to each student, and shows only that, in one place. *"No fluff. No information overload. Just the information that matters to you."* See [01-product.md](01-product.md).

**Now:** M3.4 is done ✅. UniFlow knows each student's **semester** (worked out from their intake) and their **interests** and **information types**; a message can be aimed at "Year 2" (semesters 4–6).
**Next up:** M3.5, the student API for sections: list the sections, "my sections", and add a missing class by hand.

---

## The big picture

| Milestone | In plain words | Status |
|---|---|---|
| **M0** Foundations | Set up the empty backend and website so they run and are checked automatically | ✅ Done |
| **M1** Identity | Students can register, log in and fill in their profile | ✅ Done |
| **M2** Permissions | Who is allowed to do what, "who is affected by a post", and the staff dashboard frame | ✅ Done (M2.9–M2.11 moved to later milestones) |
| **M3** Classes and preferences | UniFlow learns each student's courses, sections and interests (the semester is worked out from the intake); students see their timetable and can add a class | 🔄 In progress |
| **M4** Messages | UniFlow can store messages and timetable files from groups (pasted, uploaded, WhatsApp "Export chat", Google Drive links) | ⏳ |
| **M5** AI, first version | The AI **reads a shared timetable** and the student confirms it; the AI spots "class moved / cancelled / room changed" and the student confirms; their timetable updates | ⏳ |
| **M6** Connectors | Students add their groups in the app, and UniFlow's own WhatsApp number joins them in the background | ⏳ |
| **M7** AI, full version | Internships, notices, mentions of your name, and the personal "For you" feed with 4 levels | ⏳ |
| **M8** Notifications | Alerts inside UniFlow only for what matters to you, plus a daily summary (phone alerts come with the mobile app) | ⏳ |
| **M9** Pilot | Home screen, search, privacy notice, putting it online, and testing with a small group of real students (you check things in the Django admin) | ⏳ |
| **M10** Staff pages | After the pilot: pages for staff to check groups, fix AI mistakes and post official news | ⏳ |

---

## M0 Foundations: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M0.1 | Repository rules: line endings, ignored files | – | ✅ Done |
| M0.2 | Database: you created the `uniflow` MySQL database yourself | MySQL Workbench | ✅ Done |
| M0.3 | Created the empty Django backend | – | ✅ Done |
| M0.4 | Connected Django to MySQL, with passwords in `backend/.env` | `pipenv run python manage.py check` | ✅ Done |
| M0.4a | Switched to Pipenv for Python packages | `pipenv --venv` | ✅ Done |
| M0.5 | Automatic backend tests and code checks (pytest, ruff) | `pipenv run pytest` | ✅ Done |
| M0.6 | User accounts: log in with email, each user has a role | `/django-admin/` | ✅ Done |
| M0.7 | The API "doorway" at `/api/v1/`, with a health check | http://127.0.0.1:8000/api/v1/health/ | ✅ Done |
| M0.8 | GitHub checks the backend automatically on every push (CI) | GitHub → **Actions** tab | ✅ Done |
| M0.9 | Created the empty React website | `npm run dev` → http://localhost:5173 | ✅ Done |
| M0.10 | Styling with Tailwind (colours, fonts) | The styled page | ✅ Done |
| M0.11 | Automatic website tests (Vitest) | `npm test` | ✅ Done |
| M0.12 | Pages and addresses (`/`, `/login`, `/staff`, 404) plus the page frames | Click the menu links. Try a phone-size view. | ✅ Done |
| M0.12a | Added **shadcn/ui** (ready-made buttons, dialogs and so on) with UniFlow's indigo colour. It is used on the 404 page's button. | http://localhost:5173/anything → "Go to home" button | ✅ Done |
| M0.13 | The website can talk to the backend. A small **API: ok** badge proves it. | Run both servers; see the badge in the sidebar | ✅ Done |
| M0.14 | GitHub checks the website automatically too (CI) | GitHub → **Actions** → Frontend CI | ✅ Done (green) |

---

## M1 Identity: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M1.1 | Database tables for AIU's structure: **schools**, **programmes** (degrees) and **intakes** (batches). The role "department staff" was renamed **school staff**, because AIU uses schools. | `/django-admin/` → Academics | ✅ Done |
| M1.2 | The website can read schools, programmes and intakes through the API (for the sign-up dropdowns). They are login-only, so for now they answer "403". | http://127.0.0.1:8000/api/v1/docs/ → **academics** | ✅ Done |
| M1.3 | Loads AIU's real list (3 schools, the Foundation centre and 23 programmes) plus 8 intakes (March and October, 2023–2026) with one command | `pipenv run python manage.py seed_academics`, then `/django-admin/` → Academics | ✅ Done |
| M1.4 | Student profiles (student number, school, programme, intake) and staff profiles (school, job title). A student's programme must belong to their school. | `/django-admin/` → Users → open a user | ✅ Done |
| M1.5 | Students sign up with an `@student.aiu.edu.my` email. The account stays inactive until they click the activation email. On your computer, emails are printed in the backend terminal. | http://127.0.0.1:8000/api/v1/docs/ → **auth** → try `POST /auth/users/` | ✅ Done |
| M1.6 | Log in with email and password using **Djoser's standard login**. You get a 15-minute access token and a 14-day refresh token. | http://127.0.0.1:8000/api/v1/docs/ → **auth** → `jwt/create/`, then the **Authorize** button | ✅ Done |
| M1.7 | **Forgot password** (reset link by email, printed in the terminal on your PC) and **change password** (logged in, needs the current password). Both are Djoser's built-in features. | Swagger → **auth** → `users/reset_password/` | ✅ Done |
| M1.8 | **"My profile"** at `/api/v1/auth/users/me/`: your name, role and whether your profile is complete. Students can set their school, programme, intake and student number; the programme must match the school. | Swagger → **auth** → `users/me/` (click **Authorize** first) | ✅ Done |
| M1.9 | The website remembers who is logged in. The access token is kept only in memory, and the refresh token is in a **secure cookie** that page scripts can't read (nothing in `localStorage`). Pages are now **login-only**: visitors who aren't logged in go to `/login`. | http://localhost:5173 now redirects to `/login` | ✅ Done |
| M1.10 | **Log in** and **Register** pages. Register only accepts `@student.aiu.edu.my` and shows "check your email"; login sends you where you were going. | http://localhost:5173/register and `/login` | ✅ Done |
| M1.11 | The **links in emails now work**: the activation page (activates your account, or sends a new link if it's broken), **Forgot password?** and the reset-password page | Click the activation link from the backend terminal | ✅ Done |
| M1.12 | **Onboarding:** new students pick their school, then programme (only that school's), then intake. **Profile page:** your details, your studies, change password, log out. | Log in as a new student to see `/onboarding`, then the **Profile** link | ✅ Done |

---

## M2 Permissions and staff area: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M2.1 | **Who may manage what:** school staff manage their own school's content, university admins manage everything, and super admins can also manage users. "My profile" now lists these permissions and who you can publish as. | Swagger → `users/me/` (logged in) → `capabilities`, `publishers` | ✅ Done |
| M2.2 | **Staff user management:** a super admin lists users, creates staff accounts (the person gets a "set your password" email), changes roles and schools, and suspends users. A suspended user can't log in, and is logged out at once. | Swagger → **manage: users** (log in as a super admin first) | ✅ Done |
| M2.3 | **Reference data management:** university admins and super admins add, edit and switch off schools, programmes and intakes. Switched-off items disappear from students' dropdowns. Nothing is deleted. | Swagger → **manage: academics** (log in as a super admin first) | ✅ Done |
| M2.4 | **Audience:** a small record saying who a post is for: all students, or chosen schools, programmes and intakes. It can describe itself in a short line, e.g. "Computing · Intake October 2024". | `pipenv run python manage.py migrate` (new table); `pipenv run pytest apps/audiences` | ✅ Done |
| M2.5 | **Who sees what:** two checks that follow the same rules: "which posts may this student see?" and "which students is this post for?". Staff see everything; students who haven't finished onboarding only see posts for all students; suspended students are never notified. | `pipenv run pytest apps/audiences` | ✅ Done |
| M2.6 | **Shared base for posts:** every post (announcement, event, document, application) gets the same details: draft / published / archived, from the university or a school, who created it, and an optional expiry date. Plus the **Publish** and **Archive** actions, and the "is it live now?" check. | `pipenv run pytest apps/publishing` | ✅ Done |
| M2.7 | **Publisher rules (the school boundary):** admins manage every post; school staff only post **as** their school, **to** their school's students, and only see and edit their school's posts; lecturers manage nothing. | `pipenv run pytest apps/publishing` | ✅ Done |
| M2.8 | **Staff dashboard frame:** the `/staff` menu shows only the sections you may manage (school staff don't see Users; super admins do). Students and lecturers get a **No access** page. Staff get a **Staff dashboard** link in the student sidebar. The section pages are still "Coming soon". | Log in as `a@gmail.com` → **Staff dashboard** link → http://localhost:5173/staff. Log in as a student and open `/staff` → **No access**. | ✅ Done |
| M2.9 – M2.11 | *Moved.* Shared form pieces are built with the first pages that need them; the users and schools pages moved to M9 | – | ↪️ Moved |

---

## M3 Classes and preferences: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M3.1 | **Courses and terms.** A course is a subject (CDE2313) that belongs to a school. A term is a semester ("2025/26 Semester 1"); only one can be the current one, so ticking "current" on one un-ticks the others. The website can read them. | `pipenv run python manage.py migrate`, then `/django-admin/` → Academics → Courses / Terms. Swagger → **academics** → `courses/`, `terms/`, `terms/current/` | ✅ Done |
| M3.2 | **Sections and weekly classes.** A section is one group of a course in one term (CDE2313 Section A). Each section has weekly classes (day, start, end, room). A student can be in a section once. Each section remembers how it was added (by the AI, a student, an admin or a file). | `pipenv run python manage.py migrate`, then `/django-admin/` → **Timetable** → Course sections (add classes at the bottom of a section) | ✅ Done |
| M3.3 | **"Who is affected" by course and section.** A message for CDE2313 reaches students in a CDE2313 section **this term** (not last term's). A message for Section A reaches only Section A. School staff can only pick their own school's courses and sections. *Semester ("Year 2") moved to M3.4.* | `pipenv run python manage.py migrate`, then `pipenv run pytest apps/audiences` | ✅ Done |
| M3.4 | **Semester and interests.** The semester is worked out by **counting AIU's real terms** since the student's intake (three a year; the dates change every year, so they come from the official academic calendar, not fixed dates). An October 2025 intake is in Semester 1 from 27 Oct 2025, 2 from 23 Mar 2026 and 3 from 3 Aug 2026. Foundation students count AIU's **Foundation** terms instead. The official 2024/2025 and 2025/2026 terms of both calendars are loaded by the seed command; new terms are added in the Django admin. A student can set it by hand if that's wrong. Messages can target semesters ("Year 2" = 4–6). Students can save interests (AI, Cybersecurity, …), information types (internships, bootcamps, …) and nicknames. | `pipenv run python manage.py migrate`, then `pipenv run python manage.py seed_academics` (loads the terms) and tick the current term of each calendar in `/django-admin/` → Terms; Swagger → **auth** → `users/me/` and `preferences/choices/` | ✅ Done |
| **M3.5** | **Sections for students:** list sections, "my sections", add a missing class by hand | – | ⏭️ **Next** |

---

## Where things are

| I want to... | Look at |
|---|---|
| See what's done and what's next | **This file** |
| Run the backend | [backend/README.md](../backend/README.md) |
| Run the website | [frontend/README.md](../frontend/README.md) |
| Understand the whole design | [docs/README.md](README.md) |
| Understand how the AI works | [12-intelligence.md](12-intelligence.md) |

### Website files so far (`frontend/src/`)

| File or folder | Job |
|---|---|
| `main.tsx` | Starting point: turns on data loading (TanStack Query) and the router |
| `router.tsx` | **The router:** which address shows which page |
| `api/` | **Talking to the backend:** `client.ts` (the connection, which refreshes the login automatically), `auth.ts` (login, logout, who am I, profile, password), `academics.ts` (schools, programmes, intakes), `errors.ts` (reads errors), `health.ts` (health check), `tokenStore.ts` (the access token, in memory only) |
| `context/` | `AuthContext.tsx`: who is logged in (`useAuth()`) |
| `hooks/` | Data hooks for pages: `useAcademics.ts` (schools, programmes, intakes), `useHealth.ts` |
| `types/` | TypeScript shapes of API data: `academics.ts`, `auth.ts`, `health.ts` |
| `components/` | Page frames (`AppLayout`, `AuthLayout`, `StaffLayout`), `RequireAuth` (login-only pages, and sends new students to onboarding), `FormField` and `SelectField` (form inputs), `StudentDetailsForm`, `ChangePasswordForm`, `RequireCapability` (staff pages: "No access" if not allowed), `Can` (hides buttons you can't use), small boxes (`EmptyState`, `ErrorState`, `PageLoading`) and the dev-only `HealthBadge` |
| `components/ui/` | **shadcn** components (Button, Badge, Input, Label). Add more with `npx shadcn@latest add <name>`. |
| `pages/` | One folder per page: `Login/`, `Register/`, `ActivateAccount/`, `ForgotPassword/`, `ResetPassword/`, `Onboarding/`, `Profile/`, `NoAccess/`, `NotFound/`, `Placeholder/`, `RouteError/` |
| `lib/` | Helpers: `utils.ts` (shadcn), `queryClient.ts`, `navigation.ts` (the student and staff menu links), `capabilities.ts` (what the user may manage) |
| `index.css` | Colours and fonts |

### Backend files so far (`backend/`)

| File or folder | Job |
|---|---|
| `config/settings/` | Settings (dev, test, prod) |
| `config/api_v1.py` | The list of API addresses |
| `apps/accounts/` | User accounts, login, profiles, `capabilities.py` (who may manage what), `authentication.py` (blocks suspended users) and `manage_views.py` (staff user management) |
| `apps/academics/` | University structure: schools, programmes and intakes, and `manage_views.py` (admins edit them) |
| `apps/audiences/` | Who a post is for (`Audience`), and `selectors.py` (who sees what) |
| `apps/timetable/` | Sections, weekly classes and which students are in each section |
| `apps/publishing/` | The shared base for every post (status, publisher, expiry), the publish / archive actions, and `policies.py` (the school boundary) |
| `core/models.py` | Shared "created at / updated at" timestamps for every table |
| `core/` | Shared API pieces: the error format, paging and the health check |
| `.env` | Your local passwords (never committed) |

---

## Decided recently

- **UniFlow is an AI information assistant**, not a notice board. Messages from academic WhatsApp and Telegram groups are the main input. The AI **proposes**; normal code decides; the student **confirms** timetable changes.
- **WhatsApp:** an **unofficial connector** (a dedicated UniFlow number joins groups), chosen knowingly. Risks: WhatsApp's rules, the number can be banned, members' consent. Safeguards and details: [08](08-messaging-integrations.md). Telegram uses the official bot. Pasting and chat export always work too.
- **Staff posts stay** as one official source. The M2 code is kept and reused.
- **Background work** uses a simple database job table, still no Redis or Celery.
- **When the AI isn't sure:** sure → shown; unsure → daily summary marked "Not confirmed"; very unsure → hidden until you check it.
- **Staff posts and AI findings are one thing** in the code (no separate announcements part).
- **The normal timetable comes from the groups too:** the AI reads timetable images, PDFs and Google Drive links, and the student confirms before anything is saved.
- **Alerts stay inside UniFlow** for now; the mobile app will add phone notifications.
- **Fewer backend apps:** from now on a new app only when it's really needed. The groups, messages, AI and feed will be **one app** (`intelligence`) and alerts a second (`notifications`). Existing apps stay as they are.
- **Intakes are March and October** (the website only mentions October, but March is real).
- **Two term calendars:** Foundation students follow AIU's Foundation calendar (e.g. 13 Oct, 9 Feb, 8 Jun), everyone else the Undergraduate one (e.g. 27 Oct, 23 Mar, 3 Aug). Each has its own current term.
- **No phone numbers:** students just add their groups in the app and UniFlow's number joins them. Registering with the student email is the only verification.
- **Start small:** a pilot with a few real students, using the Django admin page to check things, before building staff pages.

- **Where login tokens live:** the refresh token is in a secure httpOnly cookie, and the access token is in memory. **Never in `localStorage`.**

- **Frontend folder layout:** `api/`, `components/`, `context/`, `hooks/`, `lib/`, `pages/<Name>/`, `types/` and `router.tsx`. It was restructured before M1.9.

- **Login is kept simple:** UniFlow uses Djoser's own URLs, with no custom login code. Suspended accounts are blocked by one small check (`authentication.py`).

- **AIU uses Schools, not departments.** Everything is called "school" (the role is `school_staff`). The Centre for Foundation and General Studies is stored as a school.

- **Who can register:** only `@student.aiu.edu.my` emails, for example `abdulaziz.mohammedyasin@student.aiu.edu.my`. **Staff accounts** are created by a super admin inside UniFlow (`manage/users/`, M2.2).

## Open decisions

- **Real email sending** (for example Gmail with an app password, or a university mailbox). For now emails are printed in the backend terminal. Set up before launch (M10); it needs 5 SMTP settings in `.env`.

- **AI provider** (proposed: Anthropic Claude). Needed before M5.1.
- **WhatsApp connector library and a dedicated WhatsApp number.** Needed before M6.3.
- **University approval** for reading academic groups. Needed before the pilot (M9.7).
- The university's official timetable format (optional import). Not blocking.
- Hosting (must keep the WhatsApp connector online). Needed before M9.6.
