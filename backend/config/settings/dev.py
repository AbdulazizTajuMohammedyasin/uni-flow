"""Local development settings (the default for manage.py)."""

import os

from config.env import env_bool, env_list, env_str

from .base import *  # noqa: F401,F403

SECRET_KEY = env_str("DJANGO_SECRET_KEY", "django-insecure-dev-only-placeholder")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
# Inngest's dev server on this computer, unless INNGEST_DEV says otherwise.
INNGEST_DEV = INNGEST_DEV or "INNGEST_DEV" not in os.environ  # noqa: F405
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"]
)
