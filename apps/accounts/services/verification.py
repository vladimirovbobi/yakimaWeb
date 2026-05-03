"""Business logic for license verification — wraps ARELLO + writes LicenseCheck audit row."""
import logging

from django.utils import timezone

from ..models import (CheckTrigger, LicenseCheck, RealtorProfile,
                      VerificationStatus)
from .arello import (ARelloDown, ARelloError, ARelloRateLimited,
                     LicenseRecord, verify_license)

log = logging.getLogger(__name__)


# ARELLO status → our internal status
_STATUS_MAP = {
    "ACTIVE":      VerificationStatus.VERIFIED,
    "INACTIVE":    VerificationStatus.EXPIRED,
    "EXPIRED":     VerificationStatus.EXPIRED,
    "SUSPENDED":   VerificationStatus.SUSPENDED,
    "REVOKED":     VerificationStatus.REVOKED,
    "SURRENDERED": VerificationStatus.REVOKED,
    "NOT_FOUND":   VerificationStatus.NOT_FOUND,
}


def run_verification(
    profile: RealtorProfile,
    *,
    triggered_by: str = CheckTrigger.SCHEDULED,
) -> LicenseCheck:
    """Verify `profile` against ARELLO. Always writes a LicenseCheck row."""
    log_kwargs = {"profile_id": profile.pk, "trigger": triggered_by}

    try:
        rec: LicenseRecord = verify_license(
            license_number=profile.license_number,
            last_name=profile.user.full_name.split()[-1] if profile.user.full_name else "",
        )
    except ARelloRateLimited:
        log.warning("ARELLO rate-limited", extra=log_kwargs)
        return LicenseCheck.objects.create(
            profile=profile, status="RATE_LIMITED",
            source="arello", triggered_by=triggered_by,
            error="ARELLO rate-limited; will retry.",
        )
    except ARelloDown as e:
        log.warning("ARELLO down: %s", e, extra=log_kwargs)
        return LicenseCheck.objects.create(
            profile=profile, status="DOWN",
            source="arello", triggered_by=triggered_by,
            error=str(e),
        )
    except ARelloError as e:
        log.error("ARELLO error: %s", e, extra=log_kwargs)
        profile.verification_status = VerificationStatus.ERROR
        profile.save(update_fields=["verification_status"])
        return LicenseCheck.objects.create(
            profile=profile, status="ERROR",
            source="arello", triggered_by=triggered_by,
            error=str(e),
        )

    # Map → internal status, persist
    new_status = _STATUS_MAP.get(rec.status, VerificationStatus.ERROR)
    profile.verification_status = new_status
    profile.license_expires = rec.expiration_date
    if new_status == VerificationStatus.VERIFIED:
        profile.verified_at = timezone.now()
    profile.save(update_fields=["verification_status", "license_expires", "verified_at"])

    return LicenseCheck.objects.create(
        profile=profile,
        status=rec.status,
        raw_response=rec.raw or {},
        source="arello",
        triggered_by=triggered_by,
    )
