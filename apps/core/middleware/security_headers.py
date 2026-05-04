"""Defense-in-depth security headers.

Caddy already sets these in production, but Django emits them too so behavior
is identical when running behind any proxy or directly. Headers chosen for low
breakage on third-party embeds (YouTube, Instagram via /videos/) by isolating
COEP to mutating endpoints.
"""
from __future__ import annotations

from django.conf import settings

# Paths where stricter cross-origin isolation is safe (no third-party iframes /
# media). Anything under /api, /admin, /dashboard, /mod, /operator.
_STRICT_PREFIXES = ("/api/", "/admin/", "/dashboard/", "/mod/", "/operator/")
# Paths that should be unindexable by search engines.
_NOINDEX_PREFIXES = ("/api/", "/admin/", "/dashboard/", "/mod/", "/operator/")


class SecurityHeadersMiddleware:
    """Set extra defensive headers on every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path or "/"

        # X-Permitted-Cross-Domain-Policies — block legacy Adobe products.
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        # Cross-Origin-Opener-Policy — protect window.opener.
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        # Cross-Origin-Resource-Policy — same-origin for app endpoints.
        if path.startswith(_STRICT_PREFIXES):
            response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        else:
            response.setdefault("Cross-Origin-Resource-Policy", "same-site")

        # COEP only on strict prefixes — third-party iframes (YouTube) need CORP
        # headers we cannot guarantee. Never apply COEP universally.
        if (
            getattr(settings, "ENABLE_COEP", False)
            and path.startswith(_STRICT_PREFIXES)
        ):
            response.setdefault("Cross-Origin-Embedder-Policy", "require-corp")

        # X-Robots-Tag — keep staff + API endpoints out of public indexes.
        if path.startswith(_NOINDEX_PREFIXES):
            response.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive")

        # Hard belt-and-braces nosniff (SecurityMiddleware already sets, but
        # if it's ever stripped we fall back here).
        response.setdefault("X-Content-Type-Options", "nosniff")

        return response
