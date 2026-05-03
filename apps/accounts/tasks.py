"""Celery tasks: verify single license, scheduled re-verify all."""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import CheckTrigger, RealtorProfile, VerificationStatus
from .services.verification import run_verification

log = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(),  # we explicitly handle retries via verification.run_verification logic
    retry_backoff=True,
    max_retries=3,
)
def verify_license_task(self, profile_id: int, *, triggered_by: str = CheckTrigger.SIGNUP) -> str:
    """Verify a single realtor profile via ARELLO."""
    try:
        profile = RealtorProfile.objects.select_related("user").get(pk=profile_id)
    except RealtorProfile.DoesNotExist:
        log.warning("verify_license_task: profile %s gone", profile_id)
        return "missing"

    check = run_verification(profile, triggered_by=triggered_by)
    return check.status


@shared_task
def reverify_all_active_realtors() -> int:
    """Beat task — re-verify any realtor not checked in N days."""
    cutoff = timezone.now() - timedelta(days=settings.ARELLO_VERIFICATION_INTERVAL_DAYS)
    qs = RealtorProfile.objects.filter(
        verification_status__in=[VerificationStatus.VERIFIED, VerificationStatus.PENDING],
    ).exclude(checks__created_at__gte=cutoff)
    count = 0
    for p in qs.iterator():
        verify_license_task.delay(p.pk, triggered_by=CheckTrigger.SCHEDULED)
        count += 1
    log.info("reverify_all_active_realtors queued %d", count)
    return count
