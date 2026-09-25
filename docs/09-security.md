# 09 — Security Considerations

All controls below are **[MVP]** unless marked otherwise.

| Area | Threat | Control |
|---|---|---|
| **Staff dashboard** | Someone calls a management action directly, bypassing the UI | **The frontend is not the security boundary.** Every `/api/v1/manage/` endpoint checks the capability (`HasCapability`), the scope (`manageable_queryset`) and the object (`CanManageObject`), and validates the publisher and school in the request body on the server. Tests call each manage endpoint as every role. |
| Registration | Outsiders create student accounts | An email domain allow-list, activation before login, and throttled registration |
| Credentials | Brute force or credential stuffing | An `auth` throttle of 10/min per IP, Django password validators (minimum 10 characters), and generic 401 errors |
| Account changes | Changing an email to bypass the domain rule, or hard-deleting accounts | Djoser's email-change and delete endpoints are restricted to super admins |
| Suspension | A blocked user reactivates themselves | `is_suspended` is separate from `is_active` and is checked at login and on every authenticated request |
| Tokens | XSS steals tokens | The access token is kept in memory and expires in 15 minutes. The refresh token is in an httpOnly cookie (web) or SecureStore (mobile). Refresh tokens rotate and are blacklisted after use, and all of them are revoked when the password changes. |
| CSRF | A cross-site call to the cookie refresh endpoint | `SameSite=Lax`, a cookie path limited to `/api/v1/auth/jwt/`, the required `X-Client` header and an `Origin` check |
| Read authorization | Seeing content aimed at another group | Every read endpoint queries through the visibility selector, and items the user cannot see return 404. There are tests for "a school A student cannot fetch a school B item". Documents are available to every logged-in user, by decision. |
| Privilege escalation | A user changes their own role | `role`, `is_staff` and `is_suspended` are read-only everywhere except `manage/users/`, which is super admin only |
| Mass assignment | A client sets `created_by`, `status` or `notified_at` | Serializers list their writable fields explicitly. Status changes only through `publish/` and `archive/`. |
| XSS through content | Malicious Markdown | react-markdown runs with raw HTML turned off. Links get `rel="noopener noreferrer nofollow"`. Only the `http`, `https`, `mailto` and `tel` URL schemes are allowed. |
| File upload | Malware, fake content types, path traversal | An extension allow-list, a check of the file's real contents (magic bytes), size limits, and UUID filenames. Downloads are sent with `Content-Disposition: attachment` and `nosniff`. HTML and SVG uploads are never accepted. |
| Phishing links | Fake WhatsApp or Telegram links | The link's host must match its platform. Communities can be marked verified. |
| Transport and headers | Eavesdropping, clickjacking | In production: HTTPS only, HSTS, secure cookies, `X-Frame-Options: DENY`, a CSP on the frontend host, and `Referrer-Policy` |
| CORS | Other sites calling the API with credentials | An exact `CORS_ALLOWED_ORIGINS` list |
| Back-office | Misuse of the Django admin | Only super admins have access, at `/django-admin/`. Staff never need it. |
| Secrets | Leaked keys | `backend/.env` is git-ignored and only `.env.example` is committed |
| Dependencies | Vulnerable packages | `npm audit` in CI, which needs no extra install. `pip-audit` is optional and needs approval. GitHub Dependabot alerts can be switched on in the repository settings. |
| Webhooks *[Later]* | Forged Telegram updates | Check the `secret_token` header |
| Personal data *[Later]* | Data protection (Malaysia's PDPA 2010) | Data export and anonymized account deletion. The MVP stores only name, email, student number and academic affiliation. |
| Audit *[Later]* | Nobody knows who changed something | The MVP records `created_by`, `updated_by` and timestamps. A `ContentAuditLog` of publish and archive actions comes later. |
