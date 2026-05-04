"""Core API views — public meta + liveness."""
from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import HealthzSerializer, SiteMetaSerializer

# Hardcoded navigation tree (move to model in v1.1 per ICD).
NAVIGATION_TREE = [
    {"label": "Home", "href": "/", "children": []},
    {"label": "Blog", "href": "/blog/", "children": []},
    {
        "label": "Services", "href": "/marketplace/",
        "children": [
            {"label": "Photography", "href": "/marketplace/photography/"},
            {"label": "Lending", "href": "/marketplace/lending/"},
            {"label": "Junk Removal", "href": "/marketplace/junk-removal/"},
            {"label": "3D Tours", "href": "/marketplace/3d-tours/"},
        ],
    },
    {"label": "Community", "href": "/community/", "children": []},
    {"label": "Tools", "href": "/tools/", "children": []},
    {"label": "About", "href": "/about/", "children": []},
    {"label": "Guidelines", "href": "/guidelines/", "children": []},
    {"label": "Privacy", "href": "/privacy/", "children": []},
    {"label": "Terms", "href": "/terms/", "children": []},
]


@method_decorator(cache_page(60), name="get")
class SiteMetaView(GenericAPIView):
    """GET /api/public/v1/meta/ — public site shell metadata. Cached 60s."""

    authentication_classes: list = []
    permission_classes = (AllowAny,)
    serializer_class = SiteMetaSerializer

    @extend_schema(responses=SiteMetaSerializer)
    def get(self, request: Request) -> Response:
        payload = {
            "site_name": getattr(settings, "SITE_NAME", "Yakima Real Estate Hub"),
            "site_tagline": getattr(settings, "SITE_TAGLINE", ""),
            "site_description": getattr(settings, "SITE_DESCRIPTION", ""),
            "contact_email": getattr(settings, "DEFAULT_FROM_EMAIL", "hello@yakimaweb.com"),
            "navigation": NAVIGATION_TREE,
            "feature_flags": {
                "ai_tools_enabled": bool(getattr(settings, "FEATURE_AI_TOOLS", False)),
                "marketplace_enabled": bool(getattr(settings, "FEATURE_MARKETPLACE", False)),
                "forum_enabled": bool(getattr(settings, "FEATURE_FORUM", False)),
            },
            "social_links": {
                "twitter": getattr(settings, "SOCIAL_TWITTER", ""),
                "facebook": getattr(settings, "SOCIAL_FACEBOOK", ""),
                "instagram": getattr(settings, "SOCIAL_INSTAGRAM", ""),
                "youtube": getattr(settings, "SOCIAL_YOUTUBE", ""),
            },
        }
        ser = self.get_serializer(payload)
        return Response(ser.data, status=status.HTTP_200_OK)


class HealthzView(GenericAPIView):
    """GET /api/public/v1/meta/healthz/ — liveness probe. No auth, no cache."""

    authentication_classes: list = []
    permission_classes = (AllowAny,)
    serializer_class = HealthzSerializer

    @extend_schema(responses=HealthzSerializer)
    def get(self, request: Request) -> Response:
        payload = {
            "status": "ok",
            "time": timezone.now(),
            "version": getattr(settings, "BUILD_SHA", ""),
        }
        ser = self.get_serializer(payload)
        resp = Response(ser.data, status=status.HTTP_200_OK)
        resp["Cache-Control"] = "no-store"
        return resp
