"""Moderation serializers.

Safety contract: Layer 2 free-text rationale (`reason`) is NEVER exposed in
API responses to mods — only allowed/categories/severity are visible.
The full classifier output is visible only to operators+ via audit endpoints.
"""
from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.accounts.api.serializers import PublicUserSerializer, PrivateUserSerializer

from ..models import (
    ActionTemplate,
    Flag,
    FlagReason,
    FlagStatus,
    ModerationAction,
    ModerationDecision,
)

# ─── Allowed target_type choices (UGC pipes only) ───────────────────────
TARGET_TYPE_CHOICES = (
    "post", "comment",
    "forum_thread", "forum_reply",
    "service", "lead_message", "review",
    "vendor_tagline",
)

# Map slug → (app_label, model_name).
TARGET_TYPE_MAP = {
    "post":           ("content",     "post"),
    "comment":        ("content",     "comment"),
    "forum_thread":   ("forum",       "forumthread"),
    "forum_reply":    ("forum",       "forumreply"),
    "service":        ("marketplace", "service"),
    "lead_message":   ("marketplace", "leadmessage"),
    "review":         ("marketplace", "review"),
    "vendor_tagline": ("accounts",    "vendorprofile"),
}


def _target_type_slug(ct: ContentType | None) -> str:
    if ct is None:
        return ""
    for slug, (app, model) in TARGET_TYPE_MAP.items():
        if ct.app_label == app and ct.model == model:
            return slug
    return f"{ct.app_label}.{ct.model}"


def _target_excerpt(target: Any, limit: int = 200) -> str:
    if target is None:
        return ""
    for field in ("body", "body_markdown", "title", "tagline", "summary", "name"):
        value = getattr(target, field, None)
        if value:
            text = str(value)
            return text[:limit] + ("…" if len(text) > limit else "")
    return ""


def _target_full_url(target: Any) -> str:
    if target is None:
        return ""
    if hasattr(target, "get_absolute_url"):
        try:
            return target.get_absolute_url()
        except Exception:  # noqa: BLE001
            return ""
    return ""


def _redact_classifier_output(output: dict, *, full: bool) -> dict:
    """Mods see allowed/categories/severity only. Op+ see full payload."""
    if not isinstance(output, dict):
        return {}
    if full:
        return output
    return {
        "allowed":    output.get("allowed"),
        "categories": output.get("categories", []),
        "severity":   output.get("severity"),
    }


# ─── Decisions ────────────────────────────────────────────────────────────
class ModerationDecisionSerializer(serializers.ModelSerializer):
    target_type = serializers.SerializerMethodField()
    target_excerpt = serializers.SerializerMethodField()
    classifier_output = serializers.SerializerMethodField()
    moderator = PublicUserSerializer(source="actor", read_only=True)
    moderated_at = serializers.DateTimeField(source="created_at", read_only=True)
    action_template = serializers.SerializerMethodField()

    class Meta:
        model = ModerationDecision
        fields = (
            "id", "target_type", "target_id", "target_excerpt",
            "action", "reason", "severity",
            "classifier_output", "moderator", "moderated_at",
            "action_template",
        )
        read_only_fields = fields

    def get_target_type(self, obj: ModerationDecision) -> str:
        return _target_type_slug(obj.target_type)

    def get_target_excerpt(self, obj: ModerationDecision) -> str:
        return _target_excerpt(obj.target)

    def get_classifier_output(self, obj: ModerationDecision) -> dict:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        is_op = bool(
            user and user.is_authenticated
            and (user.is_superuser or user.groups.filter(name="operator").exists())
        )
        return _redact_classifier_output(obj.output, full=is_op)

    def get_action_template(self, obj: ModerationDecision) -> str | None:
        if not isinstance(obj.output, dict):
            return None
        return obj.output.get("template_slug")


# ─── Queue items ──────────────────────────────────────────────────────────
class QueueItemSerializer(serializers.ModelSerializer):
    """Items pending human review. Free-text classifier rationale is REDACTED."""

    target_type = serializers.SerializerMethodField()
    target_excerpt = serializers.SerializerMethodField()
    target_full_url = serializers.SerializerMethodField()
    reason_flag = serializers.SerializerMethodField()
    classifier_output = serializers.SerializerMethodField()

    class Meta:
        model = ModerationDecision
        fields = (
            "id", "target_type", "target_id",
            "target_excerpt", "target_full_url",
            "reason_flag", "classifier_output", "severity", "created_at",
        )
        read_only_fields = fields

    def get_target_type(self, obj: ModerationDecision) -> str:
        return _target_type_slug(obj.target_type)

    def get_target_excerpt(self, obj: ModerationDecision) -> str:
        return _target_excerpt(obj.target)

    def get_target_full_url(self, obj: ModerationDecision) -> str:
        return _target_full_url(obj.target)

    def get_reason_flag(self, obj: ModerationDecision) -> str | None:
        if obj.target_type is None or obj.target_id is None:
            return None
        flag = (Flag.objects
                .filter(target_type=obj.target_type, target_id=obj.target_id, status=FlagStatus.OPEN)
                .order_by("-created_at").first())
        return flag.reason if flag else None

    def get_classifier_output(self, obj: ModerationDecision) -> dict:
        # Mods never see free-text rationale here. Always redact.
        return _redact_classifier_output(obj.output, full=False)


# ─── Flags ────────────────────────────────────────────────────────────────
class FlagSerializer(serializers.ModelSerializer):
    reporter = PublicUserSerializer(read_only=True)
    target_type = serializers.SerializerMethodField()
    reason_category = serializers.CharField(source="reason", read_only=True)
    reason_text = serializers.CharField(source="notes", read_only=True)

    class Meta:
        model = Flag
        fields = (
            "id", "reporter", "target_type", "target_id",
            "reason_category", "reason_text", "status", "created_at",
        )
        read_only_fields = fields

    def get_target_type(self, obj: Flag) -> str:
        return _target_type_slug(obj.target_type)


class FlagCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=TARGET_TYPE_CHOICES)
    target_id = serializers.IntegerField(min_value=1)
    reason_category = serializers.ChoiceField(choices=FlagReason.choices)
    reason_text = serializers.CharField(max_length=500, allow_blank=True, required=False, default="")

    def validate(self, attrs: dict) -> dict:
        slug = attrs["target_type"]
        app, model = TARGET_TYPE_MAP[slug]
        try:
            ct = ContentType.objects.get(app_label=app, model=model)
        except ContentType.DoesNotExist as e:
            raise serializers.ValidationError({"target_type": "Unknown target."}) from e
        target_cls = ct.model_class()
        if target_cls is None or not target_cls.objects.filter(pk=attrs["target_id"]).exists():
            raise serializers.ValidationError({"target_id": "Target not found."})
        attrs["_content_type"] = ct
        return attrs

    def create(self, validated: dict) -> Flag:
        ct = validated.pop("_content_type")
        request = self.context["request"]
        return Flag.objects.create(
            target_type=ct,
            target_id=validated["target_id"],
            reporter=request.user,
            reason=validated["reason_category"],
            notes=validated.get("reason_text", "")[:1000],
            status=FlagStatus.OPEN,
        )


# ─── Action templates ─────────────────────────────────────────────────────
class ActionTemplateSerializer(serializers.ModelSerializer):
    """Backed by ActionTemplate model (Sprint 5). Read-only over the wire."""

    class Meta:
        model = ActionTemplate
        fields = ("slug", "label", "action", "default_reason",
                  "notify_template_id", "is_active", "sort_order")
        read_only_fields = fields


# ─── Decision input ───────────────────────────────────────────────────────
DECISION_ACTION_CHOICES = (
    ("approve", "approve"),
    ("remove",  "remove"),
    ("escalate", "escalate"),
)


class DecisionCreateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=DECISION_ACTION_CHOICES)
    reason = serializers.CharField(max_length=300, allow_blank=True, required=False, default="")
    action_template = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")


# ─── Escalation ──────────────────────────────────────────────────────────
class EscalateSerializer(serializers.Serializer):
    notes = serializers.CharField(max_length=2000)


# ─── Investigate user ────────────────────────────────────────────────────
class _MiniContentSerializer(serializers.Serializer):
    """Stub for nested mini-cards. Phase-2/4/5 swap in real serializers."""

    id = serializers.IntegerField()
    kind = serializers.CharField(required=False)
    excerpt = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(required=False)
    moderation_status = serializers.CharField(required=False)


class InvestigateUserResultSerializer(serializers.Serializer):
    user = PrivateUserSerializer()
    recent_posts = _MiniContentSerializer(many=True)
    recent_comments = _MiniContentSerializer(many=True)
    recent_threads = _MiniContentSerializer(many=True)
    recent_replies = _MiniContentSerializer(many=True)
    recent_flags_against = FlagSerializer(many=True)
    recent_decisions = ModerationDecisionSerializer(many=True)
    total_warnings = serializers.IntegerField()
    last_seen = serializers.DateTimeField(allow_null=True)
    account_age_days = serializers.IntegerField()
    pattern_signals = serializers.ListField(
        child=serializers.CharField(), required=False, default=list,
    )
    post_count_24h = serializers.IntegerField(required=False, default=0)
    recent_decision_count_30d = serializers.IntegerField(required=False, default=0)


# ─── Moderator stats ─────────────────────────────────────────────────────
class _StatsTimePoint(serializers.Serializer):
    day = serializers.CharField()
    count = serializers.IntegerField()


class ModeratorStatsSerializer(serializers.Serializer):
    items_reviewed_30d = serializers.IntegerField()
    items_reviewed_7d = serializers.IntegerField()
    agreement_rate = serializers.FloatField()
    reversal_rate = serializers.FloatField()
    avg_response_minutes = serializers.FloatField()
    current_streak = serializers.IntegerField()
    queue_position = serializers.IntegerField()
    timeseries_30d = _StatsTimePoint(many=True, required=False, default=list)


# ─── Escalation list ─────────────────────────────────────────────────────
class EscalationListItemSerializer(serializers.ModelSerializer):
    """Operator-tier escalation row. Free-text rationale never exposed to mods."""

    target_type = serializers.SerializerMethodField()
    target_excerpt = serializers.SerializerMethodField()
    escalated_by = PublicUserSerializer(source="actor", read_only=True)
    notes = serializers.SerializerMethodField()

    class Meta:
        model = ModerationDecision
        fields = (
            "id", "target_type", "target_id", "target_excerpt",
            "severity", "notes", "escalated_by", "created_at",
        )
        read_only_fields = fields

    def get_target_type(self, obj: ModerationDecision) -> str:
        return _target_type_slug(obj.target_type)

    def get_target_excerpt(self, obj: ModerationDecision) -> str:
        return _target_excerpt(obj.target)

    def get_notes(self, obj: ModerationDecision) -> str:
        if not isinstance(obj.output, dict):
            return ""
        return str(obj.output.get("notes", ""))[:1000]
