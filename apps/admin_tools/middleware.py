"""IP allowlist middleware for admin URLs."""
import ipaddress
import logging

from django.conf import settings
from django.http import HttpResponseForbidden

log = logging.getLogger(__name__)

PROTECTED_PREFIXES = ("/admin/",)


def _client_ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _ip_allowed(ip: str, allowlist: list[str]) -> bool:
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for entry in allowlist:
        try:
            if "/" in entry:
                if addr in ipaddress.ip_network(entry, strict=False):
                    return True
            elif addr == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False


class AdminIPAllowlistMiddleware:
    """Block access to /admin/ from non-allowlisted IPs (configurable via env)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowlist = list(getattr(settings, "ADMIN_IP_ALLOWLIST", []))

    def __call__(self, request):
        path = request.path or ""
        if any(path.startswith(p) for p in PROTECTED_PREFIXES) and self.allowlist:
            ip = _client_ip(request)
            if not _ip_allowed(ip, self.allowlist):
                log.warning("admin IP block: %s tried %s", ip, path)
                return HttpResponseForbidden(
                    "Admin access restricted by IP. Contact ops if you believe "
                    "this is in error."
                )
        return self.get_response(request)
