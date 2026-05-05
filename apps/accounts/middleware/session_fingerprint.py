"""Bind authenticated sessions to a fingerprint to detect token theft.

Fingerprint = (user_agent_class, ip_/24).
On mismatch we clear the JWT cookies and force re-login. We deliberately use a
broad fingerprint so legitimate IP changes (mobile carriers, VPN) don't kick
real users out — the goal is to catch a stolen cookie replayed from a wholly
different device class.

Stored in cache keyed by user PK — TTL = JWT refresh lifetime.
"""
from __future__ import annotations

import logging
import re

from django.conf import settings
from django.core.cache import cache

try:
    from user_agents import parse as ua_parse  # type: ignore[import-not-found]
    _UA_LIB_AVAILABLE = True
except ImportError:  # pragma: no cover - lib optional
    ua_parse = None  # type: ignore[assignment]
    _UA_LIB_AVAILABLE = False

log = logging.getLogger(__name__)

CACHE_PREFIX = "ywsfp:"  # yakima-web session fingerprint
CACHE_TTL_SECONDS = 14 * 24 * 60 * 60  # 14d, matches refresh token lifetime


_BROWSER_RE = re.compile(
    r"(Edg|Chrome|Safari|Firefox|Opera|MSIE|Trident|Brave)", re.IGNORECASE
)
_MOBILE_RE = re.compile(r"(iPhone|iPad|iPod|Android|Mobile|Tablet)", re.IGNORECASE)
_BOT_RE = re.compile(r"(bot|crawler|spider|slurp|wget|curl)", re.IGNORECASE)


def _ua_class(ua_string: str) -> str:
    """Coarse UA class — bot/mobile/tablet/desktop + browser family.

    Uses `user_agents` library when installed; falls back to a regex sniff
    so the middleware never crashes on a fresh checkout.
    """
    if not ua_string:
        return "unknown"
    if _UA_LIB_AVAILABLE:
        try:
            ua = ua_parse(ua_string)
            kind = (
                "bot"
                if ua.is_bot
                else "mobile"
                if ua.is_mobile
                else "tablet"
                if ua.is_tablet
                else "desktop"
            )
            return f"{kind}:{ua.browser.family}"
        except Exception as exc:  # noqa: BLE001
            log.debug("user_agents parse failed, falling back: %s", exc)
    # Fallback regex sniff
    if _BOT_RE.search(ua_string):
        kind = "bot"
    elif "iPad" in ua_string or "Tablet" in ua_string:
        kind = "tablet"
    elif _MOBILE_RE.search(ua_string):
        kind = "mobile"
    else:
        kind = "desktop"
    m = _BROWSER_RE.search(ua_string)
    family = m.group(1).lower() if m else "other"
    return f"{kind}:{family}"


def _ip_subnet(ip: str) -> str:
    """Truncate IPv4 to /24, IPv6 to /48."""
    if not ip:
        return ""
    if ":" in ip:
        parts = ip.split(":")
        return ":".join(parts[:3]) + "::/48"
    parts = ip.split(".")
    if len(parts) != 4:
        return ip
    return ".".join(parts[:3]) + ".0/24"


def _fingerprint(request) -> str:
    # Lazy import — avoids circular settings access at module load time and
    # lets tests stub apps.core.net without bringing extra modules.
    from apps.core.net import client_ip as _client_ip
    return (
        f"{_ua_class(request.META.get('HTTP_USER_AGENT', ''))}|"
        f"{_ip_subnet(_client_ip(request))}"
    )


class SessionFingerprintMiddleware:
    """Compare current request fingerprint to the one stored at login.

    On first authenticated request we record the fingerprint. On subsequent
    requests we compare; mismatch -> clear JWT cookies and continue the request
    as anonymous (user re-login required).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        invalid = False
        if user is not None and getattr(user, "is_authenticated", False):
            key = f"{CACHE_PREFIX}{user.pk}"
            current = _fingerprint(request)
            stored: str | None = cache.get(key)
            if stored is None:
                cache.set(key, current, CACHE_TTL_SECONDS)
            elif stored != current:
                log.warning(
                    "Session fingerprint mismatch for user=%s: stored=%s current=%s",
                    user.pk,
                    stored,
                    current,
                )
                invalid = True

        response = self.get_response(request)

        if invalid:
            self._invalidate(response)
        return response

    @staticmethod
    def _invalidate(response) -> None:
        access = getattr(settings, "JWT_AUTH_COOKIE", "yw_access")
        refresh = getattr(settings, "JWT_AUTH_REFRESH_COOKIE", "yw_refresh")
        access_path = getattr(settings, "JWT_AUTH_COOKIE_PATH", "/")
        refresh_path = getattr(settings, "JWT_AUTH_REFRESH_COOKIE_PATH", "/")
        response.delete_cookie(access, path=access_path)
        response.delete_cookie(refresh, path=refresh_path)
        response["X-Auth-Reset"] = "fingerprint-mismatch"
