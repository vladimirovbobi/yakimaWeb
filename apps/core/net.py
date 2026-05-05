"""Network helpers — currently only `client_ip`.

Why this exists
---------------
The platform runs behind Caddy (per ADR-0007). Caddy injects `X-Forwarded-For`
and `X-Real-IP` after authoritatively recording the upstream socket peer. We
must ONLY trust those headers when the immediate `REMOTE_ADDR` is the trusted
proxy. Otherwise an attacker hitting the API container directly could spoof
their own IP and bypass IP-allowlist + session-fingerprint defenses.

Settings
--------
`TRUSTED_PROXIES` — list of IP/CIDR strings that may legitimately set XFF.
Default covers loopback + Docker bridge ranges in dev. In prod set this to
just the Caddy container's IP (or to the upstream LB's range on Railway/Fly).
"""
from __future__ import annotations

import ipaddress
from typing import Iterable

from django.conf import settings


_DEFAULT_TRUSTED = [
    "127.0.0.1",
    "::1",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "fc00::/7",
]


def _trusted_proxies() -> Iterable[str]:
    return getattr(settings, "TRUSTED_PROXIES", _DEFAULT_TRUSTED)


def _is_trusted(ip: str) -> bool:
    if not ip:
        return False
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for entry in _trusted_proxies():
        try:
            if "/" in entry:
                if addr in ipaddress.ip_network(entry, strict=False):
                    return True
            elif addr == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False


def client_ip(request) -> str:
    """Return the best-effort client IP, honoring XFF only from trusted proxies.

    Algorithm:
      1. Read `REMOTE_ADDR`.
      2. If `REMOTE_ADDR` is in `TRUSTED_PROXIES`, the originating client is the
         leftmost entry of `X-Forwarded-For`. Walk left-to-right, returning the
         first IP that is NOT in TRUSTED_PROXIES.
      3. Otherwise, return `REMOTE_ADDR` itself.
    """
    remote = (request.META.get("REMOTE_ADDR") or "").strip()
    if not _is_trusted(remote):
        return remote

    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if not fwd:
        # Trusted proxy spoke directly without XFF — best we have is its addr.
        return remote
    parts = [p.strip() for p in fwd.split(",") if p.strip()]
    for ip in parts:
        if not _is_trusted(ip):
            return ip
    # All hops were trusted proxies — fall back to leftmost.
    return parts[0] if parts else remote
