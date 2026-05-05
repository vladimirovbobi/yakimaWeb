"""Delivery service settings — env-driven, mirrors the Django side where they overlap."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Identity
    service_name: str = "yakimaweb-delivery"
    environment: str = "dev"

    # Auth — must match Django SECRET_KEY for JWT verification.
    # No defaults: a missing/sentinel secret in any non-dev environment is a
    # production misconfiguration. The post-init check below blocks startup.
    django_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    delivery_webhook_secret: str = ""

    def model_post_init(self, __context) -> None:  # noqa: D401
        """Refuse to boot in prod with placeholder/empty secrets."""
        env = (self.environment or "").lower()
        is_prod = env not in {"dev", "development", "test"}
        sentinels = {"", "change-me", "change-me-too", "changeme"}
        if is_prod:
            if self.django_secret_key in sentinels:
                raise RuntimeError(
                    "DJANGO_SECRET_KEY must be set to the real Django secret in prod."
                )
            if self.delivery_webhook_secret in sentinels:
                raise RuntimeError(
                    "DELIVERY_WEBHOOK_SECRET must be set to a strong random secret in prod."
                )
        # In dev we still want a usable value so the service can boot.
        if self.django_secret_key in sentinels:
            self.django_secret_key = os.environ.get("DJANGO_SECRET_KEY") or "dev-only-do-not-use"
        if self.delivery_webhook_secret in sentinels:
            self.delivery_webhook_secret = (
                os.environ.get("DELIVERY_WEBHOOK_SECRET") or "dev-only-do-not-use"
            )

    # Database — same Postgres as Django
    database_url: str = "postgresql+asyncpg://yakimaweb:yakimaweb@db:5432/yakimaweb"

    # Storage — R2 in prod, local FS in dev
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_endpoint_url: str = ""
    aws_storage_bucket_name: str = "yakimaweb-deliveries"
    aws_s3_region: str = "auto"

    # Limits
    max_file_size_image: int = 50 * 1024 * 1024
    max_file_size_archive: int = 500 * 1024 * 1024
    max_file_size_document: int = 25 * 1024 * 1024
    max_file_size_workflow: int = 5 * 1024 * 1024
    max_files_per_package: int = 200
    signed_url_ttl_seconds: int = 5 * 60

    # Webhook back to Django
    django_webhook_url: str = "http://api:8000/api/v1/delivery/webhooks/finalize/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
