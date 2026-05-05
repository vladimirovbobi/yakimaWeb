"""
Base Django settings — shared across dev/prod.
Override per-env in dev.py / prod.py.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_OTP_REQUIRED_FOR_STAFF=(bool, True),
    USE_S3=(bool, False),
    GEMINI_DAILY_SPEND_CAP_USD=(float, 50.00),
    ARELLO_VERIFICATION_INTERVAL_DAYS=(int, 30),
    FEATURE_AI_TOOLS=(bool, False),
    FEATURE_MARKETPLACE=(bool, False),
    FEATURE_FORUM=(bool, False),
    # COEP is conservative — only flips on for /api+/admin etc when enabled.
    ENABLE_COEP=(bool, False),
)
ENABLE_COEP = env("ENABLE_COEP")
environ.Env.read_env(BASE_DIR / ".env")

# ─── Core ────────────────────────────────────────────────────────────────
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# ─── Apps ────────────────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "django_htmx",
    "django_celery_beat",
    "django_celery_results",
    "treebeard",
    "anymail",
    # Auth
    "allauth",
    "allauth.account",
    # 2FA
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    # Throttling
    "axes",
    # DRF stack (Sprint 0c split architecture per ADR-0005)
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.moderation",
    "apps.audit",
    "apps.admin_tools",
    "apps.content",
    "apps.tools",
    "apps.forum",
    "apps.marketplace",
    "apps.notifications",
    "apps.operations",
    "apps.delivery",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ──────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "csp.middleware.CSPMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.core.middleware.csrf_cookie.EnsureCSRFCookieMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "axes.middleware.AxesMiddleware",
    "apps.audit.middleware.AccessLogMiddleware",
    "apps.admin_tools.middleware.AdminIPAllowlistMiddleware",
    "apps.accounts.middleware.session_fingerprint.SessionFingerprintMiddleware",
    "apps.core.middleware.security_headers.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ─── Templates ───────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_meta",
            ],
        },
    },
]

# ─── Database ────────────────────────────────────────────────────────────
DATABASES = {"default": env.db("DATABASE_URL")}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Cache + Sessions (Redis) ────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL"),
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_COOKIE_NAME = "yw_sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# ─── Auth ────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "account_login"
# Next.js owns the dashboard + landing post-login (ADR-0005). allauth flows return to /api host
# so these are absolute paths (Caddy passes them to the frontend container in the split deploy,
# while in API-only smoke tests Django simply returns the absolute URL in Location).
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ─── allauth ─────────────────────────────────────────────────────────────
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # custom User has no `username`
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = False
ACCOUNT_RATE_LIMITS = {"login_failed": "5/5m", "signup": "3/h"}
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_ADAPTER = "apps.accounts.adapters.AccountAdapter"

# ─── django-otp ──────────────────────────────────────────────────────────
OTP_TOTP_ISSUER = "Yakima Real Estate Hub"
OTP_LOGIN_URL = "/admin/login/"
DJANGO_OTP_REQUIRED_FOR_STAFF = env("DJANGO_OTP_REQUIRED_FOR_STAFF")

# ─── django-axes ─────────────────────────────────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True

# ─── Email ───────────────────────────────────────────────────────────────
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="hello@yakimaweb.com")
SERVER_EMAIL = env("SERVER_EMAIL", default="ops@yakimaweb.com")
POSTMARK_SERVER_TOKEN = env("POSTMARK_SERVER_TOKEN", default="")
ANYMAIL = {"POSTMARK_SERVER_TOKEN": POSTMARK_SERVER_TOKEN}

# Delivery service webhook (Sprint 6) — HMAC-signed callback from the
# FastAPI delivery container. When empty, dev mode accepts unsigned webhooks.
DELIVERY_WEBHOOK_SECRET = env("DELIVERY_WEBHOOK_SECRET", default="")

# Graceful dev fallback — no Postmark token means console backend.
# In prod.py we raise if POSTMARK_SERVER_TOKEN is missing.
if not POSTMARK_SERVER_TOKEN:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ─── Storage ─────────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static" / "dist"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

USE_S3 = env("USE_S3")
if USE_S3:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="auto")
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/" if AWS_S3_CUSTOM_DOMAIN else f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
else:
    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "media"

# ─── i18n ────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True

# ─── Celery ──────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 5 * 60
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ─── AI provider ─────────────────────────────────────────────────────────
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
GEMINI_MODERATION_MODEL = env("GEMINI_MODERATION_MODEL", default="gemini-2.5-flash")
GEMINI_TOOLS_MODEL = env("GEMINI_TOOLS_MODEL", default="gemini-2.5-pro")
GEMINI_DAILY_SPEND_CAP_USD = env("GEMINI_DAILY_SPEND_CAP_USD")

# Flyer-generator backend selector. Prototype path uses the local Claude Code
# subscription via subprocess; commercializing flips this to "gemini" or
# "anthropic_api" with no other code changes. See apps/tools/services/flyer_generator/.
FLYER_BACKEND = env("FLYER_BACKEND", default="claude_cli")

# ─── License verification (ARELLO) ───────────────────────────────────────
ARELLO_BASE_URL = env("ARELLO_BASE_URL", default="https://lvws-sandbox.arello.com")
ARELLO_API_KEY = env("ARELLO_API_KEY", default="")
ARELLO_VERIFICATION_INTERVAL_DAYS = env("ARELLO_VERIFICATION_INTERVAL_DAYS")

# ─── Admin lockdown ──────────────────────────────────────────────────────
ADMIN_IP_ALLOWLIST = env.list("ADMIN_IP_ALLOWLIST", default=["127.0.0.1", "::1"])

# ─── Feature flags ───────────────────────────────────────────────────────
FEATURE_AI_TOOLS = env("FEATURE_AI_TOOLS")
FEATURE_MARKETPLACE = env("FEATURE_MARKETPLACE")
FEATURE_FORUM = env("FEATURE_FORUM")

# ─── Site meta (used in templates + OG tags) ─────────────────────────────
SITE_NAME = "Yakima Real Estate Hub"
SITE_TAGLINE = "Central Washington's home for realtors, services, and market truth."
SITE_DESCRIPTION = (
    "Verified Washington realtors, trusted local service providers, and a real "
    "community for buying and selling in Yakima and Central Washington."
)

# ─── DRF (Sprint 0c — split architecture per ADR-0005) ──────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.core.api.authentication.JWTCookieAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "300/minute",
        "vote": "30/minute",
        "lead": "5/hour",
        "ai_tool": "10/hour",
        "image_compressor": "60/minute",  # Local CPU; users batch listing photos
        "comment": "30/hour",
        "forum_write": "30/hour",
        "flag": "20/hour",
        "message": "10/minute",
        "upload": "10/hour",
        "featured_anon": "120/minute",    # Public, cached, but still capped
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.api.exceptions.problem_detail_handler",
}

# SimpleJWT — tokens delivered via httpOnly cookies (ADR-0008)
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

JWT_AUTH_COOKIE = "yw_access"
JWT_AUTH_REFRESH_COOKIE = "yw_refresh"
JWT_AUTH_COOKIE_PATH = "/"
JWT_AUTH_REFRESH_COOKIE_PATH = "/api/v1/auth/refresh/"
JWT_AUTH_COOKIE_SAMESITE = "Strict"
JWT_AUTH_COOKIE_SECURE = not DEBUG
JWT_AUTH_COOKIE_HTTPONLY = True

# drf-spectacular — auto-generated OpenAPI 3.1
SPECTACULAR_SETTINGS = {
    "TITLE": "Yakima Real Estate Hub API",
    "DESCRIPTION": "Internal REST API powering the Yakima Real Estate Hub platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/(public/)?v[0-9]+",
    "SERVE_AUTHENTICATION": (
        "apps.core.api.authentication.JWTCookieAuthentication",
    ),
    "SERVERS": [{"url": "http://localhost:8000", "description": "Local"}],
}

# CORS — strict allowlist for the Next.js frontend
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://localhost"],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-request-id",
    "idempotency-key",
)

# CSRF cooperates with the cookie-JWT pattern via double-submit
CSRF_COOKIE_NAME = "yw_csrf"
CSRF_COOKIE_HTTPONLY = False  # double-submit requires JS read of the cookie
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SECURE = not DEBUG

# Content Security Policy (django-csp).
#
# The Next.js frontend ships its CSS via the bundler so we don't strictly need
# 'unsafe-inline' on style-src. We still allow it as a hedge for Tailwind JIT
# fallbacks and Django admin until the strict-only audit lands in Sprint 6.
# The nonce is set by `csp.middleware.CSPMiddleware` and is available in
# Django templates as `{{ request.csp_nonce }}` and on the response header.
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'strict-dynamic'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_INCLUDE_NONCE_IN = ("script-src",)
CSP_OBJECT_SRC = ("'none'",)

# ─── Sentry ──────────────────────────────────────────────────────────────
DJANGO_ENV = env("DJANGO_ENV", default="dev")
SENTRY_DSN = env("SENTRY_DSN", default="")


def _sentry_before_send(event, hint):
    """Strip credentials/PII before sending to Sentry."""
    SCRUB_KEYS = {
        "password", "passwd", "secret", "token", "api_key", "apikey",
        "authorization", "csrf", "session", "access_token", "refresh_token",
        "set-cookie", "cookie",
    }

    def _scrub(obj):
        if isinstance(obj, dict):
            return {
                k: ("[scrubbed]" if k.lower() in SCRUB_KEYS else _scrub(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [_scrub(x) for x in obj]
        return obj

    request = event.get("request") or {}
    if "headers" in request:
        request["headers"] = _scrub(request["headers"])
    if "cookies" in request:
        request["cookies"] = "[scrubbed]"
    if "data" in request:
        request["data"] = _scrub(request["data"])

    extra = event.get("extra") or {}
    event["extra"] = _scrub(extra)
    return event


if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=DJANGO_ENV,
        send_default_pii=False,
        before_send=_sentry_before_send,
    )

# ─── Logging ─────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security": {"level": "INFO", "propagate": True},
        "apps": {"level": "DEBUG" if DEBUG else "INFO", "propagate": True},
    },
}
