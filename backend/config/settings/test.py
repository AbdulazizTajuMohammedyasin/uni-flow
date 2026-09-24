"""Settings for the automated test suite (pytest-django, from M0.5)."""

from .base import *  # noqa: F401,F403

SECRET_KEY = "django-insecure-test-only"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# Fast, insecure hashing is fine for tests and makes user creation much quicker.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
