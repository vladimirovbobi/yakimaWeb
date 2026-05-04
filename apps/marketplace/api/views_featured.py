"""Featured-services endpoint — picks 1-3 marketplace services for in-content ad slots."""
from __future__ import annotations

from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.throttling import FeaturedAnonThrottle

from ..services.featured import pick_for_context


class FeaturedServiceCardSerializer(serializers.Serializer):
    """Tight payload for ad-slot rendering. Fields chosen to mirror what the
    `FeaturedServices` React component renders without overfetching."""

    id           = serializers.IntegerField(read_only=True)
    slug         = serializers.SlugField(read_only=True)
    title        = serializers.CharField(read_only=True)
    summary      = serializers.SerializerMethodField()
    category     = serializers.SerializerMethodField()
    starting_price_cents = serializers.SerializerMethodField()
    cover_image  = serializers.SerializerMethodField()
    vendor       = serializers.SerializerMethodField()
    rating_avg   = serializers.SerializerMethodField()

    def get_summary(self, obj) -> str:
        text = (obj.description or "").strip()
        return text[:120].rstrip() + ("…" if len(text) > 120 else "")

    def get_category(self, obj) -> dict | None:
        if obj.category is None:
            return None
        return {"slug": obj.category.slug, "label": obj.category.label}

    def get_starting_price_cents(self, obj) -> int | None:
        pkg = obj.packages.order_by("price_low").first()
        if pkg is None:
            return None
        try:
            return int(float(pkg.price_low) * 100)
        except (TypeError, ValueError):
            return None

    def get_cover_image(self, obj) -> dict | None:
        if not obj.hero_image:
            return None
        try:
            return {"url": obj.hero_image.url}
        except (ValueError, AttributeError):
            return None

    def get_vendor(self, obj) -> dict:
        v = obj.vendor
        return {
            "id":            v.id,
            "slug":          v.slug,
            "business_name": v.business_name,
            "tagline":       v.tagline,
        }

    def get_rating_avg(self, obj) -> float | None:
        v = getattr(obj, "rating_avg", None)
        if v is None:
            return None
        try:
            return round(float(v), 2)
        except (TypeError, ValueError):
            return None


class FeaturedServicesView(APIView):
    """GET /api/public/v1/services/featured/?context=...&category=...&seed=...&limit=...

    Public endpoint, anonymous-friendly. Used by content surfaces (blog posts,
    forum threads, tool pages) to render in-context ad slots without exposing
    the marketplace structure prematurely.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_classes = [FeaturedAnonThrottle]

    def get(self, request, *args, **kwargs):
        context_kind = (request.query_params.get("context") or "blog").strip()[:64]
        category     = request.query_params.get("category")
        seed_key     = request.query_params.get("seed")
        limit_raw    = request.query_params.get("limit") or "2"
        try:
            limit = max(1, min(int(limit_raw), 6))
        except ValueError:
            limit = 2

        services = pick_for_context(
            context_kind,
            category=category,
            seed_key=seed_key,
            limit=limit,
        )
        return Response({
            "context": context_kind,
            "results": FeaturedServiceCardSerializer(services, many=True).data,
        })
