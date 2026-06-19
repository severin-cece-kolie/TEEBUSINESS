"""Project paths, environment loading, and shared parsing helpers."""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Always load the repository .env explicitly. WSGI processes do not
# necessarily start in the project directory. ``override=True`` preserves the
# established behavior where this file wins over generic IDE/shell variables.
load_dotenv(BASE_DIR / '.env', override=True)


def env(name, default=''):
    """Return a raw environment value using the project's loaded .env."""
    return os.environ.get(name, default)


def env_bool(name, default=False):
    """Parse booleans exactly as the previous settings module did."""
    return env(name, 'True' if default else 'False') == 'True'


def env_int(name, default):
    return int(env(name, default))


def env_float(name, default):
    return float(env(name, default))


def env_list(name, default=''):
    return [item.strip() for item in env(name, default).split(',') if item.strip()]

