"""Tools API views — public meta + private run dispatch + task-status polling + SSE."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.csrf import StrictCSRFMixin
from apps.core.api.throttling import AIToolThrottle, ImageCompressorThrottle

from ..models import Tool, ToolUsage, UsageStatus
from ..services.flyer_presets import list_presets
from ..services.rate_limit import check_and_consume
from ..services.sse import stream_task_status
from .serializers import (
    DescriptionWriterRequestSerializer,
    DescriptionWriterResponseSerializer,
    FlyerPresetSerializer,
    FlyerRequestSerializer,
    FlyerResponseSerializer,
    FurnitureRemoverRequestSerializer,
    FurnitureRemoverResponseSerializer,
    ImageCompressorRequestSerializer,
    ImageCompressorResponseSerializer,
    ToolMetaSerializer,
    ToolTaskStatusSerializer,
)

# Static metadata for the public landing pages. Source of truth for marketing surfaces;
# can later move into the Tool model + admin if we want non-eng edits.
TOOL_META: list[dict[str, Any]] = [
    {
        "tool_id": "description-writer",
        "name": "AI Listing Description Writer",
        "description": (
            "Turn a few facts about a property into MLS-ready listing copy. "
            "Compliant tone, no Fair-Housing pitfalls, ~30s per run."
        ),
        "category": "writing",
        "requires_auth": True,
        "avg_runtime_seconds": 30,
        "rate_limit_per_hour": 10,
    },
    {
        "tool_id": "furniture-remover",
        "name": "Empty-Room Photo Tool",
        "description": (
            "Upload a furnished room; get an empty-room version back for staging. "
            "JPG or PNG, 10MB max."
        ),
        "category": "image",
        "requires_auth": True,
        "avg_runtime_seconds": 45,
        "rate_limit_per_hour": 10,
    },
    {
        "tool_id": "image-compressor",
        "name": "Lossless Image Compressor",
        "description": (
            "Shrink listing photos without losing a single pixel of quality. "
            "Supports JPG, PNG, WebP, HEIC, TIFF, GIF, BMP. Up to 50 MB per file."
        ),
        "category": "image",
        "requires_auth": True,
        "avg_runtime_seconds": 4,
        "rate_limit_per_hour": 60,
    },
    {
        "tool_id": "flyer-generator",
        "name": "Realtor Flyer Generator",
        "description": (
            "Pick a design preset, drop in property details and creative copy, "
            "get a print-ready PDF flyer in about a minute. Six curated styles."
        ),
        "category": "design",
        "requires_auth": True,
        "avg_runtime_seconds": 90,
        "rate_limit_per_hour": 5,
    },
]
TOOL_META_BY_ID = {t["tool_id"]: t for t in TOOL_META}


# ──────────────────────────────────────────────────────────────────────────
# Public meta
# ──────────────────────────────────────────────────────────────────────────
class ToolMetaListView(generics.ListAPIView):
    """GET /api/public/v1/tools/."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    serializer_class = ToolMetaSerializer
    pagination_class = None

    def get_queryset(self):
        return TOOL_META


class ToolMetaDetailView(generics.RetrieveAPIView):
    """GET /api/public/v1/tools/<slug>/."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    serializer_class = ToolMetaSerializer

    def get_object(self):
        slug = self.kwargs.get("slug")
        meta = TOOL_META_BY_ID.get(slug)
        if meta is None:
            raise NotFound("Unknown tool.")
        return meta


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _get_enabled_tool_or_400(slug: str) -> Tool:
    tool = Tool.objects.filter(slug=slug, is_enabled=True).first()
    if tool is None:
        raise ValidationError({"tool": f"Tool '{slug}' is not available."})
    return tool


def _enforce_rate_limit(user, tool: Tool) -> None:
    ok, reason = check_and_consume(user, tool)
    if not ok:
        raise ValidationError({"rate_limit": reason})


# ──────────────────────────────────────────────────────────────────────────
# Description writer
# ──────────────────────────────────────────────────────────────────────────
class DescriptionWriterRunView(StrictCSRFMixin, generics.GenericAPIView):
    """POST /api/v1/tools/description/."""

    serializer_class = DescriptionWriterRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIToolThrottle]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        tool = _get_enabled_tool_or_400("description-writer")
        _enforce_rate_limit(request.user, tool)

        d = ser.validated_data
        # Build a single facts blob for the existing description-writer service.
        facts_lines = [
            f"Property type: {d['property_type']}",
            f"Bedrooms: {d['beds']}",
            f"Bathrooms: {d['baths']}",
            f"Square feet: {d['sqft']}",
            f"Tone: {d['tone']}",
        ]
        if d.get("key_features"):
            facts_lines.append(f"Key features: {d['key_features']}")
        property_facts = "\n".join(facts_lines)

        usage = ToolUsage.objects.create(
            user=request.user,
            tool=tool,
            input_meta={
                "property_type": d["property_type"],
                "beds": d["beds"],
                "baths": str(d["baths"]),
                "sqft": d["sqft"],
                "tone": d["tone"],
                "property_facts": property_facts,
            },
        )
        # Reuse existing Celery task — moderates input, calls Gemini, persists.
        from apps.tools.tasks import run_description_writer

        run_description_writer.delay(usage.pk)

        body = {"task_id": usage.pk, "status": UsageStatus.QUEUED}
        return Response(
            DescriptionWriterResponseSerializer(body).data, status=status.HTTP_202_ACCEPTED
        )


# ──────────────────────────────────────────────────────────────────────────
# Furniture remover
# ──────────────────────────────────────────────────────────────────────────
class FurnitureRemoverRunView(StrictCSRFMixin, generics.GenericAPIView):
    """POST /api/v1/tools/furniture-remover/."""

    serializer_class = FurnitureRemoverRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIToolThrottle]
    parser_classes = None  # let DRF defaults (MultiPart + Form + JSON) apply

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        tool = _get_enabled_tool_or_400("furniture-remover")
        _enforce_rate_limit(request.user, tool)

        image = ser.validated_data["image"]
        # Stage the upload bytes in default_storage so the img-worker can pick
        # them up. We keep the path narrow: tools/furniture-remover/<uid>/uploads/...
        ts = timezone.now().strftime("%Y%m%dT%H%M%S")
        suffix = uuid.uuid4().hex[:8]
        ext = (image.name.rsplit(".", 1)[-1] or "jpg").lower()
        if ext not in {"jpg", "jpeg", "png"}:
            ext = "jpg"
        upload_path = f"tools/furniture-remover/{request.user.id}/uploads/{ts}-{suffix}.{ext}"
        default_storage.save(upload_path, ContentFile(image.read()))

        usage = ToolUsage.objects.create(
            user=request.user,
            tool=tool,
            input_meta={
                "filename": image.name,
                "size": image.size,
                "preserve_layout": ser.validated_data["preserve_layout"],
                "upload_path": upload_path,
            },
        )

        from apps.tools.tasks import run_furniture_remover

        run_furniture_remover.delay(usage.pk)

        body = {
            "task_id": usage.pk,
            "status": UsageStatus.QUEUED,
            "original_url": _safe_storage_url(upload_path),
            "result_url": None,
        }
        return Response(
            FurnitureRemoverResponseSerializer(body).data, status=status.HTTP_202_ACCEPTED
        )


def _safe_storage_url(path: str) -> str | None:
    try:
        return default_storage.url(path)
    except Exception:  # noqa: BLE001
        return None


# ──────────────────────────────────────────────────────────────────────────
# Image compressor (Sprint 1.5)
# ──────────────────────────────────────────────────────────────────────────
class ImageCompressorRunView(StrictCSRFMixin, generics.GenericAPIView):
    """POST /api/v1/tools/image-compressor/.

    Stages the upload bytes in default_storage; queues a Celery task that
    runs Pillow's lossless re-encode. Single-file submission. The frontend
    loops for batch upload so each file gets its own rate-limit slot.
    """

    serializer_class = ImageCompressorRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ImageCompressorThrottle]
    parser_classes = None

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        tool = _get_enabled_tool_or_400("image-compressor")
        _enforce_rate_limit(request.user, tool)

        image = ser.validated_data["image"]
        ts = timezone.now().strftime("%Y%m%dT%H%M%S")
        suffix = uuid.uuid4().hex[:8]
        ext = (image.name.rsplit(".", 1)[-1] or "jpg").lower()
        upload_path = f"tools/image-compressor/{request.user.id}/uploads/{ts}-{suffix}.{ext}"
        default_storage.save(upload_path, ContentFile(image.read()))

        usage = ToolUsage.objects.create(
            user=request.user,
            tool=tool,
            input_meta={
                "filename": image.name,
                "size": image.size,
                "upload_path": upload_path,
            },
        )

        from apps.tools.tasks import run_image_compressor

        run_image_compressor.delay(usage.pk)

        body = {"task_id": usage.pk, "status": UsageStatus.QUEUED}
        return Response(
            ImageCompressorResponseSerializer(body).data,
            status=status.HTTP_202_ACCEPTED,
        )


# ──────────────────────────────────────────────────────────────────────────
# Flyer generator (Sprint 2)
# ──────────────────────────────────────────────────────────────────────────
class FlyerPresetsView(generics.ListAPIView):
    """GET /api/public/v1/tools/flyer-generator/presets/ — preset gallery."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    serializer_class = FlyerPresetSerializer
    pagination_class = None

    def get_queryset(self):
        return [
            {
                "slug": preset.slug,
                "name": preset.name,
                "blurb": preset.blurb,
                "inspiration": preset.inspiration,
                "palette": preset.palette,
                "fonts": preset.fonts,
                "layout_brief": preset.layout_brief,
                "preview_image": preset.preview_image,
                "palette_token_names": preset.palette_token_names,
            }
            for preset in list_presets()
        ]


class FlyerGeneratorRunView(StrictCSRFMixin, generics.GenericAPIView):
    """POST /api/v1/tools/flyer-generator/."""

    serializer_class = FlyerRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AIToolThrottle]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        tool = _get_enabled_tool_or_400("flyer-generator")
        _enforce_rate_limit(request.user, tool)

        d = ser.validated_data
        usage = ToolUsage.objects.create(
            user=request.user,
            tool=tool,
            input_meta={
                "preset_slug": d["preset_slug"],
                "property_info": d["property_info"],
                "creative_text": d["creative_text"],
                "photo_urls": d["photo_urls"],
                "color_overrides": d.get("color_overrides") or {},
                "font_overrides": d.get("font_overrides") or {},
            },
        )

        from apps.tools.tasks import run_flyer_generator

        run_flyer_generator.delay(usage.pk)

        body = {"task_id": usage.pk, "status": UsageStatus.QUEUED}
        return Response(
            FlyerResponseSerializer(body).data,
            status=status.HTTP_202_ACCEPTED,
        )


# ──────────────────────────────────────────────────────────────────────────
# Task status (polling)
# ──────────────────────────────────────────────────────────────────────────
class ToolTaskStatusView(generics.RetrieveAPIView):
    """GET /api/v1/tools/tasks/<task_id>/ — owner-only."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ToolTaskStatusSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "task_id"

    def get_queryset(self):
        return ToolUsage.objects.filter(user=self.request.user).select_related("tool")


# ──────────────────────────────────────────────────────────────────────────
# Server-Sent Events stream — task progress
# ──────────────────────────────────────────────────────────────────────────
class ToolTaskStreamView(APIView):
    """GET /api/v1/streams/tools/<task_id>/ — owner-only SSE channel."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id: int):
        # Pre-flight ownership so we 404/403 fast before opening the stream.
        owned = ToolUsage.objects.filter(pk=task_id, user=request.user).exists()
        if not owned:
            raise NotFound("Task not found.")

        response = StreamingHttpResponse(
            stream_task_status(task_id, owner_id=request.user.id),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"  # Caddy/nginx: do not buffer
        response["Connection"] = "keep-alive"
        return response
