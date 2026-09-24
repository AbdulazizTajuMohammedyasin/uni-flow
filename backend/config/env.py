"""Minimal environment configuration helpers (standard library only).

`load_env_file` reads simple `KEY=VALUE` lines from a `.env` file into `os.environ`
without overriding variables that are already set, so real environment variables
always win. The `env_*` accessors read typed values and fail loudly when a required
variable is missing.

Supported `.env` syntax: blank lines, `# comments`, an optional `export ` prefix,
and values optionally wrapped in single or double quotes. Inline comments after a
value are NOT supported (the `#` would become part of the value).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

_MISSING = object()

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def load_env_file(path: Path) -> None:
    """Load `KEY=VALUE` pairs from `path` into `os.environ` if the file exists."""
    if not path.is_file():
        return

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()

        key, separator, value = line.partition("=")
        key = key.strip()
        if not separator or not key:
            raise ImproperlyConfigured(f"{path}:{line_number}: expected KEY=VALUE, got {raw_line!r}")

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def env_str(name: str, default=_MISSING) -> str:
    """Return the variable as a string; raise if it is missing and no default is given."""
    value = os.environ.get(name)
    if value is None:
        if default is _MISSING:
            raise ImproperlyConfigured(f"Missing required environment variable: {name}")
        return default
    return value


def env_bool(name: str, default=_MISSING) -> bool:
    """Return the variable as a boolean (true/false, 1/0, yes/no, on/off)."""
    value = os.environ.get(name)
    if value is None:
        if default is _MISSING:
            raise ImproperlyConfigured(f"Missing required environment variable: {name}")
        return default

    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise ImproperlyConfigured(f"Environment variable {name} must be a boolean, got {value!r}")


def env_list(name: str, default=_MISSING) -> list[str]:
    """Return a comma-separated variable as a list of non-empty, stripped strings."""
    value = os.environ.get(name)
    if value is None:
        if default is _MISSING:
            raise ImproperlyConfigured(f"Missing required environment variable: {name}")
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]
