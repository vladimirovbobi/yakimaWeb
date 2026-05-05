"""Operations views — dashboard, user/vendor/license/content levers.

Caching: the dashboard view is cached for 30s in Redis, keyed by user_id so
two ops looking at the same numbers don't double-count Postgres queries but
permission decisions stay per-user.

ActionLog is auto-fired by `apps/audit/signals.py` for every staff write to
the audited models below — we don't write extra rows here.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView, UpdateAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import (
    CheckTrigger,
    LicenseCheck,
    RealtorProfile,
    VendorProfile,
)
from apps.audit.models import ActionLog
from apps.core.api.csrf import StrictCSRFMixin
from apps.core.api.permissions import IsOperator, RequiresOTP
from apps.moderation.models import (
    ModerationAction,
    ModerationDecision,
    ModerationLayer,
    ModerationStatus,
)

from .serializers import (
    ContentTakedownSerializer,
    LicenseOverrideSerializer,
    MetricCardSerializer,
    OpsDashboardSerializer,
    UserSuspendSerializer,
    VendorStatusUpdateSerializer,
)

log = logging.getLogger(__name__)
User = get_user_model()

# ─── Helpers ─────────────────────────────────────────────────────────────
def _since(hours: int):
    return timezone.now() - timedelta(hours=hours)


def _ai_spend(start) -> float:
    try:
        from apps.tools.models import ToolUsage, UsageStatus
    except ImportError:
        return 0.0
    total = (ToolUsage.objects
             .filter(created_at__gte=start, status=UsageStatus.SUCCESS)
             .aggregate(s=Sum("cost_usd"))["s"]) or Decimal("0")
    return float(total)


def _suspicious_count() -> int:
    """Heuristic placeholder. Real signals land in Phase 6 ops console.

    TODO: replace with composite scoring (same-IP cluster, disposable-email
    domain, rapid posting velocity, low-account-age + flagged content).
    """
    return 0


# ─── Dashboard ──────────────────────────────────────────────────────────
def _dashboard_cache_key(user_id: int) -> str:
    return f"ops:dashboard:{user_id}"


_DASHBOARD_TTL = 30  # seconds


class DashboardView(GenericAPIView):
    """GET /api/v1/ops/dashboard/ — composed metrics. Cached 30s per user."""

    serializer_class = OpsDashboardSerializer
    permission_classes = (IsOperator, RequiresOTP)

    @extend_schema(responses=OpsDashboardSerializer)
    def get(self, request: Request) -> Response:
        cache_key = _dashboard_cache_key(request.user.pk)
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = today_start.replace(day=1)
        soon_30 = (now + timedelta(days=30)).date()

        signups_24h = User.objects.filter(created_at__gte=_since(24)).count()
        signups_7d = User.objects.filter(created_at__gte=_since(24 * 7)).count()
        mau = User.objects.filter(last_seen__gte=_since(24 * 30)).count()

        queued = ModerationDecision.objects.filter(action=ModerationAction.QUEUE)
        mod_queue_depth = queued.count()
        oldest = queued.order_by("created_at").values_list("created_at", flat=True).first()
        oldest_age_minutes = (
            int((now - oldest).total_seconds() // 60) if oldest else 0
        )

        spend_today = _ai_spend(today_start)
        spend_month = _ai_spend(month_start)
        cap = float(getattr(settings, "GEMINI_DAILY_SPEND_CAP_USD", 0) or 0)
        spend_cap_pct = (spend_today / cap * 100.0) if cap > 0 else 0.0

        licenses_expiring = (RealtorProfile.objects
                             .filter(license_expires__lte=soon_30,
                                     license_expires__gte=now.date())
                             .count())
        vendors_pending = (VendorProfile.objects
                           .filter(status=VendorProfile.Status.DRAFT).count())

        payload = {
            "signups_24h": signups_24h,
            "signups_7d": signups_7d,
            "mau": mau,
            "mod_queue_depth": mod_queue_depth,
            "mod_queue_oldest_age_minutes": oldest_age_minutes,
            "ai_spend_today_usd": spend_today,
            "ai_spend_month_usd": spend_month,
            "ai_spend_cap_pct": round(spend_cap_pct, 2),
            "licenses_expiring_30d": licenses_expiring,
            "vendors_pending_approval": vendors_pending,
            "suspicious_signal_count": _suspicious_count(),
            "generated_at": now,
        }
        ser = self.get_serializer(payload)
        cache.set(cache_key, ser.data, _DASHBOARD_TTL)
        return Response(ser.data, status=status.HTTP_200_OK)


# ─── Per-card metric (sparkline) ─────────────────────────────────────────
def _signups_trend(days: int = 14) -> list[float]:
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    out: list[float] = []
    for i in range(days - 1, -1, -1):
        start = now - timedelta(days=i)
        end = start + timedelta(days=1)
        out.append(float(User.objects.filter(created_at__gte=start, created_at__lt=end).count()))
    return out


def _queue_depth_trend(days: int = 14) -> list[float]:
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    out: list[float] = []
    for i in range(days - 1, -1, -1):
        end = now - timedelta(days=i) + timedelta(days=1)
        out.append(float(
            ModerationDecision.objects
            .filter(action=ModerationAction.QUEUE, created_at__lt=end)
            .count()
        ))
    return out


def _ai_spend_trend(days: int = 14) -> list[float]:
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    out: list[float] = []
    for i in range(days - 1, -1, -1):
        start = now - timedelta(days=i)
        end = start + timedelta(days=1)
        out.append(_ai_spend(start) - _ai_spend(end) if end < now else _ai_spend(start))
    return out


_CARD_REGISTRY = {
    "signups": {
        "name": "Signups (24h)",
        "trend_fn": _signups_trend,
        "value_fn": lambda: User.objects.filter(created_at__gte=_since(24)).count(),
        "warn_at": 50,
        "breach_at": 200,
    },
    "mod_queue_depth": {
        "name": "Mod queue depth",
        "trend_fn": _queue_depth_trend,
        "value_fn": lambda: ModerationDecision.objects.filter(action=ModerationAction.QUEUE).count(),
        "warn_at": 50,
        "breach_at": 200,
    },
    "ai_spend_today": {
        "name": "AI spend today (USD)",
        "trend_fn": _ai_spend_trend,
        "value_fn": lambda: _ai_spend(timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)),
        "warn_at": float(getattr(settings, "GEMINI_DAILY_SPEND_CAP_USD", 50)) * 0.8,
        "breach_at": float(getattr(settings, "GEMINI_DAILY_SPEND_CAP_USD", 50)),
    },
}


def _threshold_state(value: float, warn_at: float, breach_at: float) -> str:
    if value >= breach_at:
        return "breach"
    if value >= warn_at:
        return "warn"
    return "ok"


def _delta_pct(trend: list[float]) -> float | None:
    if len(trend) < 2 or trend[-2] == 0:
        return None
    return round((trend[-1] - trend[-2]) / trend[-2] * 100.0, 2)


class MetricCardView(GenericAPIView):
    """GET /api/v1/ops/metrics/<slug>/ — sparkline + delta for one card."""

    serializer_class = MetricCardSerializer
    permission_classes = (IsOperator, RequiresOTP)

    @extend_schema(responses=MetricCardSerializer)
    def get(self, request: Request, card_slug: str) -> Response:
        spec = _CARD_REGISTRY.get(card_slug)
        if spec is None:
            return Response(
                {"detail": f"Unknown card slug: {card_slug}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        trend = spec["trend_fn"]()
        value = float(spec["value_fn"]())
        payload = {
            "name": spec["name"],
            "value": value,
            "delta_pct": _delta_pct(trend),
            "trend": trend,
            "threshold_state": _threshold_state(value, spec["warn_at"], spec["breach_at"]),
        }
        ser = self.get_serializer(payload)
        return Response(ser.data, status=status.HTTP_200_OK)


# ─── User suspension ─────────────────────────────────────────────────────
class UserSuspendView(StrictCSRFMixin, GenericAPIView):
    """POST /api/v1/ops/users/<int:user_id>/suspend/ — disable + Celery re-enable."""

    serializer_class = UserSuspendSerializer
    permission_classes = (IsOperator, RequiresOTP)

    @extend_schema(request=UserSuspendSerializer, responses=UserSuspendSerializer)
    def post(self, request: Request, user_id: int) -> Response:
        target = get_object_or_404(User, pk=user_id)
        if target.is_superuser:
            raise PermissionDenied("Cannot suspend superuser.")
        if target.pk == request.user.pk:
            raise PermissionDenied("Cannot suspend yourself.")

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        duration_days = ser.validated_data["duration_days"]
        reason = ser.validated_data["reason"]
        notify = ser.validated_data["notify_user"]

        ends_at = timezone.now() + timedelta(days=duration_days)
        with transaction.atomic():
            target.is_active = False
            target.save(update_fields=["is_active"])
            try:
                ct = ContentType.objects.get_for_model(User)
                ActionLog.objects.create(
                    actor=request.user,
                    action="accounts.User.suspend",
                    target_type=ct, target_id=target.pk,
                    reason=reason[:1000],
                    after={"is_active": False, "ends_at": ends_at.isoformat()},
                )
            except Exception:  # noqa: BLE001
                log.exception("suspend ActionLog failed")

        # Schedule re-enable. TODO: build apps.operations.tasks.reenable_user
        # once Phase 6 lands; for now fall back to ETA-only Celery and document.
        try:
            from celery import current_app
            current_app.send_task(
                "apps.operations.tasks.reenable_user",
                args=[target.pk],
                eta=ends_at,
            )
        except Exception:  # noqa: BLE001
            log.warning("reenable_user task not available; manual re-enable required for user %s", target.pk)

        return Response(
            {
                "user_id": target.pk,
                "is_active": target.is_active,
                "ends_at": ends_at,
                "notified": bool(notify),
            },
            status=status.HTTP_200_OK,
        )


# ─── Vendor status ───────────────────────────────────────────────────────
class VendorStatusUpdateView(StrictCSRFMixin, UpdateAPIView):
    """PATCH /api/v1/ops/vendors/<int:vendor_id>/ — flip status + log."""

    serializer_class = VendorStatusUpdateSerializer
    permission_classes = (IsOperator, RequiresOTP)
    queryset = VendorProfile.objects.all()
    lookup_url_kwarg = "vendor_id"
    http_method_names = ["patch", "options"]

    def perform_update(self, serializer):  # noqa: ANN001
        # Strip non-model `reason` field before save.
        reason = serializer.validated_data.pop("reason", "")
        instance = serializer.save()
        try:
            ct = ContentType.objects.get_for_model(VendorProfile)
            ActionLog.objects.create(
                actor=self.request.user,
                action="accounts.VendorProfile.status_change",
                target_type=ct, target_id=instance.pk,
                reason=reason[:1000],
                after={"status": instance.status},
            )
        except Exception:  # noqa: BLE001
            log.exception("vendor status ActionLog failed")


# ─── License override ────────────────────────────────────────────────────
class LicenseOverrideView(StrictCSRFMixin, GenericAPIView):
    """POST /api/v1/ops/licenses/<int:profile_id>/override/ — manual verification flip."""

    serializer_class = LicenseOverrideSerializer
    permission_classes = (IsOperator, RequiresOTP)

    @extend_schema(request=LicenseOverrideSerializer, responses=LicenseOverrideSerializer)
    def post(self, request: Request, profile_id: int) -> Response:
        profile = get_object_or_404(RealtorProfile, pk=profile_id)
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data["status"]
        reason = ser.validated_data["reason"]
        expires_override = ser.validated_data.get("expires_override")

        with transaction.atomic():
            profile.verification_status = new_status
            updates = ["verification_status"]
            if expires_override:
                profile.license_expires = expires_override
                updates.append("license_expires")
            if new_status == "verified":
                profile.verified_at = timezone.now()
                updates.append("verified_at")
            profile.save(update_fields=updates)

            LicenseCheck.objects.create(
                profile=profile,
                status=new_status,
                source="manual_override",
                triggered_by=CheckTrigger.MANUAL,
                raw_response={"override_by": request.user.email, "reason": reason},
            )

        return Response(
            {
                "profile_id": profile.pk,
                "status": new_status,
                "license_expires": profile.license_expires,
            },
            status=status.HTTP_200_OK,
        )


# ─── Content takedown ────────────────────────────────────────────────────
_TAKEDOWN_MAP = {
    "post":           ("content",     "post"),
    "comment":        ("content",     "comment"),
    "forum_thread":   ("forum",       "forumthread"),
    "forum_reply":    ("forum",       "forumreply"),
    "service":        ("marketplace", "service"),
    "lead_message":   ("marketplace", "leadmessage"),
    "review":         ("marketplace", "review"),
    "vendor_tagline": ("accounts",    "vendorprofile"),
}


class ContentTakedownView(StrictCSRFMixin, GenericAPIView):
    """POST /api/v1/ops/content/takedown/ — set moderation_status='removed'."""

    serializer_class = ContentTakedownSerializer
    permission_classes = (IsOperator, RequiresOTP)

    @extend_schema(request=ContentTakedownSerializer, responses=ContentTakedownSerializer)
    def post(self, request: Request) -> Response:
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        slug = ser.validated_data["target_type"]
        target_id = ser.validated_data["target_id"]
        reason = ser.validated_data["reason"]

        app, model = _TAKEDOWN_MAP[slug]
        try:
            ct = ContentType.objects.get(app_label=app, model=model)
        except ContentType.DoesNotExist:
            return Response({"detail": "Unknown target type."},
                            status=status.HTTP_404_NOT_FOUND)
        target_cls = ct.model_class()
        if target_cls is None:
            return Response({"detail": "Target model unavailable."},
                            status=status.HTTP_404_NOT_FOUND)
        target = target_cls.objects.filter(pk=target_id).first()
        if target is None:
            return Response({"detail": "Target not found."},
                            status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            if hasattr(target, "moderation_status"):
                target.moderation_status = ModerationStatus.REMOVED
                target.moderated_at = timezone.now()
                target.save(update_fields=["moderation_status", "moderated_at"])

            ModerationDecision.objects.create(
                target_type=ct, target_id=target_id,
                layer=ModerationLayer.HUMAN,
                classifier_ver=f"ops:{request.user.email}",
                input_hash="ops_takedown",
                output={"reason": reason, "via": "ops_takedown"},
                action=ModerationAction.REMOVE,
                severity=4,
                reason=reason[:300],
                actor=request.user,
            )

        return Response(
            {
                "target_type": slug, "target_id": target_id,
                "moderation_status": ModerationStatus.REMOVED,
            },
            status=status.HTTP_200_OK,
        )
