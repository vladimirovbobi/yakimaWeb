"""Inject site-wide context (meta tags, feature flags, branding) into every template."""
from django.conf import settings


def site_meta(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "FEATURE_AI_TOOLS": settings.FEATURE_AI_TOOLS,
        "FEATURE_MARKETPLACE": settings.FEATURE_MARKETPLACE,
        "FEATURE_FORUM": settings.FEATURE_FORUM,
    }
