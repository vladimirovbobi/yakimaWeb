"""Daily Gemini spend cap — enforced via Redis counters.

Pre-flight check happens *before* the LLM call inside the Celery task. If
already over budget, raise SpendCapExceeded and the task records a BLOCKED
ToolUsage with `block_reason='spend_cap_exceeded'`.

After a successful call, increment by the realized cost in cents so subsequent
runs see the latest total. We track in cents to keep keys integer-safe.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

log = logging.getLogger(__name__)

_KEY_TMPL = "gemini:spend:{ymd}"
_TTL = timedelta(days=2).total_seconds()


class SpendCapExceeded(Exception):
    """Raised when today's spend has already met or exceeded the cap."""


def _today_key() -> str:
    return _KEY_TMPL.format(ymd=timezone.now().strftime("%Y-%m-%d"))


def _cap_cents() -> int:
    cap_usd = float(getattr(settings, "GEMINI_DAILY_SPEND_CAP_USD", 0) or 0)
    return int(cap_usd * 100)


def get_today_spend_cents() -> int:
    return int(cache.get(_today_key()) or 0)


def get_today_spend_usd() -> float:
    return get_today_spend_cents() / 100.0


def remaining_budget_usd() -> float:
    cap = _cap_cents()
    if cap <= 0:
        return float("inf")
    return max(0, cap - get_today_spend_cents()) / 100.0


def check_budget() -> None:
    """Raise SpendCapExceeded if today's spend has hit the cap.

    A cap of 0 means unbounded (dev mode); we don't enforce in that case.
    """
    cap = _cap_cents()
    if cap <= 0:
        return
    spent = get_today_spend_cents()
    if spent >= cap:
        log.warning("gemini spend cap hit: %s/%s cents", spent, cap)
        raise SpendCapExceeded(
            f"Daily Gemini cap reached ({spent / 100:.2f}/{cap / 100:.2f} USD)."
        )


def record_spend_usd(amount_usd: float) -> int:
    """Increment today's spend by `amount_usd`. Returns new total in cents."""
    cents = max(0, int(round(float(amount_usd) * 100)))
    if cents == 0:
        return get_today_spend_cents()
    key = _today_key()
    cache.add(key, 0, timeout=int(_TTL))
    try:
        new_total = cache.incr(key, cents)
    except ValueError:
        # Key fell out under us; reset.
        cache.set(key, cents, timeout=int(_TTL))
        new_total = cents
    return int(new_total)
