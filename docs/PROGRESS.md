# UniFlow Progress

This is the **simple overview** of where UniFlow is. It is updated after every task.
(The detailed plan is [11-roadmap.md](11-roadmap.md). You do not need to read it to follow progress.)

**What UniFlow is (updated after M2.8):** an **AI assistant** that reads academic WhatsApp and Telegram groups, works out what matters to each student, and shows only that, in one place. *"No fluff. No information overload. Just the information that matters to you."* See [01-product.md](01-product.md).

**Now:** M9.3 is done ✅. A **privacy notice** anyone can read (linked from registration and the profile), and people who ask **not to be read** can be excluded from the admin. (M6.3's real WhatsApp test still waits for the new number.)
**Next up:** M9.4, the **Django admin** set up for you as the operator: a queue of drafts to check, publish and retract, reviewing new groups, and how much the AI is used.

---

## The big picture

| Milestone | In plain words | Status |
|---|---|---|
| **M0** Foundations | Set up the empty backend and website so they run and are checked automatically | ✅ Done |
| **M1** Identity | Students can register, log in and fill in their profile | ✅ Done |
| **M2** Permissions | Who is allowed to do what, "who is affected by a post", and the staff dashboard frame | ✅ Done (M2.9–M2.11 moved to later milestones) |
| **M3** Classes and preferences | UniFlow learns each student's courses, sections and interests (the semester is worked out from the intake); students see their timetable and can add a class | ✅ Done |
| **M4** Messages | UniFlow can store messages and timetable files from groups (pasted, uploaded, WhatsApp "Export chat", Google Drive links) | ✅ Done |
| **M5** AI, first version | The AI **reads a shared timetable** and the student confirms it; the AI spots "class moved / cancelled / room changed" and the student confirms; their timetable updates | ✅ Done |
| **M6** Connectors | Students add their groups in the app, and UniFlow's own WhatsApp number joins them in the background | ✅ Done except the real WhatsApp test (waits for the new number) |
| **M7** AI, full version | Internships, notices, mentions of your name, and the personal "For you" feed with 4 levels | ✅ Done |
| **M8** Notifications | Alerts inside UniFlow only for what matters to you, plus a daily summary (phone alerts come with the mobile app) | ✅ Done |
| **M9** Pilot | Home screen, search, privacy notice, putting it online, and testing with a small group of real students (you check things in the Django admin) | 🔄 In progress |
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
| M3.1 | **Courses and terms.** A course is a subject (CDE2313) that belongs to a school. A term is a semester ("2025/26 Semester 1"); UniFlow works out the **current term from the dates** (during a break: the next term if it's added, otherwise the one that just ended), so nobody ticks it by hand. The website can read them. | `pipenv run python manage.py migrate`, then `/django-admin/` → Academics → Courses / Terms. Swagger → **academics** → `courses/`, `terms/`, `terms/current/` | ✅ Done |
| M3.2 | **Sections and weekly classes.** A section is one group of a course in one term (CDE2313 Section A). Each section has weekly classes (day, start, end, room). A student can be in a section once. Each section remembers how it was added (by the AI, a student, an admin or a file). | `pipenv run python manage.py migrate`, then `/django-admin/` → **Timetable** → Course sections (add classes at the bottom of a section) | ✅ Done |
| M3.3 | **"Who is affected" by course and section.** A message for CDE2313 reaches students in a CDE2313 section **this term** (not last term's). A message for Section A reaches only Section A. School staff can only pick their own school's courses and sections. *Semester ("Year 2") moved to M3.4.* | `pipenv run python manage.py migrate`, then `pipenv run pytest apps/audiences` | ✅ Done |
| M3.4 | **Semester and interests.** The semester is worked out by **counting AIU's real terms** since the student's intake (three a year; the dates change every year, so they come from the official academic calendar, not fixed dates). An October 2025 intake is in Semester 1 from 27 Oct 2025, 2 from 23 Mar 2026 and 3 from 3 Aug 2026. Foundation students count AIU's **Foundation** terms instead. The official 2024/2025 and 2025/2026 terms of both calendars are loaded by the seed command; new terms are added in the Django admin. A student can set it by hand if that's wrong. Messages can target semesters ("Year 2" = 4–6). Students can save interests (AI, Cybersecurity, …), information types (internships, bootcamps, …) and nicknames. | `pipenv run python manage.py migrate`, then `pipenv run python manage.py seed_academics` (loads the terms); Swagger → **auth** → `users/me/` and `preferences/choices/` | ✅ Done |
| M3.5 | **Sections for students.** A student can browse this term's sections (search by course code or name), join and leave sections, and **add a class that's missing**: course code, section and weekly times. It is created once, so classmates who add the same class just join it, and nobody can change classes someone else added. Foundation students see Foundation-term sections. | Swagger → **timetable** → `sections/` and `my-sections/` (log in as a student) | ✅ Done |
| M3.6 | **Today and this week.** A student's classes for today, or for a whole week (Monday to Sunday), from the sections they joined, in time order. "Today" uses Kuala Lumpur time, so just after midnight it already shows the new day. Days outside the current term are empty. | Swagger → **timetable** → `today/` and `week/` (log in as a student who joined a section) | ✅ Done |
| M3.7 | **Interests on the website.** Onboarding now has a second step, "What matters to you?": tap your interests (AI, Cybersecurity…) and what you want to hear about (internships, bootcamps…), add nicknames, or **Skip for now**. The profile page has a "Your interests" section, and "Your studies" shows **"You are in Semester 3"** with a way to correct it. | Register a new student → after school/programme/intake you see the interests step; then open **Profile** | ✅ Done |
| M3.8 | **Timetable page.** **Today** and **This week** (Monday to Sunday, with previous/next week). A **My sections** box: search for sections and add them, remove them, or **add a missing class** (course, section and one or more weekly classes). New students without classes see a clear "add your classes" message. *The week is a simple list per day, not a calendar grid: easier on phones and no extra library.* | Log in as a student → **Timetable** in the menu | ✅ Done |

---

## M4 Messages: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M4.1 | **Background work with Celery and Redis.** Slow work (the AI, later) will be handed to a **worker** program instead of making students wait. Redis holds the to-do list. Tests don't need Redis. Includes a tiny **ping** job to check the set-up. | See "Background jobs" in [backend/README.md](../backend/README.md): start Redis, start the worker, send `ping`, see `'pong'` | ✅ Done |
| M4.2 | **Groups, members and messages.** A new `intelligence` app with three tables: **Source** (a WhatsApp/Telegram group or channel, or pasted messages: what it's for, official or not, waiting/active/disconnected), **Source member** (a student who added the group) and **Message** (sender, time, text, and whether the AI has looked at it). A group is only connected once, and a message is only stored once. | `pipenv run python manage.py migrate`, then `/django-admin/` → **Intelligence** → Sources / Messages | ✅ Done |
| M4.3 | **Messages by hand.** A student creates a group (e.g. "CDE2313 Sec A") and becomes its member. Then they can **paste** messages copied from WhatsApp (split into separate messages with sender and time) or a single plain message, or **upload WhatsApp's "Export chat" .txt**. UniFlow understands Android and iPhone formats, messages over several lines, and skips system lines ("Ali joined…") and "<Media omitted>". Pasting or uploading the same chat again adds only the new messages. | Swagger → **sources** → `POST /sources/`, then `paste/` or `export/` (with a real exported chat) | ✅ Done |
| M4.4 | **Timetable files.** UniFlow can keep a timetable **image (PNG, JPG, WEBP), PDF or Excel file**, up to 10 MB. The file must **really be** that type (a renamed program is refused), and it's stored **privately** under a random name. A **Google Drive or Google Docs link** is downloaded too (Docs as PDF, Sheets as Excel), but only from Google's own sites and only if the file is shared "Anyone with the link"; otherwise the student gets a clear message. *The upload screen comes with timetable reading in M5.* | `pipenv run python manage.py migrate`; `/django-admin/` → Intelligence → Message files; `pipenv run pytest apps/intelligence` | ✅ Done |
| M4.5 | **Privacy clean-up.** Every night at 03:00, a background job **blanks the text** of messages older than **60 days** (who sent it and when stay) and **deletes timetable files** older than 60 days from the disk. What UniFlow already learned from them (classes, and later the AI's findings with a short quote) stays. 60 days is a setting (`MESSAGE_RETENTION_DAYS`). | Start Celery Beat (`pipenv run celery -A config beat -l info`) next to the worker; or run it now: `pipenv run celery -A config call apps.intelligence.tasks.clear_old_messages` | ✅ Done |
| M4.6 | **Groups page.** In the menu, **Groups** replaces Communities (a later feature). Students see their groups with message counts, **add a group** by name, and for each group **paste messages** or **upload a WhatsApp export** (with instructions). UniFlow says how many messages were new, or shows the reason a file was refused. | Log in as a student → **Groups** in the menu | ✅ Done |

## M5 AI, first version: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M5.1 | **The AI connection.** One small module talks to **Gemini** (Google), using Google's official library: a fast model (`gemini-3.1-flash-lite`) for "is this message academic?" and a smarter one (`gemini-3.5-flash`) that can also read timetable images and PDFs. Both can be changed in `.env`. When Gemini says "too many requests" (the free tier has limits), the job will wait and retry. Tests use a **fake AI**, so they never use your quota. | Put `GEMINI_API_KEY=…` in `backend/.env` and save, then run `pipenv run python manage.py check_ai` | ✅ Done |
| M5.2 | **Insights.** An **insight** is one piece of information ("CDE2313 class moved to 2 PM"): kind, title, summary, importance, action needed, dates and link, who it's for, and **how sure the AI was**. It links to the **original messages** with a short **quote** that stays after the 60-day clean-up. The rule: **sure** (80%+) → shown; **unsure** (50–80%) → shown but marked "Not confirmed"; **very unsure** → kept as a draft. **Official staff posts** are insights too: write one in the Django admin (leave "audience" empty for all students), then use **Publish**. | `pipenv run python manage.py migrate`; `/django-admin/` → Intelligence → Insights → Add | ✅ Done |
| M5.3 | **Triage.** As soon as messages arrive, a background job sends them to the **fast model** in batches of up to 30 (one request per batch) and marks each one **academic** or **noise** (greetings, thanks, selling things…). Messages with a file count as academic and emptied ones as noise, without asking the AI. If Gemini says "too many requests", the job waits 1, 2, 4… minutes and tries again. Messages are sent as data, so a message saying "ignore your instructions" can't change the rules (checked on the real Gemini). | With Redis and the worker running, paste messages on the Groups page, then `/django-admin/` → Intelligence → Messages (the "Triage" column). Or select a group in Sources → **Sort new messages now** | ✅ Done |
| M5.4 | **Reading timetables.** The smart AI model reads a timetable **image, PDF or Excel file** into a list of classes (course, section, lecturer, day, time, type, room). An Excel file is read **tab by tab, once**, and reused for every student. Each student gets **the tab matching their programme and intake** (e.g. "BCS Oct 2025"). Nothing is saved until the student **confirms**; then missing courses, sections and classes are created (shared with classmates), existing ones are **never changed**, and the student is enrolled. Section names like "Grp A" or "Section A" all become "A". Tested on the real Gemini with a sample timetable grid: all classes, days, times and rooms read correctly. | `pipenv run python manage.py migrate`; the screen comes in M5.5. `/django-admin/` → Intelligence → Timetable imports | ✅ Done |
| M5.5 | **"Add my timetable" screen.** On the Timetable page: upload a **photo, PDF or Excel** timetable, or paste a Google Drive / Sheets link. UniFlow shows "Reading your timetable…", then **"Is this your timetable?"** with your tab chosen (you can switch tabs) and every class with its times and rooms. **Untick** classes you don't take, then **Confirm** (or **Not my timetable**). **AIU-only links:** the server can't open links that need an AIU login, so the screen says how to download the sheet as Excel and upload it. | Run both servers, Redis and the Celery worker, log in as a student → **Timetable** → **Add my timetable** | ✅ Done |
| M5.6 | **Spotting timetable changes.** After triage marks messages as academic, a second background job sends them to the **smart model** together with the **earlier messages around them** (so "yes, 2 PM" after "is class still at 10?" makes sense). It finds four kinds: **class moved, class cancelled, room changed, extra class**, with the date ("tomorrow" → the real date). Plain code then finds the **course, section and weekly class**. Every change must quote a real message, or it's thrown away. **Unknown course → kept as a draft** for you to check in the admin. Tested on the real Gemini: 3 real changes found with the right dates; a rumour and an "ignore all rules" message were ignored. | With Redis and the worker running, paste messages like "CDE2313 Sec A: tomorrow's class moves to 2pm" on the Groups page, then `/django-admin/` → Intelligence → Insights | ✅ Done |
| M5.7 | **Confirming a change.** Each change the AI found becomes a **proposal** for the students of that section, with the original message as evidence. A student **confirms** or **rejects** it (and can change their mind). Only after confirming does **their own** Today/Week timetable change: new time or room, a class moved to another day, an extra class added, or a cancelled class marked. Classmates who haven't confirmed see their usual timetable, with the class flagged "change waiting". If you **retract** the insight in the admin, the change leaves everyone's timetable. The AI step now also notices "moved to **another day**". | `pipenv run python manage.py migrate`; the screen comes in M5.8. Try it at `/api/v1/docs/` → timetable → `changes/`, and `/django-admin/` → Timetable → Class changes | ✅ Done |
| M5.8 | **Confirm changes on the Timetable page.** When a change is waiting, a yellow box at the top says "A class may have changed" and shows each change ("10:00–12:00 → 14:00–16:00"), the **original message** and who sent it in which group, a "Not confirmed" tag when the AI wasn't sure, and **Confirm / Reject** buttons. After you answer, the box disappears and Today/Week refresh. Classes get a label: **Moved**, **Cancelled** (time crossed out), **Room changed**, **Extra class**, or **Change waiting**. | Run both servers, Redis and the worker; paste a change message for one of your classes on the Groups page, then open **Timetable** | ✅ Done |
| M5.9 | **Checking the AI.** A saved **test set** in `backend/apps/intelligence/tests/eval/`: 15 group conversations with the right answer (every kind of change, plus tricky ones: a rumour, a question, "ignore all rules", a change taken back, a reply that needs the question before it) and 2 timetable sheets. `evaluate_intelligence` runs the **real** Gemini on them and prints OK or WRONG for each, then the score per kind. Run it again whenever the AI instructions or model change. When the AI gets a real message wrong, add it there (names removed). **Note:** one full run uses 17 requests, and Gemini's free tier allows only **20 a day** for the smart model, so run it on a fresh day (or with `--only changes` / `--only timetables`). | `pipenv run python manage.py evaluate_intelligence` (a few minutes; uses your Gemini free quota) | ✅ Done |

---

## M6 Connectors: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M6.1 | **Telegram bot.** A group admin adds UniFlow's Telegram bot to a group (or makes it admin of a channel), and Telegram sends every new message to UniFlow. A secret checks it's really Telegram (anything else gets "403 refused"). The group appears in UniFlow by itself; each message is stored **once**, with who sent it and what it replies to; photos, PDFs and Excel files are downloaded; then the AI sorts them like any other message. Removing the bot disconnects the group. **No new library.** | Tests only for now: Telegram needs UniFlow online at an **https** address. Setup steps: [08](08-messaging-integrations.md#the-telegram-bot) | ✅ Done |
| M6.2 | **Private addresses for the WhatsApp connector.** Four addresses the connector (M6.3) will use: "which groups should I join?", "I joined this group", "here's a new message", and "here's its file". Every request is **signed** with a shared secret and the time: a forged or changed request, or an old one sent again later (over 5 minutes), gets "403 refused". A message sent twice is stored once; the sender's WhatsApp id is scrambled again on UniFlow's side, so a **phone number is never stored**; files are checked like uploads. If two students' links lead to the same group, it stays one group with both as members. **No new library.** | Tests only (the connector comes in M6.3). Add `CONNECTOR_SECRET` to `backend/.env` when the connector is set up | ✅ Done |
| **M6.3** | **WhatsApp connector.** A small **Node.js** program (it has to be JavaScript because the approved library, **Baileys**, is) in `connectors/whatsapp/`. It logs in as UniFlow's WhatsApp number with a **pairing code**, joins the groups students add (**one at a time**, slowly), posts **one notice** in each group saying what UniFlow reads and how to remove it, and passes every new group message and its photo/PDF/Excel file to UniFlow through the signed addresses from M6.2. It ignores private chats and sends nothing else. After a restart, missed messages arrive **once**. 11 tests, and GitHub runs them automatically. | **Waiting for the dedicated number.** Linking a personal number was tried and stopped on purpose (ban risk). Linking failed with "Couldn't link device": a known Baileys problem; one part is fixed, the other may need a patch | 🔄 Built, real test to do |
| M6.4 | **Add a group.** On the Groups page, one **Add a group** form: a name saying what the group is for, plus the group's **WhatsApp invite link** (optional). With a link, the group is saved as "Waiting for UniFlow to join" and UniFlow's number joins it in the background (M6.3). If another student already added the same group, it **isn't joined twice**: you're simply added to it. Only real WhatsApp links (`https://chat.whatsapp.com/…`) are accepted, so **fake or look-alike links are refused**; a Telegram link explains how to ask the admin to add the UniFlow bot. Without a link, it's a group for pasting messages, as before. | Run both servers, log in as a student → **Groups** → Add a group with a WhatsApp invite link | ✅ Done |
| M6.5 | **Timetables shared in groups.** When a timetable file (Excel, PDF or photo) arrives in a group through Telegram or the WhatsApp connector, every member of that group (a student who added it) **without classes this term** gets it ready on the Timetable page: "A timetable was shared in *SCI Year 1*", with **their own tab** chosen, so they just press Confirm. Students who already have classes aren't bothered. The AI reads the file **only once**, and **only if someone needs it**; a file with no classes (e.g. a poster) is ignored. | Needs a real group (Telegram or the WhatsApp connector): share a timetable file, then open **Timetable** as a member without classes | ✅ Done |


## M7 AI, full version: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M7.1 | **Every kind of information.** Besides timetable changes, the AI now finds **opportunities** (internships, bootcamps, industry visits, competitions, scholarships), **notices** (academic, student affairs, compulsory events, deadlines) and **requests to named students** ("Ali and Sara, please see me"). For each: a title, a one-line summary, **how important** it is, whether you must **act** and what to do, the **deadline** and event date, place, link, topics (like AI or cybersecurity), and **who it's for** ("BCS Year 3" becomes the BCS programme, semesters 7–9). It's the **same single AI request** as before, so no extra quota. Bad answers are thrown away or cleaned (e.g. only real web links). Checked on the real Gemini: an internship, a request to two students and a compulsory briefing were found; an advert and an "ignore your rules" message were ignored. | Nothing for students yet (the "For you" page is M7.6). With the worker running, paste messages on the Groups page, then `/django-admin/` → Intelligence → Insights | ✅ Done |
| M7.2 | **Who is "Ali"?** When the AI finds a request to named students, each name is matched to a real student: first among the students **who added that group**, then among the students the group is **for** (its school, programme, course…). "Ali" matches "Ali Hassan"; "Bro Ali" too; a **nickname** from the profile works. If two students fit (two Alis), it's **not** matched: UniFlow never guesses. Lecturers and staff are never matched. Each match is saved as a **mention** (it will put the message at the top of that student's feed and send an alert, in M7.4 and M8). | `pipenv run python manage.py migrate`; then a request found in a group shows its mentioned students at the bottom of the insight in `/django-admin/` → Intelligence → Insights | ✅ Done |
| M7.3 | **One announcement, not ten copies.** Before saving something the AI found, UniFlow checks the last **2 weeks** for the same information: for a **timetable change**, everything must match (course, section, date, new time and room), so "moved to 2 PM" and "moved to 3 PM" stay **separate** and the conflict is visible; for **other information**, the same link, or the same date and a title with mostly the same words. A match adds the new message as **extra proof** instead of a second item, keeps the **higher "how sure"** score, and can publish a draft that was too unsure once another group confirms it. Retracted items are never brought back this way. | Paste the same announcement in two of your groups (worker running), then `/django-admin/` → Intelligence → Insights: one insight with two pieces of evidence | ✅ Done |
| M7.4 | **What matters to *you*.** When an item is published, UniFlow works out for **each student**: **who** gets it (the students it's for, the members of the groups it came from, anyone named; a timetable change only goes to that section; never staff), **how relevant** it is (0–100: named 100, your section 90, your course 85, your group 80, your programme 65…; your **interests** raise it, a kind of information you **switched off** lowers it a lot), the **level** (**Direct attention** if you were named, **Action required** if you must act, **Important** for e.g. a change to your own class, else the **Digest**; an item the AI wasn't sure about only goes in the digest), and a short **reason** ("You are in CDE2313 Section A", "Matches your interest: Artificial Intelligence"). Items that matter too little to someone aren't shown to them. Plain code, no AI, so no quota. | `pipenv run python manage.py migrate`; then `/django-admin/` → Intelligence → **Deliveries** (who got what, at which level, and why) | ✅ Done |
| M7.5 | **Feed API.** The addresses the "For you" page will call: **my feed** (Direct attention first, then Action required, Important, Digest; newest first in each; or only one level), **one item** with why I see it and the **original messages** (sender, group, time, quote, and "open original": the exact Telegram post, or the WhatsApp group), whether I confirmed it if it's a timetable change, and buttons for **read**, **dismiss** and **"not relevant to me"**. You only ever see **your own** items (anything else: "not found"); retracted or expired items disappear. | `/api/v1/docs/` → **feed** (log in as a student with some deliveries) | ✅ Done |
| M7.6 | **The "For you" page.** The home page (`/`) is now **For you**: your items in **four sections in order** (Direct attention, Action required, Important updates, Digest; empty ones hidden). Each card shows the title, summary, date or deadline, **why you see it**, an **Official** or **Not confirmed** tag, and a dot if unread. Clicking opens the **item page**: details, a **"What to do"** box, a link, the **original messages** with **Open original**, a link to your timetable for a class change, and **Dismiss** / **Not relevant to me**. Opening it marks it read. The menu is now **For you, Timetable, Groups** (Profile stays at the bottom of the sidebar); the old "Announcements" and "Events" placeholders are gone. **Notifications** joins the menu with M8. | Run both servers, log in as a student → **For you** (items appear once groups bring in messages, or after you publish a staff post in the admin) | ✅ Done |

## M8 Notifications: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M8.1 | **Storing alerts.** A new backend app, `notifications` (the second app you chose with `intelligence`): each alert says **who** it's for, **what kind** (you were named, action required, important update, class change to confirm or taken back, daily digest, from UniFlow), a title and a short text, and **what it opens** (e.g. an item of your feed). The same alert can **never be stored twice**. Addresses to **list** my alerts (newest first), get the **unread count** (for the bell), **mark one read** and **mark all read**; you only ever see your own. Backend only: nothing creates alerts yet (M8.2) and the bell comes in M8.4. | `pipenv run python manage.py migrate`; `/api/v1/docs/` → **notifications**; `/django-admin/` → Notifications | ✅ Done |
| M8.2 | **Sending alerts.** When something is published (or a name in it is matched), the background worker sends an alert to every student for whom it's **Direct attention** (you were named), **Action required**, or **Important** (a **class change to confirm** gets its own alert). **Digest** items don't alert; they wait for the daily digest (M8.3). An alert is **never sent twice** (each student and item is marked once, and the database refuses duplicates). A **forwarded copy** puts the item in new students' feeds but sends **no alert**. If a class change is **taken back**, the students alerted about it get "Taken back: …". | With the worker running, publish an important staff post in the admin (importance 70+), then `/django-admin/` → Notifications (or `/api/v1/notifications/` as a student) | ✅ Done |
| M8.3 | **The daily digest.** "Digest" items are the *good to know* ones (not urgent, or the AI wasn't sure), so they **don't alert one by one**. Instead, **every evening at 7 pm** (Malaysia time) a scheduled job sends each student **one** alert: "Your daily digest: 4 new items", with the top 3 titles. **Nothing new → no alert.** At most **one per day**, even if the job runs twice. Items you dismissed, marked "not relevant", or that were retracted or expired are left out. Tapping the alert (M8.4) opens the **Digest page** (`/digest`): that day's items **grouped by type** (Academic notices, Student affairs, Internships…), each opening its item page. | Run the worker **and** `celery -A config beat` (the scheduler), or try it at once: `pipenv run python manage.py shell -c "from apps.intelligence.delivery import send_daily_digests; print(send_daily_digests())"`, then open `/digest` as a student | ✅ Done |
| M8.4 | **The bell.** **Notifications** is in the menu ("Alerts" on phones) with a **red number** of unread alerts, checked **every 60 seconds only while the UniFlow tab is visible** (and again when you come back to it). The **Notifications page** lists your alerts, newest first: what kind ("You were named", "Class change to confirm", "Daily digest"…), the title and text, and "5 min ago"; unread ones are bold with a dot. **Tapping** one marks it read and **opens it** (its item page, or that day's Digest page). **Mark all as read** clears the number. | Run both servers (and the worker), log in as a student who has alerts → the number next to **Notifications** → tap an alert | ✅ Done |

## M9 Pilot release: task by task

| Task | What it did (plain words) | What you can see or try | Status |
|---|---|---|---|
| M9.1 | **Today at a glance.** A new address, `GET /api/v1/feed/home/`, gives everything the home screen needs in **one fast request** (15 database lookups at most): the first few Direct attention, Action required and Important items, **today's classes** (with changes you confirmed), **class changes waiting** for you, a digest preview and your unread alert count. It follows the same rules as the feed (you only see your own; dismissed, retracted and expired items are hidden). On the website, For you now starts with a **Today** box: your classes today (a cancelled one crossed out, a moved one marked) and "1 class change is waiting for you → Confirm or reject". Staff don't see the box. The mobile app will use the same address. | Run both servers, log in as a student with classes → **For you** | ✅ Done |
| M9.2 | **Search.** "Search" is in the menu. Type a few words (e.g. "petronas internship") and UniFlow finds every item that was **delivered to you**, including ones you read, dismissed or got in a digest, newest first. It looks in titles, summaries, places, "what to do" and the **original messages**; with several words, an item must contain **all** of them. It **never** shows something that wasn't delivered to you, nor retracted or expired items. At least 2 characters. | Run both servers, log in as a student → **Search** | ✅ Done |
| M9.3 | **Privacy.** A **privacy notice** page (`/privacy`) that anyone can open without logging in, linked from **registration** and the **profile**: what UniFlow reads (only academic groups students added; never private chats or phones), what it keeps (message text **60 days**, then only short quotes; senders by name and a scrambled id, never a phone number), that text goes to **Google's Gemini AI**, and how to ask not to be read. **Excluding a sender**: in the admin, select any of their messages → "**Stop reading these senders**". Their stored message text is **erased** (quotes from them become "[Removed at the sender's request]"), and their future messages are **skipped** everywhere: Telegram, the WhatsApp connector, pasting and chat exports. | `pipenv run python manage.py migrate`; open `/privacy`; `/django-admin/` → Intelligence → Messages → select → the action; then Excluded senders | ✅ Done |
| **M9.4** | **The admin, set up for you:** drafts to check, publish/retract, new groups to review, AI usage | – | ⏭️ **Next** |
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
| `api/` | **Talking to the backend:** `client.ts` (the connection, which refreshes the login automatically), `auth.ts` (login, logout, who am I, profile, password), `timetable.ts` (sections, today, week, imports, changes), `sources.ts` (groups, paste, upload, connect), `feed.ts` (the "For you" feed and digest), `notifications.ts` (alerts and the unread count), `academics.ts` (schools, programmes, intakes), `errors.ts` (reads errors), `health.ts` (health check), `tokenStore.ts` (the access token, in memory only) |
| `context/` | `AuthContext.tsx`: who is logged in (`useAuth()`) |
| `hooks/` | Data hooks for pages: `useAcademics.ts` (schools, programmes, intakes), `usePreferences.ts` (interest choices), `useTimetable.ts` (today, week, my sections), `useSources.ts` (groups), `useFeed.ts` (For you, digest), `useNotifications.ts` (alerts; the unread count every 60 s), `useHealth.ts` |
| `types/` | TypeScript shapes of API data: `academics.ts`, `auth.ts`, `timetable.ts`, `sources.ts`, `feed.ts`, `notifications.ts`, `health.ts` |
| `components/` | Page frames (`AppLayout`, `AuthLayout`, `StaffLayout`), `RequireAuth` (login-only pages, and sends new students to onboarding), `FormField` and `SelectField` (form inputs), `StudentDetailsForm`, `PreferencesForm` (interests, information types, nicknames), `SectionPicker`, `AddClassForm` and `TimetableImport` (timetable), `ChangePasswordForm`, `RequireCapability` (staff pages: "No access" if not allowed), `Can` (hides buttons you can't use), small boxes (`EmptyState`, `ErrorState`, `PageLoading`) and the dev-only `HealthBadge` |
| `components/ui/` | **shadcn** components (Button, Badge, Input, Label). Add more with `npx shadcn@latest add <name>`. |
| `pages/` | One folder per page: `Login/`, `Register/`, `ActivateAccount/`, `ForgotPassword/`, `ResetPassword/`, `Onboarding/`, `Profile/`, `ForYou/` (the home page), `Insight/` (one item), `Digest/` (one day's digest), `Notifications/`, `Search/`, `Timetable/`, `Sources/` (Groups), `NoAccess/`, `NotFound/`, `Placeholder/`, `RouteError/` |
| `lib/` | Helpers: `utils.ts` (shadcn), `queryClient.ts`, `navigation.ts` (the student and staff menu links), `capabilities.ts` (what the user may manage), `timetable.ts` (date and class-time formatting), `feed.ts` (the four levels, digest headings, date formatting), `notifications.ts` (alert labels, where each alert goes, "5 min ago") |
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
| `apps/intelligence/` | The AI pipeline: groups (sources), their members and messages, `whatsapp_export.py` (reads WhatsApp's text formats), `services.py` (paste and upload rules), `files.py` (timetable files and Drive links), `providers.py` (the AI), `triage.py` (academic or noise), `timetable_reading.py` (reading timetables), `extraction.py` (timetable changes in messages) and `telegram.py` (the Telegram bot) |
| `apps/notifications/` | Alerts inside UniFlow (`Notification`): the list, unread count and mark-as-read addresses (M8.1); sending them comes in M8.2 |
| `apps/publishing/` | The shared base for every post (status, publisher, expiry), the publish / archive actions, and `policies.py` (the school boundary) |
| `core/models.py` | Shared "created at / updated at" timestamps for every table |
| `core/` | Shared API pieces: the error format, paging and the health check |
| `.env` | Your local passwords (never committed) |

---

## Decided recently

- **UniFlow is an AI information assistant**, not a notice board. Messages from academic WhatsApp and Telegram groups are the main input. The AI **proposes**; normal code decides; the student **confirms** timetable changes.
- **WhatsApp:** an **unofficial connector** (a dedicated UniFlow number joins groups), chosen knowingly. Risks: WhatsApp's rules, the number can be banned, members' consent. Safeguards and details: [08](08-messaging-integrations.md). Telegram uses the official bot. Pasting and chat export always work too.
- **Staff posts stay** as one official source. The M2 code is kept and reused.
- **The AI is Gemini, on the free tier for now**, using the **oldest models that still work for a new key** (`gemini-3.1-flash-lite` and `gemini-3.5-flash`; the 2.5 models are closed to new users), because older models usually allow many more free requests. Google may use what's sent on the free tier; you decided (October 2026) to stay on it, and the privacy notice says so.
- **Background work uses Celery with Redis** (your choice, over a simpler database table). Redis runs in WSL on your PC; tests need no Redis.
- **When the AI isn't sure:** sure → shown; unsure → daily summary marked "Not confirmed"; very unsure → hidden until you check it.
- **Staff posts and AI findings are one thing** in the code (no separate announcements part).
- **The normal timetable comes from the groups too:** the AI reads timetable images, PDFs and Google Drive links, and the student confirms before anything is saved.
- **Alerts stay inside UniFlow** for now; the mobile app will add phone notifications.
- **The current term is automatic:** worked out from the term dates, so nobody ticks "current". When AIU publishes a new term, add it in `/django-admin/` → Terms (the "Current now" column shows which one UniFlow is using).
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

- **A contact address for the privacy notice** (an email students and group members can write to, e.g. to ask not to be read). The notice says "will be added before launch". Also consider adding the `/privacy` address to the WhatsApp join notice once UniFlow has its web address.
- **Gemini free tier: decided, UniFlow stays on it** (October 2026). The privacy notice says plainly that Google may use the message text to improve its products. Still open: the free tier's **daily limits** (the smart model allowed only 20 requests a day in M5.9), which a few busy groups would use up. One idea: when a model's daily limit is used up, switch to another model that still has requests left.
- **A dedicated WhatsApp number** (a new SIM, never a personal number: it can be banned). Needed to finish testing M6.3. *(The library is decided: Baileys.)*
- **Patch Baileys if linking still fails?** WhatsApp changed linking in July 2026 and Baileys' fix isn't released yet. Options: apply the fix as a patch (a new tool, `patch-package`), or wait for the next Baileys release.
- **The UniFlow Telegram bot** (create it with @BotFather; choose its name). Needed to switch Telegram on, together with hosting.
- **University approval** for reading academic groups. Needed before the pilot (M9.7).
- The university's official timetable format (optional import). Not blocking.
- Hosting (must keep the WhatsApp connector online). Needed before M9.6.
