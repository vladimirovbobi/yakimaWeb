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
# CSRF cookie MUST stay JS-readable: the SPA double-submit pattern requires
# JS to copy the cookie value into the X-CSRFToken header. httpOnly here
# would silently break every mutating request from the Next.js frontend.
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "DENY"

# CSP — the Next.js per-request nonce CSP (frontend/middleware.ts) is the
# primary defense. Django responses (admin + email + RSS) inherit the
# strict base.py policy: nonce-based script-src, no 'unsafe-inline' on
# script. Style still allows 'unsafe-inline' because Django admin ships
# inline styles; tightening that is a separate Sprint 9 follow-up.
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'strict-dynamic'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "data:")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_INCLUDE_NONCE_IN = ("script-src",)

# ─── Email — Postmark required in prod ─────────────────────────────────
if not env("POSTMARK_SERVER_TOKEN", default=""):
    raise RuntimeError(
        "POSTMARK_SERVER_TOKEN is required in production. "
        "Set it in Railway/Fly secrets."
    )
EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"

# ─── Webhook secrets must be present in prod ────────────────────────────
if not env("DELIVERY_WEBHOOK_SECRET", default=""):
    raise RuntimeError(
        "DELIVERY_WEBHOOK_SECRET is required in production. "
        "Set it in Railway/Fly secrets and mirror it into the delivery service."
    )
