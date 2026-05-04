"""Session-fingerprint middleware tests.

Verifies:
  - Same UA class + IP /24 -> no challenge.
  - Different UA class -> JWT cookies cleared.
  - Different IP /24 -> JWT cookies cleared.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory

from apps.accounts.middleware.session_fingerprint import (
    CACHE_PREFIX,
    SessionFingerprintMiddleware,
    _ip_subnet,
    _ua_class,
)

User = get_user_model()

CHROME_DESKTOP = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)
SAFARI_IOS = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


@pytest.fixture
def auth_user(db):
    return User.objects.create_user(
        email="fp@yakimaweb.local", password="x" * 12
    )


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def _make_request(rf: RequestFactory, ua: str, ip: str, user):
    req = rf.get("/")
    req.user = user
    req.META["HTTP_USER_AGENT"] = ua
    req.META["REMOTE_ADDR"] = ip
    return req


def _run(req):
    captured = HttpResponse("ok")
    mw = SessionFingerprintMiddleware(lambda _r: captured)
    return mw(req)


class TestHelpers:
    def test_ip_subnet_v4(self):
        assert _ip_subnet("10.0.0.5") == "10.0.0.0/24"

    def test_ip_subnet_v6(self):
        assert _ip_subnet("2001:db8::1").endswith("/48")

    def test_ua_class_desktop_browser(self):
        assert _ua_class(CHROME_DESKTOP).startswith("desktop:")

    def test_ua_class_mobile_safari(self):
        assert _ua_class(SAFARI_IOS).startswith("mobile:")

    def test_ua_class_unknown(self):
        assert _ua_class("") == "unknown"

    def test_ua_class_distinct_for_phone_vs_desktop(self):
        assert _ua_class(CHROME_DESKTOP) != _ua_class(SAFARI_IOS)


@pytest.mark.django_db
class TestMiddleware:
    def test_first_request_records_fingerprint(self, auth_user, rf):
        req = _make_request(rf, CHROME_DESKTOP, "10.0.0.5", auth_user)
        resp = _run(req)
        assert "X-Auth-Reset" not in resp
        assert cache.get(f"{CACHE_PREFIX}{auth_user.pk}") is not None

    def test_same_ua_class_same_subnet_no_challenge(self, auth_user, rf):
        req1 = _make_request(rf, CHROME_DESKTOP, "10.0.0.5", auth_user)
        _run(req1)
        # Different IP within /24, same UA family
        req2 = _make_request(rf, CHROME_DESKTOP, "10.0.0.99", auth_user)
        resp2 = _run(req2)
        assert "X-Auth-Reset" not in resp2

    def test_different_ua_class_invalidates(self, auth_user, rf):
        req1 = _make_request(rf, CHROME_DESKTOP, "10.0.0.5", auth_user)
        _run(req1)
        req2 = _make_request(rf, SAFARI_IOS, "10.0.0.5", auth_user)
        resp2 = _run(req2)
        assert resp2.get("X-Auth-Reset") == "fingerprint-mismatch"

    def test_different_subnet_invalidates(self, auth_user, rf):
        req1 = _make_request(rf, CHROME_DESKTOP, "10.0.0.5", auth_user)
        _run(req1)
        req2 = _make_request(rf, CHROME_DESKTOP, "192.168.1.1", auth_user)
        resp2 = _run(req2)
        assert resp2.get("X-Auth-Reset") == "fingerprint-mismatch"

    def test_anonymous_request_skipped(self, rf):
        req = rf.get("/")
        req.user = MagicMock(is_authenticated=False)
        resp = _run(req)
        assert "X-Auth-Reset" not in resp


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()
