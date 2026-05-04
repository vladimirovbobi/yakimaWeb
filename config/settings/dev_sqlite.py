"""Local dev settings without Docker — SQLite + in-memory cache.

Use when Docker Desktop isn't available. Runs entirely on the host.
DJANGO_SETTINGS_MODULE=config.settings.dev_sqlite
"""
import os
import sys
from pathlib import Path

from .base import *  # noqa: F401, F403
from .base import BASE_DIR, INSTALLED_APPS, MIDDLEWARE

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# SQLite — zero setup
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(BASE_DIR) / "dev.sqlite3",
    }
}

# In-memory cache + DB-backed sessions (no Redis required)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "yw-dev",
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Celery → eager mode (run tasks synchronously in-process)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Lighter throttles + axes in dev
AXES_FAILURE_LIMIT = 100

# CSRF trusted for the Next.js dev server origin
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8001",
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Debug toolbar — skip during pytest
_RUNNING_TESTS = "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST")
if not _RUNNING_TESTS:
    try:
        import debug_toolbar  # noqa: F401
        INSTALLED_APPS += ["debug_toolbar"]
        MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
        INTERNAL_IPS = ["127.0.0.1"]
        DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda req: DEBUG}
    except ImportError:
        pass
