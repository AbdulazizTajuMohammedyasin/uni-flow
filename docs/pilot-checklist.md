# Pilot checklist (M9.7)

Go/no-go list for the first pilot with real AIU students. Every item must be checked, or explicitly waived in the sign-off table, before the pilot cohort is invited. Items already done in the codebase are pre-checked.

## 1. Approvals and privacy

- [ ] **University approval** obtained in writing for reading academic WhatsApp and Telegram groups. The request must state that:
  - message text and timetable files go to Gemini's free tier, where Google may use them to improve its products;
  - this includes members who never signed up ([09](09-security.md)).
- [ ] **PDPA 2010** review with the university's data-protection contact: purpose, retention (60 days), the processors listed below, and how to make a request.
- [ ] **Contact address** added to the privacy notice (`frontend/src/pages/Privacy/Privacy.tsx`, "Your choices"); it currently says "will be added before launch".
- [x] Privacy notice matches current behaviour (re-checked in M9.7):
  - silent joins, with the team informing groups;
  - message text **and timetable files** sent to Gemini;
  - hosting providers named.
- [ ] **Group consent:** every pilot group's admin agrees before UniFlow's number or bot is added, and members are told, with a link to `/privacy`. Joins are silent by default (`SEND_JOIN_NOTICE=false`), so telling members is a manual step.
- [x] Sender exclusion works end to end: the Messages admin action skips and erases an excluded sender ([09](09-security.md)).

**Processors:**

| Processor | Role |
|---|---|
| Render | API hosting |
| Supabase | Database and files |
| Vercel | Web app |
| Inngest | Job orchestration; receives only record IDs |
| Google Gemini | AI processing |

## 2. Infrastructure ([deployment.md](deployment.md))

- [ ] Production deployed, and the smoke test in [deployment.md](deployment.md) passes end to end.
- [ ] Inngest shows 10 synced functions. Both crons ran at least once: `clear-old-messages` (03:00) and `send-daily-digest` (19:00).
- [ ] HSTS raised from 1 hour to 1 year (`DJANGO_HSTS_SECONDS=31536000`) after HTTPS has been confirmed for a week.
- [ ] Backups:
  - Supabase's automatic backups confirmed;
  - a manual `pg_dump` taken and **restored into a scratch database once**;
  - `connectors/whatsapp/auth/` copied somewhere safe.
- [ ] A 10 MB timetable upload succeeds through the Vercel proxy, or `MAX_UPLOAD_MB` is lowered to what does ([10](10-testing-and-deployment.md#how-the-two-hosts-fit-together-vercel-forwarding-m96b)).
- [ ] Secrets rotated before launch: every key that was ever pasted outside Render or a local `.env` (for example in a chat) is replaced.

## 3. Messaging channels

- [ ] **WhatsApp number:**
  - a dedicated SIM, never a personal number;
  - used normally for at least a day before linking, to reduce ban risk;
  - paired with the connector (M6.3's real-number test).
- [ ] Connector host decided. For now it's the developer's machine: the pilot schedule assumes it is on during the day, and missed messages replay on reconnect. Or: an always-free VM.
- [ ] **Telegram bot:**
  - created with BotFather;
  - privacy mode off, so it reads group messages;
  - webhook set with `set_telegram_webhook`, and `--info` shows the production URL.
- [ ] A real message in one test group of each platform appears in the admin and is sorted (`triage-source` run in Inngest).

## 4. AI (Gemini free tier)

- [ ] `manage.py check_ai` (run locally with the production key) lists every model in `AI_FAST_MODELS` and `AI_SMART_MODELS` as working.
- [ ] Expected daily volume estimated against the free tier's per-model daily limits (Google AI Studio). Rough count: the pilot groups' messages per day ÷ 30 per triage batch, plus one smart-model call per academic batch and per timetable. Fallback across models ([12](12-intelligence.md)) covers spikes. When every model is exhausted, jobs wait as long as Google asks (at most an hour) instead of failing.
- [ ] A sample of real pilot-group messages, anonymised and labelled, added to `apps/intelligence/tests/eval/`; `evaluate_intelligence` run on it and the accuracy reviewed before launch.
- [ ] Operator routine agreed:
  - **Drafts to check** reviewed daily in the admin;
  - **AI requests** list checked for errors or rate limits.

## 5. Pilot cohort

- [ ] **Intake and programmes chosen**, for example one intake of one school. Their programmes, intake and courses exist (`seed_academics`; 376 courses loaded).
- [ ] **Group list** for the cohort: course and section groups, with their admins' consent (section 1).
- [ ] **Account activation emails** arrive through Brevo (M9.8): test with one real student address, check that it is not filtered as spam by the university's mail system, and keep the daily volume under the free tier's 300.
- [ ] Onboarding walk-through tested with one student: register → activate → profile → timetable upload → confirm classes → For you.
- [ ] Feedback channel announced (form or chat), and a date set for the end-of-pilot review.

## 6. Known limitations accepted for the pilot

| Limitation | Accepted because |
|---|---|
| Render free tier sleeps after 15 min idle (about 1 min wake-up) | Pilot scale; Inngest and connector traffic wake it |
| Supabase pauses after about 1 week of inactivity | Daily use and crons keep it active; restore takes minutes |
| Connector doesn't retry on 5xx (a message can be lost during a redeploy) | Redeploys are rare and scheduled; retry is planned |
| No staff pages (the operator uses the Django admin) | Planned for M10 |
| Gemini free tier: Google may use submitted data | Disclosed in the privacy notice; part of the university approval |

## Sign-off

| Area | Owner | Status | Date | Notes / waivers |
|---|---|---|---|---|
| Approvals and privacy | | | | |
| Infrastructure | | | | |
| Messaging channels | | | | |
| AI | | | | |
| Pilot cohort | | | | |
