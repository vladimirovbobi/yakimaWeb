"""Operations serializers."""
from __future__ import annotations

from rest_framework import serializers

from apps.accounts.models import VendorProfile, VerificationStatus

# ─── Top-level dashboard payload ─────────────────────────────────────────
class OpsDashboardSerializer(serializers.Serializer):
    """High-level metrics for /ops/dashboard/. Cheap, cache-friendly."""

    signups_24h = serializers.IntegerField()
    signups_7d = serializers.IntegerField()
    mau = serializers.IntegerField()

    mod_queue_depth = serializers.IntegerField()
    mod_queue_oldest_age_minutes = serializers.IntegerField()

    ai_spend_today_usd = serializers.FloatField()
    ai_spend_month_usd = serializers.FloatField()
    ai_spend_cap_pct = serializers.FloatField()

    licenses_expiring_30d = serializers.IntegerField()
    vendors_pending_approval = serializers.IntegerField()
    suspicious_signal_count = serializers.IntegerField()

    generated_at = serializers.DateTimeField()


# ─── Single-card payload for /ops/metrics/<slug>/ ────────────────────────
class MetricCardSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = serializers.FloatField()
    delta_pct = serializers.FloatField(allow_null=True)
    trend = serializers.ListField(child=serializers.FloatField())
    threshold_state = serializers.ChoiceField(choices=("ok", "warn", "breach"))


class OpsDashboardCardSerializer(serializers.Serializer):
    """Wraps MetricCardSerializer for the cards-array variant."""

    cards = MetricCardSerializer(many=True)


# ─── Mutating ops payloads ───────────────────────────────────────────────
class UserSuspendSerializer(serializers.Serializer):
    duration_days = serializers.IntegerField(min_value=1, max_value=365)
    reason = serializers.CharField(max_length=500)
    notify_user = serializers.BooleanField(default=True)


class VendorStatusUpdateSerializer(serializers.ModelSerializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

    class Meta:
        model = VendorProfile
        fields = ("status", "reason")


_LICENSE_STATUS_CHOICES = VerificationStatus.choices


class LicenseOverrideSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=_LICENSE_STATUS_CHOICES)
    reason = serializers.CharField(max_length=500)
    expires_override = serializers.DateField(required=False, allow_null=True)


# ─── Content takedown ────────────────────────────────────────────────────
TAKEDOWN_TARGET_CHOICES = (
    "post", "comment",
    "forum_thread", "forum_reply",
    "service", "lead_message", "review",
    "vendor_tagline",
)


class ContentTakedownSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=TAKEDOWN_TARGET_CHOICES)
    target_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)
