# 06 — Authentication & Authorization

## 12. Authentication architecture [MVP]

**Kept simple on purpose:** UniFlow uses **Djoser's own URLs** for accounts and login. The only addition is keeping the website's refresh token in a secure httpOnly cookie (`cookie_jwt.py`).

```python
# backend/apps/accounts/urls.py  (mounted at /api/v1/auth/)
urlpatterns = [
    path("", include("djoser.urls")),      # register, activate, users/me/, password reset/change
    path("", include("djoser.urls.jwt")),  # jwt/create/ (login), jwt/refresh/, jwt/verify/
]
```

| Library | Responsibility |
|---|---|
| **Djoser** | Registration, activation email, resending activation, `users/me/`, password reset and change |
| **SimpleJWT** | Login tokens: issuing, refreshing and verifying them (`JWTAuthentication`) |
| **UniFlow** (`apps/accounts`) | Only the rules Djoser can't know: the `@student.aiu.edu.my` domain check and creating the student profile (`serializers.py`), plus profiles, capabilities and staff management later |

### Registration

1. `POST /api/v1/auth/users/` takes `{email, full_name, password, re_password}`.
2. The email domain must be in `ALLOWED_EMAIL_DOMAINS` (`student.aiu.edu.my`). `UserCreateSerializer` enforces this.
3. The user is created through `accounts.services.create_user()` with `role = student` and `is_active = false`, together with their student profile. **`is_active` means "email verified".** Djoser emails a link to `http://<FRONTEND_DOMAIN>/verify-email/{uid}/{token}`, and the website page sends `{uid, token}` to `users/activation/`.
4. Logging in before activation fails with 401 (Djoser and SimpleJWT's normal "no active account" answer).
5. Students without a complete profile are sent to `/onboarding`.

**Staff accounts:**

- **Only `@student.aiu.edu.my` addresses can self-register.** Staff and lecturers (`@aiu.edu.my`) cannot.
- A `super_admin` **creates staff accounts** in the staff dashboard (`POST /api/v1/manage/users/`, M2.2), and UniFlow emails a "set your password" link using Djoser's password-reset flow.
- Until M2.2 exists, staff accounts can be created in the Django admin back-office. The first `super_admin` is created with `createsuperuser`.

**Suspension** (`is_suspended`) is set by a super admin in `manage/users/`. A suspended user **can't log in or refresh**, and an access token they already hold is refused at once (401 `account_suspended`). This is one small check in `apps/accounts/authentication.py`.

### Djoser configuration

```python
DOMAIN = env_str("FRONTEND_DOMAIN", "localhost:5173")   # used in email links
SITE_NAME = "UniFlow"

DJOSER = {
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SEND_ACTIVATION_EMAIL": True,
    "ACTIVATION_URL": "verify-email/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "reset-password/{uid}/{token}",
    "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": False,
    "HIDE_USERS": True,
    "SERIALIZERS": {
        "user_create_password_retype": "apps.accounts.serializers.UserCreateSerializer",
    },
    # is_staff is only true for super admins, so IsAdminUser means "super admin".
    "PERMISSIONS": {
        "user_list": ["rest_framework.permissions.IsAdminUser"],
        "user_delete": ["rest_framework.permissions.IsAdminUser"],   # Djoser would hard-delete
        "set_username": ["rest_framework.permissions.IsAdminUser"],  # would bypass the domain rule
        "username_reset": ["rest_framework.permissions.IsAdminUser"],
        "username_reset_confirm": ["rest_framework.permissions.IsAdminUser"],
    },
}
```

### Login tokens (SimpleJWT)

| Setting | Value |
|---|---|
| Access token lifetime | 15 minutes |
| Refresh token lifetime | 14 days |
| `ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION` | `True`: each refresh returns a new refresh token, and the old one stops working |
| Authentication class | `rest_framework_simplejwt.authentication.JWTAuthentication` (`Authorization: Bearer <access>`) |

**Where the tokens live (website):**

- The **access token** is kept only in the website's memory. It is lost on page reload and restored through refresh.
- The **refresh token** is in a **secure httpOnly cookie** named `uniflow_refresh`, set by `jwt/create/`. It uses `SameSite=Lax`, the path `/api/v1/auth/jwt/`, and HTTPS only outside development. Page scripts can never read it, and other websites can't send it.
- `apps/accounts/cookie_jwt.py` is SimpleJWT's own login and refresh views with the refresh token moved into that cookie, plus `jwt/logout/`, which cancels it and deletes the cookie.

**Flow:**

1. `POST jwt/create/ {email, password}` returns `{access}` and sets the cookie.
2. Every request sends `Authorization: Bearer <access>`.
3. On a 401, or when the page first loads, `POST jwt/refresh/` sends the cookie and gets a new `{access}`. The cookie is rotated.
4. `POST jwt/logout/` cancels the refresh token and deletes the cookie.

The mobile app (later) can send `{refresh}` in the body instead, which `jwt/refresh/` also accepts.

## 13. Authorization: roles → capabilities → scope [MVP]

The frontend is **not** the security boundary. Every manage endpoint enforces these rules on the server.

### Capabilities (MVP)

A capability is a named permission to manage one kind of resource. Every capability is computed in one place, `accounts.capabilities.capabilities_for(user) -> dict[str, bool]`:

| Capability | student | lecturer | school_staff | university_admin | super_admin |
|---|:-:|:-:|:-:|:-:|:-:|
| `announcements.manage` (official posts) | – | – | ✔ own school | ✔ all | ✔ all |
| `sources.manage` (review, scope, disconnect connected groups) | – | – | ✔ own-school sources | ✔ all | ✔ all |
| `insights.review` (correct or retract AI insights) | – | – | ✔ insights from own-school sources | ✔ all | ✔ all |
| *[Later]* `events.manage`, `documents.manage`, `applications.manage`, `communities.manage` | – | – | ✔ own school | ✔ all | ✔ all |
| `timetable.manage` | – | – | ✔ sections of own-school courses | ✔ all, plus terms | ✔ all, plus terms |
| `academics.manage` (reference data) | – | – | – | ✔ | ✔ |
| `users.manage` (create staff accounts, roles, suspension) | – | – | – | – | ✔ |

**Student actions are not capabilities.** Every logged-in student may connect groups, paste messages, confirm or reject their own timetable changes and set their preferences; these endpoints only ever touch the caller's own data.

| Django admin (back-office; the operator's tool in the pilot) | – | – | – | – | ✔ |

> The code from M2.1 still lists the four [Later] capabilities, and has no `sources.manage` or `insights.review` yet. They are added in the tasks that need them ([11](11-roadmap.md)). In the pilot, sources and insights are handled by the super admin in the Django admin.

A `school_staff` user with no school on their `StaffProfile` gets **no** capabilities, so a half-configured account can do nothing.

**Lecturers** are read-only in the MVP. Like every non-student role, they can see all published content. *[Later]*: publishing to the sections they teach, and editing their own timetable entries.

### Scope: which items a user may manage

In `publishing.policies`:

```python
def manageable_queryset(user, model):      # used by every /manage/ list/detail
    # admins → all rows; school_staff → rows where publisher_school == their school
def publishers_for(user) -> list[PublisherRef]:   # lives in accounts/capabilities.py (M2.1)
    # admins → [university] + all active schools; school_staff → [their school]
def can_manage(user, obj) -> bool          # object-level check, used by DRF permission + `can_edit` flag
def validate_publisher(user, publisher)    # rejects a publisher outside publishers_for(user) → 403
def validate_audience(user, audience)      # school_staff: audience must stay inside their school → 403
```

### The school boundary (MVP rule)

| Role | May manage |
|---|---|
| `university_admin` and `super_admin` | Content from any school or from the university, sent to any audience |
| `school_staff` | Only content that **belongs to** their school **and** is **targeted within** it |
| `lecturer` | Nothing. Read-only in the MVP. |

For a `school_staff` user, "belongs to and targeted within" means all of the following:

- **Publisher:** `publisher_type = school` and `publisher_school` is their school. They can never publish as the university or as another school.
- **Audience:** `schools` must be exactly their own school. Their audience can never be "all students" or include another school. Any `programmes` must belong to their school. `intakes` may be added to narrow the audience further, since they are combined with the school using AND.
- **Items they can manage:** the list and detail views show only items whose `publisher_school` is their school. Other schools' items return 404.
- **Sources and AI insights:** the same boundary, applied through `source.school` (insights through their source). Sources with no school (university-wide groups) are handled by university admins.
- **Timetable:** the same boundary through `section.course.school`.

The server enforces every one of these rules through `validate_publisher`, `validate_audience` and `manageable_queryset`. The staff dashboard shows the school preselected and locked, but that is only a convenience.

**Cross-school content** (for example, a school event open to all students) is published by a **university admin** in the MVP. *[Later]*: a university admin can explicitly grant a school staff member wider reach, for example through a per-user "may target all students" grant or by approving a request. Nothing is granted implicitly.

Equivalent functions exist for sources (scoped by `source.school`) and the timetable (scoped by `section.course.school`).

**How the pieces connect:**

- `me.capabilities` and `me.publishers` are built from these functions.
- The DRF permission class `HasCapability("announcements.manage")` checks the capability.
- Querysets are narrowed by `manageable_queryset`.
- The object-level `CanManageObject` permission calls `can_manage`.

Because the UI and the API use the same functions, the UI can never show an action that the API would refuse.

**Why not Django groups or django-guardian?** The rules depend on the user's school, not on fixed permission lists. One small module of code is easier to test than permission rows stored in the database.

### Later

- **Class representatives:** a student allowed to confirm a timetable change for their whole section.
- **Community managers** (with browsable communities): a `community` publisher type.
- **Lecturer permissions**, as described above.
