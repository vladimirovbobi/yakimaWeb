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
)
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
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "django_extensions",
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
    "apps.operations",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ──────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
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
LOGIN_REDIRECT_URL = "core:profile"
LOGOUT_REDIRECT_URL = "core:home"

# ─── allauth ─────────────────────────────────────────────────────────────
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
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
ANYMAIL = {"POSTMARK_SERVER_TOKEN": env("POSTMARK_SERVER_TOKEN", default="")}

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
