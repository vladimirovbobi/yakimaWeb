"""Ensure the `yw_csrf` cookie is set on every response.

Django's CsrfViewMiddleware sets the cookie only when a view explicitly calls
``django.middleware.csrf.get_token(request)`` (or otherwise marks the request
as needing the token). Cookie-JWT clients never traverse a session-bound view,
so the cookie was only being set on the rare GET that happened to render a
CSRF form. The frontend `apiFetch` reads the cookie on every unsafe call —
without the cookie present, the double-submit invariant collapses.

Cheap fix: on each response, if the cookie is absent, prime the token. The
SecurityMiddleware-supplied CsrfViewMiddleware further down the chain handles
emitting the Set-Cookie via the standard rotation logic.
"""
from __future__ import annotations

from django.conf import settings
from django.middleware.csrf import get_token


class EnsureCSRFCookieMiddleware:
    """Force-prime the CSRF token so the cookie ships on every response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cookie_name = getattr(settings, "CSRF_COOKIE_NAME", "csrftoken")
        if cookie_name not in request.COOKIES:
            # Touch the token so CsrfViewMiddleware writes Set-Cookie.
            get_token(request)
        return self.get_response(request)
