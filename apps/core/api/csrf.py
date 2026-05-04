"""Strict CSRF double-submit verification for DRF viewsets.

Layered on top of Django's CsrfViewMiddleware. The default middleware is
session-aware but our public DRF API uses JWT cookies — Django still applies
CSRF if the request is "safe-method" or carries a session, but for unsafe
methods (POST/PUT/PATCH/DELETE) we want explicit, predictable enforcement on
viewsets that don't rely on sessions. This mixin makes that contract loud.

Pattern:
  class CommentViewSet(StrictCSRFMixin, viewsets.ModelViewSet): ...

Behavior:
  GET / HEAD / OPTIONS — no-op.
  POST / PUT / PATCH / DELETE — require X-CSRFToken header to match the
  CSRF cookie. Mismatch -> raise PermissionDenied with code "csrf_required".
"""
from __future__ import annotations

from django.conf import settings
from rest_framework.exceptions import PermissionDenied

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}


class CSRFRequired(PermissionDenied):
    """Sentinel: 403 with code 'csrf_required'."""

    default_detail = "CSRF token missing or invalid."
    default_code = "csrf_required"


class StrictCSRFMixin:
    """Apply to any DRF viewset / view that mutates state via cookie auth."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in UNSAFE:
            return

        cookie_name = getattr(settings, "CSRF_COOKIE_NAME", "csrftoken")
        header_name = getattr(
            settings, "CSRF_HEADER_NAME", "HTTP_X_CSRFTOKEN"
        )
        cookie_token = request.COOKIES.get(cookie_name)
        header_token = request.META.get(header_name) or request.META.get(
            "HTTP_X_CSRF_TOKEN"
        )

        if not cookie_token or not header_token:
            raise CSRFRequired("CSRF token missing.")
        # Constant-time compare via Django util.
        from django.utils.crypto import constant_time_compare

        if not constant_time_compare(cookie_token, header_token):
            raise CSRFRequired("CSRF token mismatch.")
