"""Production settings. Every secret and host must come from the environment.

Security hardening (HTTPS redirects, HSTS, secure cookies, ...) is added in M10.6.
"""

from config.env import env_list, env_str

from .base import *  # noqa: F401,F403
from .base import DATABASES

SECRET_KEY = env_str("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

# Reuse database connections between requests.
DATABASES["default"]["CONN_MAX_AGE"] = 60
