"""Settings shared by every environment (dev, test, prod).

Environment-specific modules import everything from here and override only what differs.
Configuration comes from environment variables, optionally loaded from `backend/.env`.
"""

from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from corsheaders.defaults import default_headers as default_cors_headers

from config.env import env_list, env_str, load_env_file

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Real environment variables take precedence over values in backend/.env.
load_env_file(BASE_DIR / ".env")

# Overridden per environment; production requires it from the environment.
SECRET_KEY = ""
DEBUG = False
ALLOWED_HOSTS: list[str] = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "djoser",
    "rest_framework_simplejwt.token_blacklist",  # remembers logged-out / rotated refresh tokens
    # UniFlow apps
    "apps.accounts",
    "apps.academics",
    "apps.audiences",
    "apps.timetable",
    "apps.intelligence",
    "apps.publishing",
]

# Email-based custom user. Must be set before the first migration.
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # CORS must run before CommonMiddleware so preflight responses get CORS headers.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: local MySQL 8.x (see docs/development-setup.md)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env_str("DB_NAME", "uniflow"),
        "USER": env_str("DB_USER", "root"),
        "PASSWORD": env_str("DB_PASSWORD", ""),
        "HOST": env_str("DB_HOST", "127.0.0.1"),
        "PORT": env_str("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            "NAME": "test_uniflow",
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_0900_ai_ci",
        },
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization. Datetimes are stored in UTC; TIME_ZONE is the display/business zone.

LANGUAGE_CODE = "en-us"
TIME_ZONE = env_str("TIME_ZONE", "Asia/Kuala_Lumpur")
USE_I18N = True
USE_TZ = True


# Static files and user uploads

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = Path(env_str("MEDIA_ROOT", str(BASE_DIR / "media")))
# Uploaded files (timetable images, PDFs, spreadsheets) are private: no URL serves MEDIA_ROOT.
MAX_UPLOAD_MB = int(env_str("MAX_UPLOAD_MB", "10"))


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework (see docs/04-api.md)

REST_FRAMEWORK = {
    # "Authorization: Bearer <access token>" (SimpleJWT + a suspended-account check).
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.accounts.authentication.ActiveUserJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/min",
        "user": "300/min",
        # Login, registration and password reset (M1) opt in with throttle_scope = "auth".
        "auth": "10/min",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "UniFlow API",
    "DESCRIPTION": "Student information platform API (web now, mobile later).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Two different role lists exist (all roles vs. roles a super admin can give).
    "ENUM_NAME_OVERRIDES": {
        "UserRoleEnum": "apps.accounts.models.UserRole",
        "StaffRoleEnum": "apps.accounts.serializers.STAFF_ROLE_CHOICES",
    },
}


# Accounts: registration and activation (Djoser). See docs/06-auth-and-permissions.md.

# Only these email domains may self-register (staff accounts are created by a super admin).
ALLOWED_EMAIL_DOMAINS = env_list("ALLOWED_EMAIL_DOMAINS", ["student.aiu.edu.my"])

# Links in emails point to the website (e.g. http://localhost:5173/verify-email/<uid>/<token>).
DOMAIN = env_str("FRONTEND_DOMAIN", "localhost:5173")
SITE_NAME = "UniFlow"

# Development prints emails in the runserver terminal instead of sending them.
EMAIL_BACKEND = env_str("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "UniFlow <no-reply@uniflow.local>")

DJOSER = {
    "LOGIN_FIELD": "email",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SEND_ACTIVATION_EMAIL": True,
    "ACTIVATION_URL": "verify-email/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "reset-password/{uid}/{token}",
    "PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND": False,  # same reply for unknown emails
    "PASSWORD_RESET_CONFIRM_RETYPE": True,  # new password typed twice (re_new_password)
    "SET_PASSWORD_RETYPE": True,
    "HIDE_USERS": True,
    "SERIALIZERS": {
        "user_create_password_retype": "apps.accounts.serializers.UserCreateSerializer",
        "current_user": "apps.accounts.serializers.MeSerializer",  # users/me/
    },
    # is_staff is only true for super admins, so IsAdminUser means "super admin".
    "PERMISSIONS": {
        "user_list": ["rest_framework.permissions.IsAdminUser"],
        "user_delete": ["rest_framework.permissions.IsAdminUser"],  # Djoser would hard-delete
        "set_username": ["rest_framework.permissions.IsAdminUser"],  # would bypass the domain rule
        "username_reset": ["rest_framework.permissions.IsAdminUser"],
        "username_reset_confirm": ["rest_framework.permissions.IsAdminUser"],
    },
}


# Login tokens (SimpleJWT, via djoser.urls.jwt).

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,  # every refresh gives a new refresh token...
    "BLACKLIST_AFTER_ROTATION": True,  # ...and the old one stops working
    "UPDATE_LAST_LOGIN": True,
    # Activated and not suspended (apps/accounts/authentication.py).
    "USER_AUTHENTICATION_RULE": "apps.accounts.authentication.can_log_in",
}


# CORS: only the listed frontend origins may call the API from a browser.

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", [])
# The website's API client sends credentials; safe because origins are an exact list.
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_cors_headers, "x-client")


# Background jobs: Celery with Redis as the broker (see config/celery.py).

# 127.0.0.1, not "localhost": on Windows "localhost" tries IPv6 first, which WSL does not
# forward, and every connection then waits ~20 seconds.
CELERY_BROKER_URL = env_str("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_IGNORE_RESULT = True  # jobs save their results in the database themselves
CELERY_TASK_ACKS_LATE = True  # a job is only removed from Redis after it finishes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # take one job at a time (AI calls are slow)
# Daily jobs, started by Celery Beat (times are Kuala Lumpur time).
CELERY_BEAT_SCHEDULE = {
    "clear-old-messages": {
        "task": "apps.intelligence.tasks.clear_old_messages",
        "schedule": crontab(hour=3, minute=0),  # every night at 03:00
    },
}

# Privacy: message text and timetable files are deleted after this many days.
MESSAGE_RETENTION_DAYS = int(env_str("MESSAGE_RETENTION_DAYS", "60"))


# The AI (apps/intelligence/providers.py). Gemini's free tier for now: Google may use what
# is sent on the free tier to improve its products (decide on the paid tier before real
# students' messages are processed; see docs/PROGRESS.md "Open decisions").

AI_PROVIDER = env_str("AI_PROVIDER", "gemini")  # "gemini", or "fake" in tests
GEMINI_API_KEY = env_str("GEMINI_API_KEY", "")
AI_FAST_MODEL = env_str("AI_FAST_MODEL", "gemini-2.5-flash-lite")  # "is this academic?"
AI_SMART_MODEL = env_str("AI_SMART_MODEL", "gemini-2.5-flash")  # understanding, timetables
