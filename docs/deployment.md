# Deployment

UniFlow runs entirely on free tiers. The backend image runs both the API and the background jobs; there is no separate worker, scheduler or message broker.

```
Browser ──► Vercel (React SPA) ──/api/*──► Render web service (Django + gunicorn)
                                              │        ▲
                                              │        │ signed calls to /api/inngest
                                              │        │ (events, retries, cron)
                                              ▼        │
                             Supabase PostgreSQL     Inngest Cloud
                             Supabase Storage (S3)
WhatsApp connector (Node, Baileys) ──signed POST──► /api/v1/internal/
Telegram ──webhook──► /api/v1/integrations/telegram/webhook/
```

| Component | Platform | Notes |
|---|---|---|
| Web app | Vercel | Built from `frontend/`. `vercel.json` proxies `/api/*` to Render, so the refresh-token cookie stays first-party. |
| API and background jobs | Render web service (Docker, Singapore) | Built from `backend/Dockerfile`. Background jobs run in-process when Inngest calls `/api/inngest`. |
| Database | Supabase PostgreSQL (Singapore) | Session pooler (IPv4). Chosen over Render PostgreSQL, whose free tier expires after 30 days. |
| File storage | Supabase Storage via its S3 API | Private bucket; `django-storages`. |
| Job orchestration | Inngest Cloud | Event-triggered and cron functions, retries, per-group concurrency limits. |
| Email | Brevo (HTTPS API, free tier) | Activation and password-reset emails via `django-anymail`. Render's free tier blocks outbound SMTP (ports 25, 465, 587), so an HTTP API is required. |
| WhatsApp connector | Self-hosted (developer machine) | Long-lived WebSocket; unsuitable for a sleeping free web service. |

## Configuration

Production uses `config.settings.prod`, which reads all secrets from the environment and refuses to start if a required one is missing.

| Variable | Purpose |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `DJANGO_SECRET_KEY` | Django secret (50+ random characters) |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | The Render hostname (`uniflow-api.onrender.com`, `https://…`) |
| `DATABASE_URL` | Supabase session-pooler URI with `?sslmode=require` |
| `FRONTEND_DOMAIN`, `CORS_ALLOWED_ORIGINS` | The Vercel domain (used in email links; CORS is a fallback, since the proxy is same-origin) |
| `ALLOWED_EMAIL_DOMAINS`, `TIME_ZONE` | `student.aiu.edu.my`, `Asia/Kuala_Lumpur` |
| `EMAIL_BACKEND` | `anymail.backends.brevo.EmailBackend` (the console backend prints emails to the log instead) |
| `BREVO_API_KEY` | Brevo API key. **Required** when `EMAIL_BACKEND` is Brevo |
| `DEFAULT_FROM_EMAIL` | Sender, e.g. `UniFlow <address@example.com>`; the address must be a verified sender in Brevo |
| `GEMINI_API_KEY` | AI provider |
| `INNGEST_SIGNING_KEY`, `INNGEST_EVENT_KEY` | **Required.** Verify inbound calls and authorize outbound events |
| `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | Supabase Storage (S3 compatibility) |
| `CONNECTOR_SECRET` | HMAC secret shared with the WhatsApp connector |
| `UNIFLOW_WHATSAPP_NUMBER` | UniFlow's WhatsApp number (e.g. `+60123456789`), shown to students who add it to a group without an invite link |
| `EXPO_ACCESS_TOKEN` | Expo access token (expo.dev → Account settings → Access tokens), for push notifications to the mobile app. **Secret.** Empty: nothing is pushed |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` | Optional Telegram bot |

The full list with local defaults is in [02, Configuration](02-system-architecture.md).

## Setup

1. **Supabase.** Create a project in Singapore. Take the *Session pooler* connection string as `DATABASE_URL`. Create a private bucket and an S3 access key ([10](10-testing-and-deployment.md#uploaded-files-online-supabase-storage-m96h)).
2. **Inngest.** Create a production environment and copy the event key and signing key.
3. **Brevo.** Create a free account, verify the sender address (*Senders, domains & dedicated IPs → Senders*) and create an API key (*SMTP & API → API keys*).
4. **Render.** Create a web service from the repository:
   - root directory `backend`, Docker runtime, Singapore, free instance;
   - health check path `/api/v1/health/`;
   - the variables above.

   The container runs `migrate` and `collectstatic` on start, then gunicorn on `$PORT` (2 workers, 120 s timeout: jobs invoked by Inngest can exceed gunicorn's 30 s default).
5. **Bootstrap data.** Render's free tier has no shell, so run management commands locally against `DATABASE_URL`:
   ```powershell
   $env:DATABASE_URL = "<supabase uri>"
   pipenv run python manage.py createsuperuser
   pipenv run python manage.py seed_academics
   Remove-Item Env:DATABASE_URL
   ```
6. **Sync Inngest.** Register `https://uniflow-api.onrender.com/api/inngest`. The dashboard should list 13 functions, including the daily jobs (03:00 and 19:00, Asia/Kuala_Lumpur) and the push jobs (every 5 and 15 minutes).

   Inngest only learns about functions when the app is synced. **After any deploy that adds, removes or changes a background function, resync** (*Apps → uniflow → Resync*) and check the function count; until then, new functions never run.
7. **Vercel.** Import the repository with root directory `frontend` (Vite preset). If the Render hostname differs from `uniflow-api.onrender.com`, update `frontend/vercel.json`.
8. **WhatsApp connector.** Set `UNIFLOW_API_URL=https://uniflow-api.onrender.com/api/v1` and the shared `CONNECTOR_SECRET` in `connectors/whatsapp/.env`, then run `npm start`.
9. **Telegram (optional).** Run `manage.py set_telegram_webhook https://uniflow-api.onrender.com`, with the same token and secret as production.

**Smoke test:**
- `/api/v1/health/` responds through the Vercel domain;
- registration sends an activation email, and its link activates the account;
- a timetable upload lands in the bucket and triggers `read-timetable-import` in Inngest;
- a group message triggers `triage-source`.

## Free-tier trade-offs

| Constraint | Effect | Mitigation |
|---|---|---|
| Render free services sleep after 15 min idle | First request after idle takes up to about 1 min | Inngest calls and connector traffic wake the service; the connector waits for the response |
| Render free tier: about 750 instance-hours/month per account | Room for one always-on free service | Single web service; no worker needed thanks to Inngest |
| Supabase pauses free projects after about 1 week of inactivity | Site errors until the project is restored | Daily cron jobs and regular use keep it active |
| Vercel function payload limit (about 4.5 MB) on proxied requests | Large timetable uploads may fail through the proxy | Verify with a 10 MB file; fall back to direct upload or a lower `MAX_UPLOAD_MB` |
| Brevo free tier: 300 emails/day | Enough for activation and reset emails at pilot scale | Brevo paid plan if volume grows |
| Sender is a free-mail address, not an own domain | Some messages may be filtered as spam | Verify an own domain in Brevo (SPF and DKIM records) |
| Connector on a developer machine | Ingestion pauses when the machine is off; missed messages replay on reconnect | Move to an always-free VM (Oracle Cloud, GCP e2-micro) using `connectors/whatsapp/Dockerfile` |
| Connector doesn't retry on 5xx | A message can be lost during a redeploy | Planned: retry with backoff |
