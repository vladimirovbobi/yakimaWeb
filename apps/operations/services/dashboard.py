"""Operator dashboard data aggregator. Each func returns a dict for one card."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

User = get_user_model()


def _since(hours: int):
    return timezone.now() - timedelta(hours=hours)


def signups_card() -> dict:
    return {
        "today":      User.objects.filter(created_at__gte=_since(24)).count(),
        "this_week":  User.objects.filter(created_at__gte=_since(24 * 7)).count(),
        "this_month": User.objects.filter(created_at__gte=_since(24 * 30)).count(),
        "realtors":   User.objects.filter(is_realtor=True).count(),
        "vendors":    User.objects.filter(is_vendor=True).count(),
    }


def moderation_card() -> dict:
    from apps.moderation.models import ModerationDecision

    return {
        "queued_24h":   ModerationDecision.objects.filter(action="queue", created_at__gte=_since(24)).count(),
        "removed_24h":  ModerationDecision.objects.filter(action="remove", created_at__gte=_since(24)).count(),
        "approved_24h": ModerationDecision.objects.filter(action="approve", created_at__gte=_since(24)).count(),
        "queue_depth":  ModerationDecision.objects.filter(action="queue").count(),
    }


def ai_spend_card() -> dict:
    """Today + month-to-date Gemini spend across all tools."""
    try:
        from apps.tools.models import ToolUsage, UsageStatus
    except ImportError:
        return {"today": 0, "mtd": 0, "by_tool": []}
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    today = ToolUsage.objects.filter(created_at__gte=today_start, status=UsageStatus.SUCCESS) \
        .aggregate(s=Sum("cost_usd"))["s"] or Decimal("0")
    mtd = ToolUsage.objects.filter(created_at__gte=month_start, status=UsageStatus.SUCCESS) \
        .aggregate(s=Sum("cost_usd"))["s"] or Decimal("0")
    by_tool = (ToolUsage.objects.filter(created_at__gte=month_start, status=UsageStatus.SUCCESS)
               .values("tool__slug")
               .annotate(spend=Sum("cost_usd"), runs=Count("id"))
               .order_by("-spend")[:10])
    return {"today": float(today), "mtd": float(mtd), "by_tool": list(by_tool)}


def licenses_card() -> dict:
    from apps.accounts.models import RealtorProfile
    soon_30 = (timezone.now() + timedelta(days=30)).date()
    return {
        "verified":          RealtorProfile.objects.filter(verification_status="verified").count(),
        "pending":           RealtorProfile.objects.filter(verification_status="pending").count(),
        "expiring_soon":     RealtorProfile.objects.filter(license_expires__lte=soon_30).count(),
        "suspended":         RealtorProfile.objects.filter(verification_status__in=["suspended", "revoked"]).count(),
    }


def vendors_card() -> dict:
    """Vendors active but with no leads in 30 days — churn signal."""
    try:
        from apps.accounts.models import VendorProfile
        from apps.marketplace.models import Lead
    except ImportError:
        return {"active": 0, "no_recent_leads": 0}
    thirty = _since(24 * 30)
    active = VendorProfile.objects.filter(status="active").count()
    recent_lead_vendor_ids = Lead.objects.filter(created_at__gte=thirty).values_list("vendor_id", flat=True).distinct()
    no_recent = VendorProfile.objects.filter(status="active").exclude(pk__in=recent_lead_vendor_ids).count()
    return {"active": active, "no_recent_leads": no_recent}


def suspicious_card() -> dict:
    """Cheap heuristics: same-IP signups, rapid posting velocity, etc."""
    from apps.audit.models import AccessLog
    last_hour = _since(1)
    by_ip = (AccessLog.objects
             .filter(created_at__gte=last_hour)
             .values("ip")
             .annotate(c=Count("id"))
             .filter(c__gt=50)
             .order_by("-c")[:5])
    return {
        "high_volume_ips": list(by_ip),
        "windowed_minutes": 60,
    }


def all_cards() -> dict:
    return {
        "signups":     signups_card(),
        "moderation":  moderation_card(),
        "ai_spend":    ai_spend_card(),
        "licenses":    licenses_card(),
        "vendors":     vendors_card(),
        "suspicious":  suspicious_card(),
    }
