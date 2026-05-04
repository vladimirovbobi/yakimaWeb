"""Dev settings — debug on, console email, debug toolbar (only outside tests)."""
import os
import sys

from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Lighter Axes in dev
AXES_FAILURE_LIMIT = 100

# Debug toolbar — skip during pytest (it confuses the test client URL resolver)
_RUNNING_TESTS = "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST")
if not _RUNNING_TESTS:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
    INTERNAL_IPS = ["127.0.0.1"]
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda req: DEBUG}
