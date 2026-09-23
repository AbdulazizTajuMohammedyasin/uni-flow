# 06 — Authentication & Authorization

## 12. Authentication architecture [MVP]

### Libraries: Djoser and SimpleJWT

| Library | Responsibility |
|---|---|
| **Djoser** | The account lifecycle: registration, activation email, resending activation, the "me" endpoint, password reset and change. It uses `django-templated-mail`, which Djoser installs itself. |
| **SimpleJWT** | Issuing, rotating, verifying and blacklisting tokens |
| **UniFlow** (`apps/accounts`) | The email domain rule, the web cookie transport, logout, suspension, capabilities, and staff user management |

UniFlow does **not** include `djoser.urls` or `djoser.urls.jwt`. It registers its own subclass of Djoser's `UserViewSet` at `auth/users/`, and cookie-aware SimpleJWT subclasses at `auth/jwt/create|refresh|verify/`, plus `auth/jwt/logout/`.

### Registration

1. `POST /api/v1/auth/users/` takes `{email, full_name, password, re_password}`.
2. The email domain must be in `ALLOWED_EMAIL_DOMAINS`. `UserCreateSerializer` enforces this.
3. The user is created through `accounts.services.create_user()` with `role = student` and `is_active = false`. The student profile is created at the same time. **`is_active` means "email verified".** Djoser emails a link to `https://<FRONTEND_DOMAIN>/verify-email/{uid}/{token}`. The frontend page sends `{uid, token}` to `users/activation/`.
4. Login before activation fails. A correct password on an inactive account returns 403 `email_not_verified`. A wrong password always returns 401, so the response never reveals whether an email is registered.
5. Students without a complete profile are sent to `/onboarding`.

**Staff accounts:**

- Staff register the same way.
- A `super_admin` then assigns their role and department in the staff dashboard (`/staff/users`).
- The first `super_admin` is created with `createsuperuser`.

**Suspension** uses `is_suspended`, not `is_active`. Otherwise a blocked user could reactivate their own account through `resend_activation`. Both the JWT authentication class and the login serializer reject suspended users.

### Djoser configuration

```python
DOMAIN = env("FRONTEND_DOMAIN")
SITE_NAME = "UniFlow"

DJOSER = {
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SEND_ACTIVATION_EMAIL": True,
    "ACTIVATION_URL": "verify-email/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "reset-password/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": False,
    "SET_PASSWORD_RETYPE": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "HIDE_USERS": True,
    "SERIALIZERS": {
        "user_create_password_retype": "apps.accounts.serializers.UserCreateSerializer",
        "user": "apps.accounts.serializers.UserSerializer",
        "current_user": "apps.accounts.serializers.MeSerializer",   # profile, profile_complete, capabilities, publishers
    },
    "PERMISSIONS": {
        # is_staff is true only for super_admin, so IsAdminUser means "super admin".
        "user_list": ["rest_framework.permissions.IsAdminUser"],
        "user_delete": ["rest_framework.permissions.IsAdminUser"],      # Djoser's default is a hard delete. See the MVP note below.
        "set_username": ["rest_framework.permissions.IsAdminUser"],     # changing an email would bypass the domain rule
        "username_reset": ["rest_framework.permissions.IsAdminUser"],
        "username_reset_confirm": ["rest_framework.permissions.IsAdminUser"],
    },
    "EMAIL": {
        "activation": "apps.accounts.emails.ActivationEmail",
        "password_reset": "apps.accounts.emails.PasswordResetEmail",
    },
}
```

`UniFlowUserViewSet` changes Djoser's behaviour in two ways:

- It applies `throttle_scope = "auth"` to the public actions.
- After `set_password` or `reset_password_confirm`, it revokes every outstanding refresh token for the user.

**Account deletion:** in the MVP, only admins can delete accounts. *[Later]*, `perform_destroy` will anonymize the account instead of deleting it, and self-service deletion will be opened to users.

### JWT settings (SimpleJWT)

| Setting | Value |
|---|---|
| Access token lifetime | 15 minutes |
| Refresh token lifetime | 14 days |
| `ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION` | `True` |
| Claims | `user_id`. The server always reloads the user, so the role is never trusted from the token. |

### Token transport (one API, two clients)

| | Web | Mobile [Later] |
|---|---|---|
| How the client identifies itself | The `X-Client: web` header | No header |
| `jwt/create/` response | `{access}` plus `Set-Cookie: uf_refresh=…; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth/jwt/` | `{access, refresh}` |
| Where the refresh token is stored | The httpOnly cookie | `expo-secure-store` |
| Refresh | `POST jwt/refresh/`, which sends the cookie | `POST jwt/refresh/ {refresh}` |

**CSRF protection.** Only `jwt/refresh/` and `jwt/logout/` read the cookie. They require the `X-Client: web` header and check `Origin` against `CSRF_TRUSTED_ORIGINS`. In production, the frontend and the API run on the same site, for example `uniflow.example.edu` and `api.uniflow.example.edu`.

**Logout.** `POST jwt/logout/` blacklists the refresh token and clears the cookie.

## 13. Authorization: roles → capabilities → scope [MVP]

The frontend is **not** the security boundary. Every manage endpoint enforces these rules on the server.

### Capabilities (MVP)

A capability is a named permission to manage one kind of resource. Every capability is computed in one place, `accounts.capabilities.capabilities_for(user) -> dict[str, bool]`:

| Capability | student | lecturer | department_staff | university_admin | super_admin |
|---|:-:|:-:|:-:|:-:|:-:|
| `announcements.manage` | – | – | ✔ own dept | ✔ all | ✔ all |
| `events.manage` | – | – | ✔ own dept | ✔ all | ✔ all |
| `documents.manage` | – | – | ✔ own dept | ✔ all | ✔ all |
| `applications.manage` | – | – | ✔ own dept | ✔ all | ✔ all |
| `communities.manage` | – | – | ✔ own-dept communities | ✔ all | ✔ all |
| `timetable.manage` | – | – | ✔ sections of own-dept courses | ✔ all, plus terms | ✔ all, plus terms |
| `academics.manage` (reference data) | – | – | – | ✔ | ✔ |
| `users.manage` (roles, suspension) | – | – | – | – | ✔ |
| Django admin (back-office) | – | – | – | – | ✔ |

A `department_staff` user with no department on their `StaffProfile` gets **no** capabilities, so a half-configured account can do nothing.

**Lecturers** are read-only in the MVP. Like every non-student role, they can see all published content. *[Later]*: publishing to the sections they teach, and editing their own timetable entries.

### Scope: which items a user may manage

In `publishing.policies`:

```python
def manageable_queryset(user, model):      # used by every /manage/ list/detail
    # admins → all rows; department_staff → rows where publisher_department == their dept
def publishers_for(user) -> list[PublisherRef]:
    # admins → [university] + all active departments; department_staff → [their department]
def can_manage(user, obj) -> bool          # object-level check, used by DRF permission + `can_edit` flag
def validate_publisher(user, publisher)    # rejects a publisher outside publishers_for(user) → 403
def validate_audience(user, audience)      # department_staff: audience must stay inside their department → 403
```

### The department boundary (MVP rule)

| Role | May manage |
|---|---|
| `university_admin` and `super_admin` | Content from any department or from the university, sent to any audience |
| `department_staff` | Only content that **belongs to** their department **and** is **targeted within** it |
| `lecturer` | Nothing. Read-only in the MVP. |

For a `department_staff` user, "belongs to and targeted within" means all of the following:

- **Publisher:** `publisher_type = department` and `publisher_department` is their department. They can never publish as the university or as another department.
- **Audience:** `departments` must be exactly their own department. Their audience can never be "all students" or include another department. Any `programmes` must belong to their department. `intakes` may be added to narrow the audience further, since they are combined with the department using AND.
- **Items they can manage:** the list and detail views show only items whose `publisher_department` is their department. Other departments' items return 404.
- **Documents** have no audience in the MVP, so the rule applies through the publisher only. Every logged-in user can still read published documents, as decided.
- **Communities and timetable:** the same boundary, applied through `community.department` and `section.course.department`.

The server enforces every one of these rules through `validate_publisher`, `validate_audience` and `manageable_queryset`. The staff dashboard shows the department preselected and locked, but that is only a convenience.

**Cross-department content** (for example, a department event open to all students) is published by a **university admin** in the MVP. *[Later]*: a university admin can explicitly grant a department staff member wider reach, for example through a per-user "may target all students" grant or by approving a request. Nothing is granted implicitly.

Equivalent functions exist for communities (scoped by `community.department`) and the timetable (scoped by `section.course.department`).

**How the pieces connect:**

- `me.capabilities` and `me.publishers` are built from these functions.
- The DRF permission class `HasCapability("announcements.manage")` checks the capability.
- Querysets are narrowed by `manageable_queryset`.
- The object-level `CanManageObject` permission calls `can_manage`.

Because the UI and the API use the same functions, the UI can never show an action that the API would refuse.

**Why not Django groups or django-guardian?** The rules depend on the user's department, not on fixed permission lists. One small module of code is easier to test than permission rows stored in the database.

### Later

- **Community managers:** a new `community` publisher type, and a `CommunityManager` model granting management of one community only.
- **Approval workflow** for community posts addressed to all students.
- **Lecturer permissions**, as described above.
