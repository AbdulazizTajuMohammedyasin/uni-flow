"""Settings shared by every environment (dev, test, prod).

Environment-specific modules import everything from here and override only what differs.
Configuration comes from environment variables, optionally loaded from `backend/.env`.
"""

from pathlib import Path

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
    # UniFlow apps
    "apps.accounts",
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


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework (see docs/04-api.md)

REST_FRAMEWORK = {
    # JWT authentication arrives in M1.6; until then only public (AllowAny) endpoints work.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
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
}


# CORS: only the listed frontend origins may call the API from a browser.

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", [])
# Needed from M1.6 for the httpOnly refresh-token cookie; safe because origins are an exact list.
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_cors_headers, "x-client")
