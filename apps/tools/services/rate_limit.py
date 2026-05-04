"""Redis-backed token bucket rate limiter for tool runs."""
from datetime import date

from django.core.cache import cache

from ..models import Tool, UsageStatus


def _bucket_key(user_id: int, tool_slug: str) -> str:
    return f"toolusage:{user_id}:{tool_slug}:{date.today().isoformat()}"


def check_and_consume(user, tool: Tool) -> tuple[bool, str]:
    """Atomically check whether `user` is under daily limit; if so, increment.

    Returns (allowed, reason). When `allowed=False`, reason explains why.
    """
    if not tool.is_enabled:
        return False, "tool_disabled"

    limit = tool.daily_limit_for(user)
    if limit == 0:
        return False, "no_quota"

    key = _bucket_key(user.pk, tool.slug)
    # 24h TTL — auto-resets daily. Race-safe via cache.add + incr.
    cache.add(key, 0, timeout=24 * 60 * 60)
    new_value = cache.incr(key)
    if new_value > limit:
        return False, "rate_limited"
    return True, "ok"


def usage_today(user, tool: Tool) -> int:
    return cache.get(_bucket_key(user.pk, tool.slug)) or 0


def daily_spend_usd(tool: Tool) -> float:
    """Sum cost_usd of today's successful runs for this tool. For spend cap."""
    from django.utils import timezone
    from django.db.models import Sum

    start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    agg = (tool.runs
           .filter(created_at__gte=start, status=UsageStatus.SUCCESS)
           .aggregate(total=Sum("cost_usd")))
    return float(agg["total"] or 0)
