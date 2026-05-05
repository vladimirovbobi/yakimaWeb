"""StrictCSRFMixin: prove the double-submit invariant fires on real viewsets.

Targets `MeView` (PATCH /api/v1/me/) since the path requires only a logged-in
user — no models or external services. The mixin behaves identically across
every viewset it's bolted onto, so one focused proof per shape (header
missing, header mismatched, header matched) is enough.
"""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def _login(client: APIClient, user) -> str:
    """Force-authenticate and prime a CSRF cookie. Returns the token value."""
    client.force_authenticate(user=user)
    # GETting any URL primes the yw_csrf cookie via EnsureCSRFCookieMiddleware.
    client.get("/api/v1/me/")
    cookie = client.cookies.get("yw_csrf")
    assert cookie is not None, "EnsureCSRFCookieMiddleware did not set yw_csrf"
    return cookie.value


@pytest.mark.django_db
class TestStrictCSRFMixin:
    def test_missing_header_returns_403_csrf_required(self, user):
        client = APIClient(enforce_csrf_checks=False)
        _login(client, user)
        # No X-CSRFToken header — must reject.
        resp = client.patch("/api/v1/me/", {"full_name": "A"}, format="json")
        assert resp.status_code == 403
        # DRF surfaces our custom code on the response payload.
        assert "csrf" in (resp.data.get("detail", "")).lower()

    def test_mismatched_header_returns_403(self, user):
        client = APIClient(enforce_csrf_checks=False)
        token = _login(client, user)
        resp = client.patch(
            "/api/v1/me/",
            {"full_name": "A"},
            format="json",
            HTTP_X_CSRFTOKEN=token + "tampered",
        )
        assert resp.status_code == 403

    def test_matching_header_allows_through(self, user):
        client = APIClient(enforce_csrf_checks=False)
        token = _login(client, user)
        resp = client.patch(
            "/api/v1/me/",
            {"full_name": "Alice"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        # 200 from MeView (PATCH echoes PrivateUserSerializer); never 403.
        assert resp.status_code == 200
        assert resp.data["full_name"] == "Alice"

    def test_safe_method_skips_csrf(self, user):
        # GET /api/v1/me/ should never require CSRF.
        client = APIClient(enforce_csrf_checks=False)
        client.force_authenticate(user=user)
        resp = client.get("/api/v1/me/")
        assert resp.status_code == 200
