"""Audit serializers.

Privacy / safety:
- before/after JSON is op-only here, but we limit it to a redacted subset.
- Full before/after only visible via ActionLogDetailView (admin-only).
- Query params from AccessLog are sanitized to strip auth tokens.
"""
from __future__ import annotations

from urllib.parse import urlencode, urlparse, parse_qsl

from rest_framework import serializers

from apps.accounts.api.serializers import PublicUserSerializer

from ..models import AccessLog, ActionLog

# Keys we never expose at the op tier (admin sees them via the detail view).
_REDACTED_KEYS = {
    "password", "password_hash", "secret", "token", "refresh_token",
    "api_key", "totp_seed", "raw_response",
}

# Query params we strip from access logs to avoid leaking auth material.
_STRIP_QUERY_KEYS = {"token", "code", "key", "secret", "auth", "access_token", "refresh_token"}


def _truncate(s: str | None, limit: int) -> str:
    if not s:
        return ""
    return s[:limit]


def _redact(payload):  # noqa: ANN001
    if not isinstance(payload, dict):
        return payload
    return {
        k: ("[REDACTED]" if k.lower() in _REDACTED_KEYS else v)
        for k, v in payload.items()
    }


def _sanitize_query(query: str) -> str:
    if not query:
        return ""
    pairs = [
        (k, "[REDACTED]" if k.lower() in _STRIP_QUERY_KEYS else v)
        for k, v in parse_qsl(query, keep_blank_values=True)
    ]
    return urlencode(pairs, doseq=True)


# ─── ActionLog ────────────────────────────────────────────────────────────
class ActionLogSerializer(serializers.ModelSerializer):
    actor = PublicUserSerializer(read_only=True)
    target_type = serializers.SerializerMethodField()
    user_agent = serializers.SerializerMethodField()
    before_state = serializers.SerializerMethodField()
    after_state = serializers.SerializerMethodField()

    class Meta:
        model = ActionLog
        fields = (
            "id", "actor", "target_type", "target_id",
            "action", "before_state", "after_state",
            "ip", "user_agent", "reason", "created_at",
        )
        read_only_fields = fields

    def get_target_type(self, obj: ActionLog) -> str:
        if obj.target_type is None:
            return ""
        return f"{obj.target_type.app_label}.{obj.target_type.model}"

    def get_user_agent(self, obj: ActionLog) -> str:
        return _truncate(obj.user_agent, 200)

    def get_before_state(self, obj: ActionLog):
        return _redact(obj.before)

    def get_after_state(self, obj: ActionLog):
        return _redact(obj.after)


class ActionLogDetailSerializer(serializers.ModelSerializer):
    """Admin-only — returns full before/after JSON without redaction."""

    actor = PublicUserSerializer(read_only=True)
    target_type = serializers.SerializerMethodField()
    before_state = serializers.JSONField(source="before")
    after_state = serializers.JSONField(source="after")
    user_agent = serializers.SerializerMethodField()

    class Meta:
        model = ActionLog
        fields = (
            "id", "actor", "target_type", "target_id",
            "action", "before_state", "after_state", "diff",
            "ip", "user_agent", "reason", "created_at",
        )
        read_only_fields = fields

    def get_target_type(self, obj: ActionLog) -> str:
        if obj.target_type is None:
            return ""
        return f"{obj.target_type.app_label}.{obj.target_type.model}"

    def get_user_agent(self, obj: ActionLog) -> str:
        return obj.user_agent or ""


# ─── AccessLog ────────────────────────────────────────────────────────────
class AccessLogSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(source="actor", read_only=True)
    query_params = serializers.SerializerMethodField()
    user_agent = serializers.SerializerMethodField()
    referer = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()

    class Meta:
        model = AccessLog
        fields = (
            "id", "user", "method", "path", "query_params",
            "status_code", "ip", "user_agent", "referer", "created_at",
        )
        read_only_fields = fields

    def get_path(self, obj: AccessLog) -> str:
        return urlparse(obj.path).path or obj.path

    def get_query_params(self, obj: AccessLog) -> str:
        return _sanitize_query(urlparse(obj.path).query)

    def get_user_agent(self, obj: AccessLog) -> str:
        return _truncate(obj.user_agent, 200)

    def get_referer(self, obj: AccessLog) -> str:
        # AccessLog model doesn't store referer; surface empty string for shape.
        return ""
