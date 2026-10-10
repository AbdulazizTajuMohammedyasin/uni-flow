"""Production settings. Every secret and host must come from the environment.

Hardened for being online (M9.5): `manage.py check --deploy` is clean with these settings
(CI checks it). nginx sits in front of Django and handles HTTPS (docs/10).
"""

from config.env import env_bool, env_list, env_str

from .base import *  # noqa: F401,F403
from .base import DATABASES

SECRET_KEY = env_str("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

# Reuse database connections between requests.
DATABASES["default"]["CONN_MAX_AGE"] = 60

# --- HTTPS only -----------------------------------------------------------------------------
# nginx receives HTTPS and passes requests on over plain HTTP, telling Django the original
# was HTTPS with this header; without it, the redirect below would loop forever.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)  # http:// → https://
# Health checks from the server itself may use plain HTTP.
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/$"]

# HSTS: browsers remember to only ever use HTTPS for this site. Start small (1 hour) and,
# once HTTPS is confirmed to work, raise DJANGO_HSTS_SECONDS to 31536000 (one year). A
# mistake with a long value can't be undone quickly, because browsers remember it.
SECURE_HSTS_SECONDS = int(env_str("DJANGO_HSTS_SECONDS", "3600"))
# Covers only addresses under UniFlow's own (e.g. *.uniflow.aiu.edu.my), not other sites.
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# "Preload" (the browsers' built-in HTTPS list) is for a whole domain such as aiu.edu.my:
# the university's decision, not UniFlow's. Off on purpose, so its check is silenced.
SECURE_HSTS_PRELOAD = False
SILENCED_SYSTEM_CHECKS = ["security.W021"]

# Cookies only travel over HTTPS (the login refresh cookie already is: see cookie_jwt.py).
SESSION_COOKIE_SECURE = True  # the Django admin login
CSRF_COOKIE_SECURE = True
# The Django admin's forms come from these addresses, e.g. https://uniflow.aiu.edu.my
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])

# Kept from Django's safe defaults (stated so nobody turns them off by accident): no showing
# UniFlow inside another site's frame, no guessing file types, a careful Referer.
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
