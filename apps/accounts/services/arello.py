"""ARELLO API client. Spec: docs/research/arello-api-notes.md.

Sandbox-first. Mockable in tests via the `responses` library.
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import requests
from django.conf import settings

log = logging.getLogger(__name__)

Status = Literal[
    "ACTIVE", "EXPIRED", "SUSPENDED", "REVOKED",
    "INACTIVE", "SURRENDERED", "NOT_FOUND",
]


class ARelloError(Exception):
    """Base ARELLO error."""


class ARelloRateLimited(ARelloError):
    """HTTP 429 from ARELLO."""


class ARelloDown(ARelloError):
    """Network failure or 5xx from ARELLO."""


class ARelloConfigError(ARelloError):
    """Missing API key or base URL."""


@dataclass
class LicenseRecord:
    license_number: str
    jurisdiction: str
    license_type: str
    status: Status
    first_name: str = ""
    last_name: str = ""
    expiration_date: date | None = None
    raw: dict = field(default_factory=dict)

    @classmethod
    def not_found(cls, license_number: str, jurisdiction: str = "WA") -> "LicenseRecord":
        return cls(
            license_number=license_number, jurisdiction=jurisdiction,
            license_type="", status="NOT_FOUND",
        )


def verify_license(
    license_number: str,
    last_name: str = "",
    jurisdiction: str = "WA",
    *,
    timeout: int = 10,
) -> LicenseRecord:
    """Synchronous ARELLO call. Raise on transport errors; return NOT_FOUND on count=0."""
    if not settings.ARELLO_API_KEY:
        raise ARelloConfigError("ARELLO_API_KEY not configured")

    url = f"{settings.ARELLO_BASE_URL.rstrip('/')}/api/v2/search"
    headers = {"Authorization": f"Bearer {settings.ARELLO_API_KEY}",
               "Accept": "application/json"}
    params = {"jurisdiction": jurisdiction, "license_number": license_number.strip().upper()}
    if last_name:
        params["last_name"] = last_name

    try:
        r = requests.get(url, headers=headers, params=params, timeout=timeout)
    except requests.RequestException as e:
        log.warning("ARELLO transport error: %s", e)
        raise ARelloDown(str(e)) from e

    if r.status_code == 429:
        raise ARelloRateLimited()
    if r.status_code >= 500:
        raise ARelloDown(f"HTTP {r.status_code}")
    if r.status_code != 200:
        raise ARelloError(f"HTTP {r.status_code}: {r.text[:240]}")

    try:
        data = r.json()
    except ValueError as e:
        raise ARelloError(f"Non-JSON response: {r.text[:240]}") from e

    if data.get("count", 0) == 0 or not data.get("results"):
        return LicenseRecord.not_found(license_number, jurisdiction)

    rec = data["results"][0]
    exp = None
    if rec.get("expiration_date"):
        try:
            exp = date.fromisoformat(rec["expiration_date"])
        except (ValueError, TypeError):
            exp = None
    return LicenseRecord(
        license_number=rec.get("license_number", license_number),
        jurisdiction=rec.get("jurisdiction", jurisdiction),
        license_type=rec.get("license_type", ""),
        status=rec.get("status", "INACTIVE"),
        first_name=rec.get("first_name", ""),
        last_name=rec.get("last_name", last_name),
        expiration_date=exp,
        raw=rec,
    )
