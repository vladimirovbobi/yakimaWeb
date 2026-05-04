"""Production settings — security headers, S3 storage, no debug.

Sentry init now lives in base.py (auto-engages on SENTRY_DSN presence).
"""
from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

# ─── Security ───────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

# CSP (basic — tighten in Phase 8)
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # tighten when Vite hashes wired
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'",)

# ─── Email — Postmark required in prod ─────────────────────────────────
if not env("POSTMARK_SERVER_TOKEN", default=""):
    raise RuntimeError(
        "POSTMARK_SERVER_TOKEN is required in production. "
        "Set it in Railway/Fly secrets."
    )
EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"
