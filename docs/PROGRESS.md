# UniFlow Progress

This is the **simple overview** of where UniFlow is. It is updated after every task.
(The detailed plan is [11-roadmap.md](11-roadmap.md). You do not need to read it to follow progress.)

**Now:** M2.3 is done ✅. Admins can add, edit and switch off schools, programmes and intakes through the API (backend only; the pages come in M2.11).
**Next up:** M2.4, the `Audience` model: a small record saying who a post is for (everyone, a school, a programme or an intake).

---

## The big picture

| Milestone | In plain words | Status |
|---|---|---|
| **M0** Foundations | Set up the empty backend and website so they run and are checked automatically | ✅ Done |
| **M1** Identity | Students can register, log in and fill in their profile | ✅ Done |
| **M2** Permissions and staff area | Who is allowed to do what, and the staff dashboard frame | 🔄 In progress |
| **M3** Announcements | Staff post announcements, and students see the ones meant for them | ⏳ |
| **M4** Documents | Upload and download documents, and attach them to announcements | ⏳ |
| **M5** Events | Events list and calendar | ⏳ |
| **M6** Communities | Clubs and groups with WhatsApp and Telegram links | ⏳ |
| **M7** Timetable | Students see today's and this week's classes | ⏳ |
| **M8** Applications and forms | What students can apply for, and until when | ⏳ |
| **M9** Notifications | The bell icon for important news | ⏳ |
| **M10** Dashboard, search and launch | Home page, search, and putting it online | ⏳ |

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
| **M2.4** | **Audience:** who a post is for (everyone, a school, a programme or an intake) | – | ⏭️ **Next** |
| M2.5 – M2.11 | Audience targeting, the shared content base, the staff dashboard frame and its first pages | – | ⏳ |

---

## Where things are

| I want to... | Look at |
|---|---|
| See what's done and what's next | **This file** |
| Run the backend | [backend/README.md](../backend/README.md) |
| Run the website | [frontend/README.md](../frontend/README.md) |
| Understand the whole design | [docs/README.md](README.md) |

### Website files so far (`frontend/src/`)

| File or folder | Job |
|---|---|
| `main.tsx` | Starting point: turns on data loading (TanStack Query) and the router |
| `router.tsx` | **The router:** which address shows which page |
| `api/` | **Talking to the backend:** `client.ts` (the connection, which refreshes the login automatically), `auth.ts` (login, logout, who am I, profile, password), `academics.ts` (schools, programmes, intakes), `errors.ts` (reads errors), `health.ts` (health check), `tokenStore.ts` (the access token, in memory only) |
| `context/` | `AuthContext.tsx`: who is logged in (`useAuth()`) |
| `hooks/` | Data hooks for pages: `useAcademics.ts` (schools, programmes, intakes), `useHealth.ts` |
| `types/` | TypeScript shapes of API data: `academics.ts`, `auth.ts`, `health.ts` |
| `components/` | Page frames (`AppLayout`, `AuthLayout`, `StaffLayout`), `RequireAuth` (login-only pages, and sends new students to onboarding), `FormField` and `SelectField` (form inputs), `StudentDetailsForm`, `ChangePasswordForm`, small boxes (`EmptyState`, `ErrorState`, `PageLoading`) and the dev-only `HealthBadge` |
| `components/ui/` | **shadcn** components (Button, Badge, Input, Label). Add more with `npx shadcn@latest add <name>`. |
| `pages/` | One folder per page: `Login/`, `Register/`, `ActivateAccount/`, `ForgotPassword/`, `ResetPassword/`, `Onboarding/`, `Profile/`, `NotFound/`, `Placeholder/`, `RouteError/` |
| `lib/` | Helpers: `utils.ts` (shadcn), `queryClient.ts`, `navigation.ts` (the menu links) |
| `index.css` | Colours and fonts |

### Backend files so far (`backend/`)

| File or folder | Job |
|---|---|
| `config/settings/` | Settings (dev, test, prod) |
| `config/api_v1.py` | The list of API addresses |
| `apps/accounts/` | User accounts, login, profiles, `capabilities.py` (who may manage what), `authentication.py` (blocks suspended users) and `manage_views.py` (staff user management) |
| `apps/academics/` | University structure: schools, programmes and intakes, and `manage_views.py` (admins edit them) |
| `core/models.py` | Shared "created at / updated at" timestamps for every table |
| `core/` | Shared API pieces: the error format, paging and the health check |
| `.env` | Your local passwords (never committed) |

---

## Decided recently

- **Where login tokens live:** the refresh token is in a secure httpOnly cookie, and the access token is in memory. **Never in `localStorage`.**

- **Frontend folder layout:** `api/`, `components/`, `context/`, `hooks/`, `lib/`, `pages/<Name>/`, `types/` and `router.tsx`. It was restructured before M1.9.

- **Login is kept simple:** UniFlow uses Djoser's own URLs, with no custom login code. Suspended accounts are blocked by one small check (`authentication.py`).

- **AIU uses Schools, not departments.** Everything is called "school" (the role is `school_staff`). The Centre for Foundation and General Studies is stored as a school.

- **Who can register:** only `@student.aiu.edu.my` emails, for example `abdulaziz.mohammedyasin@student.aiu.edu.my`. **Staff accounts** are created by a super admin inside UniFlow (`manage/users/`, M2.2).

## Open decisions

- **Real email sending** (for example Gmail with an app password, or a university mailbox). For now emails are printed in the backend terminal. Set up before launch (M10); it needs 5 SMTP settings in `.env`.

- The university's timetable format. This is needed before M7.11.
- Hosting. This is needed before M10.7.
