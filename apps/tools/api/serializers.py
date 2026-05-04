"""Tools serializers — meta + run requests + task status + usage rows."""
from __future__ import annotations

from rest_framework import serializers

from ..models import ToolUsage


# ──────────────────────────────────────────────────────────────────────────
# Public meta
# ──────────────────────────────────────────────────────────────────────────
class ToolMetaSerializer(serializers.Serializer):
    """Static-ish landing-page metadata. Shaped for the marketing pages."""

    tool_id = serializers.SlugField()
    name = serializers.CharField()
    description = serializers.CharField()
    category = serializers.CharField()
    requires_auth = serializers.BooleanField(default=True)
    avg_runtime_seconds = serializers.IntegerField(min_value=0)
    rate_limit_per_hour = serializers.IntegerField(min_value=0)


# ──────────────────────────────────────────────────────────────────────────
# Description writer
# ──────────────────────────────────────────────────────────────────────────
TONE_CHOICES = (
    ("professional", "Professional"),
    ("friendly", "Friendly"),
    ("luxury", "Luxury"),
)


class DescriptionWriterRequestSerializer(serializers.Serializer):
    property_type = serializers.CharField(min_length=2, max_length=64)
    beds = serializers.IntegerField(min_value=0, max_value=20)
    baths = serializers.DecimalField(max_digits=4, decimal_places=1,
                                     min_value=0, max_value=20)
    sqft = serializers.IntegerField(min_value=1, max_value=100_000)
    key_features = serializers.CharField(max_length=1000, allow_blank=True)
    tone = serializers.ChoiceField(choices=TONE_CHOICES, default="professional")


class DescriptionWriterResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=(
        ("queued", "queued"), ("running", "running"),
        ("done", "done"), ("failed", "failed"),
    ))


# ──────────────────────────────────────────────────────────────────────────
# Furniture remover
# ──────────────────────────────────────────────────────────────────────────
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg"}


class FurnitureRemoverRequestSerializer(serializers.Serializer):
    image = serializers.ImageField(use_url=False)
    preserve_layout = serializers.BooleanField(default=True)

    def validate_image(self, image):
        if image.size > MAX_IMAGE_BYTES:
            raise serializers.ValidationError("Image must be 10 MB or smaller.")
        content_type = (getattr(image, "content_type", "") or "").lower()
        if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise serializers.ValidationError("Only JPG and PNG are allowed.")
        return image


class FurnitureRemoverResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=(
        ("queued", "queued"), ("running", "running"),
        ("done", "done"), ("failed", "failed"),
    ))
    original_url = serializers.URLField(allow_null=True, required=False)
    result_url = serializers.URLField(allow_null=True, required=False)


# ──────────────────────────────────────────────────────────────────────────
# Task status (polling)
# ──────────────────────────────────────────────────────────────────────────
class ToolTaskStatusSerializer(serializers.ModelSerializer):
    """Polled by the frontend. Does not echo input_meta to avoid PII leakage."""

    task_id = serializers.IntegerField(source="pk", read_only=True)
    progress = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    completed_at = serializers.SerializerMethodField()

    class Meta:
        model = ToolUsage
        fields = (
            "task_id", "status", "progress", "result", "error",
            "created_at", "completed_at",
        )
        read_only_fields = fields

    def get_progress(self, obj: ToolUsage) -> int:
        # Coarse progress mapping — Celery has no native % progress.
        return {
            "queued": 0,
            "running": 50,
            "success": 100,
            "failed": 100,
            "blocked": 100,
        }.get(obj.status, 0)

    def get_result(self, obj: ToolUsage):
        if obj.status != "success":
            return None
        meta = obj.output_meta or {}
        in_meta = obj.input_meta or {}
        # Keep the public-facing payload narrow; bare-bones for now.
        return {
            "text": meta.get("text"),
            "url": meta.get("url"),
            "input_url": meta.get("input_url") or in_meta.get("image_url"),
            "cost_usd": float(obj.cost_usd or 0),
            "runtime_ms": obj.duration_ms or 0,
        }

    def get_completed_at(self, obj: ToolUsage):
        return obj.updated_at if obj.status in {"success", "failed", "blocked"} else None


# ──────────────────────────────────────────────────────────────────────────
# /me/tool-usage/
# ──────────────────────────────────────────────────────────────────────────
class ToolUsageSerializer(serializers.ModelSerializer):
    """Lean ledger row for the /me/ tool-usage list."""

    tool_id = serializers.SlugField(source="tool.slug", read_only=True)
    input_meta = serializers.SerializerMethodField()
    token_cost_usd = serializers.DecimalField(
        source="cost_usd", max_digits=8, decimal_places=4, read_only=True,
    )

    class Meta:
        model = ToolUsage
        fields = (
            "id", "tool_id", "status", "input_meta",
            "token_cost_usd", "created_at",
        )
        read_only_fields = fields

    # Limit echoed input_meta to non-sensitive keys.
    SAFE_INPUT_KEYS = (
        "property_type", "beds", "baths", "sqft", "tone",
        "preserve_layout", "model",
    )

    def get_input_meta(self, obj: ToolUsage) -> dict:
        meta = obj.input_meta or {}
        return {k: meta[k] for k in self.SAFE_INPUT_KEYS if k in meta}
