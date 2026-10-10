"""Settings for the automated test suite (pytest-django, from M0.5)."""

from .base import *  # noqa: F401,F403

SECRET_KEY = "django-insecure-test-only-key-at-least-32-bytes-long"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# Fast, insecure hashing is fine for tests and makes user creation much quicker.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Tests never need Redis: jobs run immediately in the same process, and errors surface.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Tests never call the real AI (no key, no quota used): see providers.FakeProvider.
AI_PROVIDER = "fake"
# One model each, so a fake "too many requests" reaches the retry logic (fallback tests
# set their own lists).
AI_FAST_MODELS, AI_SMART_MODELS = [AI_FAST_MODEL], [AI_SMART_MODEL]  # noqa: F405
