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
    baths = serializers.DecimalField(max_digits=4, decimal_places=1, min_value=0, max_value=20)
    sqft = serializers.IntegerField(min_value=1, max_value=100_000)
    key_features = serializers.CharField(max_length=1000, allow_blank=True)
    tone = serializers.ChoiceField(choices=TONE_CHOICES, default="professional")


class DescriptionWriterResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=(
            ("queued", "queued"),
            ("running", "running"),
            ("done", "done"),
            ("failed", "failed"),
        )
    )


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
    status = serializers.ChoiceField(
        choices=(
            ("queued", "queued"),
            ("running", "running"),
            ("done", "done"),
            ("failed", "failed"),
        )
    )
    original_url = serializers.URLField(allow_null=True, required=False)
    result_url = serializers.URLField(allow_null=True, required=False)


# ──────────────────────────────────────────────────────────────────────────
# Image compressor
# ──────────────────────────────────────────────────────────────────────────
MAX_COMPRESSOR_INPUT_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_COMPRESSOR_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
    "heic",
    "heif",
    "tiff",
    "tif",
    "bmp",
}


class ImageCompressorRequestSerializer(serializers.Serializer):
    """Single-file lossless image compression request.

    Multi-file batches are handled by the frontend looping over single-file
    submissions — keeps the API simple and the rate limiter accurate per-image.
    """

    image = serializers.FileField(use_url=False)

    def validate_image(self, image):
        if image.size > MAX_COMPRESSOR_INPUT_BYTES:
            raise serializers.ValidationError(
                "Image must be 50 MB or smaller.",
            )
        name = (image.name or "").lower()
        ext = name.rsplit(".", 1)[-1] if "." in name else ""
        if ext not in ALLOWED_COMPRESSOR_EXTENSIONS:
            raise serializers.ValidationError(
                f"Format '.{ext}' is not supported. Allowed: jpg, png, webp, gif, heic, tiff, bmp."
            )
        return image


class ImageCompressorResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=(
            ("queued", "queued"),
            ("running", "running"),
            ("done", "done"),
            ("failed", "failed"),
        )
    )


# ──────────────────────────────────────────────────────────────────────────
# Flyer generator (Sprint 2)
# ──────────────────────────────────────────────────────────────────────────
MAX_HEADLINE = 80
MAX_CALLOUT = 60
MAX_VALUE_PROP = 140
MAX_CALLOUTS = 3
MAX_VALUE_PROPS = 3
MAX_PHOTOS = 5
MIN_PHOTOS = 1


class FlyerPaletteSerializer(serializers.Serializer):
    """Read-only nested representation of a preset's palette (hex values)."""

    primary = serializers.CharField()
    secondary = serializers.CharField()
    accent = serializers.CharField()
    bg = serializers.CharField()
    fg = serializers.CharField()


class FlyerPresetSerializer(serializers.Serializer):
    """Public preset metadata for the gallery picker."""

    slug = serializers.SlugField()
    name = serializers.CharField()
    blurb = serializers.CharField()
    inspiration = serializers.CharField()
    palette = FlyerPaletteSerializer()
    fonts = serializers.DictField(child=serializers.CharField())
    layout_brief = serializers.CharField()
    preview_image = serializers.CharField(allow_blank=True)
    palette_token_names = serializers.DictField(
        child=serializers.CharField(),
        required=False,
    )


class FlyerRequestSerializer(serializers.Serializer):
    """Realtor's flyer-generation request.

    property_info + creative_text are validated to known shapes; the actual
    untrusted content (address, headline, etc.) is wrapped through the
    moderation pipeline before reaching the LLM.
    """

    preset_slug = serializers.SlugField(max_length=64)
    property_info = serializers.JSONField()
    creative_text = serializers.JSONField()
    photo_urls = serializers.ListField(
        child=serializers.URLField(max_length=500),
        min_length=MIN_PHOTOS,
        max_length=MAX_PHOTOS,
    )
    color_overrides = serializers.JSONField(required=False, default=dict)
    font_overrides = serializers.JSONField(required=False, default=dict)

    def validate_preset_slug(self, value):
        from apps.tools.services.flyer_presets import get_preset

        if get_preset(value) is None:
            raise serializers.ValidationError(f"Unknown flyer preset: {value!r}.")
        return value

    def validate_property_info(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("property_info must be an object.")
        addr = (value.get("address") or "").strip()
        if not addr:
            raise serializers.ValidationError("property_info.address is required.")
        if len(addr) > 200:
            raise serializers.ValidationError("address must be 200 chars or fewer.")
        try:
            price = float(value.get("price") or 0)
        except (TypeError, ValueError) as exc:
            raise serializers.ValidationError("property_info.price must be numeric.") from exc
        if price <= 0:
            raise serializers.ValidationError("property_info.price must be > 0.")
        return value

    def validate_creative_text(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("creative_text must be an object.")
        headline = (value.get("headline") or "").strip()
        if headline and len(headline) > MAX_HEADLINE:
            raise serializers.ValidationError(
                f"headline must be {MAX_HEADLINE} chars or fewer.",
            )
        callouts = value.get("callouts") or []
        if not isinstance(callouts, list):
            raise serializers.ValidationError("callouts must be a list.")
        if len(callouts) > MAX_CALLOUTS:
            raise serializers.ValidationError(f"max {MAX_CALLOUTS} callouts.")
        for c in callouts:
            if not isinstance(c, str):
                raise serializers.ValidationError("each callout must be a string.")
            if len(c) > MAX_CALLOUT:
                raise serializers.ValidationError(
                    f"callout must be {MAX_CALLOUT} chars or fewer.",
                )
        value_props = value.get("value_props") or []
        if not isinstance(value_props, list):
            raise serializers.ValidationError("value_props must be a list.")
        if len(value_props) > MAX_VALUE_PROPS:
            raise serializers.ValidationError(f"max {MAX_VALUE_PROPS} value_props.")
        for v in value_props:
            if not isinstance(v, str):
                raise serializers.ValidationError("each value_prop must be a string.")
            if len(v) > MAX_VALUE_PROP:
                raise serializers.ValidationError(
                    f"value_prop must be {MAX_VALUE_PROP} chars or fewer.",
                )
        return value


class FlyerResponseSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    status = serializers.ChoiceField(
        choices=(
            ("queued", "queued"),
            ("running", "running"),
            ("done", "done"),
            ("failed", "failed"),
        )
    )


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
            "task_id",
            "status",
            "progress",
            "result",
            "error",
            "created_at",
            "completed_at",
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
        result = {
            "text": meta.get("text"),
            "url": meta.get("url"),
            "input_url": meta.get("input_url") or in_meta.get("image_url"),
            "cost_usd": float(obj.cost_usd or 0),
            "runtime_ms": obj.duration_ms or 0,
        }
        slug = getattr(obj.tool, "slug", None) if obj.tool_id else None
        if slug == "image-compressor":
            result["compression"] = {
                "filename": meta.get("filename"),
                "format": meta.get("format"),
                "input_size": meta.get("input_size", 0),
                "output_size": meta.get("output_size", 0),
                "bytes_saved": meta.get("bytes_saved", 0),
                "percent_saved": meta.get("percent_saved", 0.0),
                "width": meta.get("width"),
                "height": meta.get("height"),
                "method": meta.get("method"),
            }
        elif slug == "flyer-generator":
            result["flyer"] = {
                "preset_slug": meta.get("preset_slug"),
                "pdf_url": meta.get("pdf_url"),
                "pdf_path": meta.get("pdf_path"),
                "pdf_bytes": meta.get("pdf_bytes", 0),
                "pdf_format": meta.get("pdf_format"),
            }
        return result

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
        source="cost_usd",
        max_digits=8,
        decimal_places=4,
        read_only=True,
    )

    class Meta:
        model = ToolUsage
        fields = (
            "id",
            "tool_id",
            "status",
            "input_meta",
            "token_cost_usd",
            "created_at",
        )
        read_only_fields = fields

    # Limit echoed input_meta to non-sensitive keys.
    SAFE_INPUT_KEYS = (
        "property_type",
        "beds",
        "baths",
        "sqft",
        "tone",
        "preserve_layout",
        "model",
    )

    def get_input_meta(self, obj: ToolUsage) -> dict:
        meta = obj.input_meta or {}
        return {k: meta[k] for k in self.SAFE_INPUT_KEYS if k in meta}
