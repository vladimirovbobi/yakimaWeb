"""Tools API views — public meta + private run dispatch + task-status polling."""
from __future__ import annotations

from typing import Any

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.core.api.throttling import AIToolThrottle

from ..models import Tool, ToolUsage, UsageStatus
from ..services.rate_limit import check_and_consume
from .serializers import (
    DescriptionWriterRequestSerializer,
    DescriptionWriterResponseSerializer,
    FurnitureRemoverRequestSerializer,
    FurnitureRemoverResponseSerializer,
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
class DescriptionWriterRunView(generics.GenericAPIView):
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
        return Response(DescriptionWriterResponseSerializer(body).data,
                        status=status.HTTP_202_ACCEPTED)


# ──────────────────────────────────────────────────────────────────────────
# Furniture remover
# ──────────────────────────────────────────────────────────────────────────
class FurnitureRemoverRunView(generics.GenericAPIView):
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
        usage = ToolUsage.objects.create(
            user=request.user,
            tool=tool,
            input_meta={
                "filename": image.name,
                "size": image.size,
                "preserve_layout": ser.validated_data["preserve_layout"],
            },
        )

        # TODO: wire `apps.tools.tasks.run_furniture_remover` (Phase 3 — port from
        # virtual-staging-app). For now we stage the upload bytes inside input_meta
        # and let the Phase-3 task pick it up.
        try:
            from apps.tools.tasks import run_furniture_remover  # type: ignore[attr-defined]
        except ImportError:
            run_furniture_remover = None
        if run_furniture_remover is not None:
            run_furniture_remover.delay(usage.pk)

        body = {
            "task_id": usage.pk,
            "status": UsageStatus.QUEUED,
            "original_url": None,
            "result_url": None,
        }
        return Response(FurnitureRemoverResponseSerializer(body).data,
                        status=status.HTTP_202_ACCEPTED)


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
