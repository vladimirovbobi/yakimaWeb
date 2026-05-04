"""Pick contextually-relevant marketplace services to feature inside content surfaces.

Used for in-content "sponsored" / "featured" ad slots on blog posts, forum
threads, tool landing pages, and lead-magnet outputs. Vendors get visibility,
content surfaces get a non-intrusive monetization path, buyers get pointed at
the right service for what they're reading.

Selection rules (deterministic given the same `seed_key`):
  1. Filter services to active + moderation_status=approved.
  2. Apply context-driven category preference (a soft weight).
  3. Random sample with the seeded RNG so the feature mix is stable for a
     given page (better for caching, better for buyer recall).
  4. De-duplicate by vendor — a single ad slot should never show two
     services from the same vendor.

Cached in Redis (60-min TTL) keyed on (context_kind, category, seed_key, limit).
"""
from __future__ import annotations

import hashlib
import logging
import random
from collections.abc import Iterable

from django.core.cache import cache
from django.db.models import Avg, Q

from ..models import Service

log = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60 * 60  # 1 hour
DEFAULT_LIMIT = 2

# Category routing per content context. Map of (context_kind → ordered list of
# preferred top-level category labels). The first match wins; everything else
# is the fallback pool. These are slugs that match the seeded category tree
# — see apps/marketplace/management/commands/seed_categories.py.
CONTEXT_CATEGORY_PREFERENCES: dict[str, tuple[str, ...]] = {
    "blog":           ("photography", "staging", "marketing", "lending"),
    "blog/listing":   ("photography", "staging", "service"),
    "blog/finance":   ("lending", "legal-closing"),
    "blog/inspection": ("legal-closing", "service"),
    "blog/market":    ("marketing", "tech"),
    "forum":          ("photography", "service", "staging"),
    "forum/show-tell": ("photography", "staging"),
    "forum/help":     ("service", "legal-closing"),
    "tools":          ("photography", "staging", "marketing"),
    "tool/furniture-remover": ("staging", "photography"),
    "tool/description-writer": ("marketing", "photography"),
    "tool/image-compressor":   ("photography", "staging"),
    "landing":        ("photography", "staging"),
}


def _seed_int(seed_key: str | None) -> int:
    if not seed_key:
        return 0
    digest = hashlib.sha256(seed_key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _cache_key(context_kind: str, category: str | None, seed_key: str | None, limit: int) -> str:
    return f"featured:v1:{context_kind}:{category or '_'}:{seed_key or '_'}:{limit}"


def _preferred_categories(context_kind: str) -> tuple[str, ...]:
    if context_kind in CONTEXT_CATEGORY_PREFERENCES:
        return CONTEXT_CATEGORY_PREFERENCES[context_kind]
    base = context_kind.split("/", 1)[0]
    return CONTEXT_CATEGORY_PREFERENCES.get(base, ("photography", "staging"))


def _approved_services_qs(category_slugs: Iterable[str] | None = None):
    qs = (
        Service.objects
        .filter(is_active=True, moderation_status="approved")
        .select_related("vendor", "vendor__user", "category")
        .annotate(rating_avg=Avg("leads__review__rating",
                                  filter=Q(leads__review__moderation_status="approved")))
    )
    if category_slugs:
        slugs = list(category_slugs)
        qs = qs.filter(
            Q(category__slug__in=slugs)
            | Q(category__path__startswith=_path_prefixes_for(slugs))
        )
    return qs


def _path_prefixes_for(slugs: list[str]) -> str:
    """Treebeard MP_Node paths begin with a 4-char step. We want descendants of
    a top-level category — but ``startswith=``-of-list isn't supported by the
    ORM. We accept a single prefix here; for now this short-circuits via the
    ``slug__in`` clause which covers both top-level and direct-child categories
    in our seeded tree. Returning an empty string means "any path"."""
    return ""


def _select_with_fallback(
    preferred: tuple[str, ...],
    rng: random.Random,
    limit: int,
) -> list[Service]:
    chosen: list[Service] = []
    seen_vendor_ids: set[int] = set()

    # First pass: pull from preferred category pool.
    pool = list(_approved_services_qs(category_slugs=preferred)[:60])
    rng.shuffle(pool)
    for svc in pool:
        if svc.vendor_id in seen_vendor_ids:
            continue
        chosen.append(svc)
        seen_vendor_ids.add(svc.vendor_id)
        if len(chosen) >= limit:
            return chosen

    # Fallback: pull from any active service so we never return empty when
    # there's seeded data.
    if len(chosen) < limit:
        fallback = list(_approved_services_qs(category_slugs=None)[:60])
        rng.shuffle(fallback)
        for svc in fallback:
            if svc.vendor_id in seen_vendor_ids:
                continue
            chosen.append(svc)
            seen_vendor_ids.add(svc.vendor_id)
            if len(chosen) >= limit:
                break

    return chosen


def pick_for_context(
    context_kind: str,
    *,
    category: str | None = None,
    seed_key: str | None = None,
    limit: int = DEFAULT_LIMIT,
) -> list[Service]:
    """Pick `limit` services for the given content context.

    Args:
        context_kind: e.g. ``"blog"``, ``"forum/show-tell"``,
            ``"tool/furniture-remover"``. Drives the preferred category pool.
        category: Optional explicit category slug override. When supplied,
            takes precedence over ``context_kind``'s preferred list.
        seed_key: Stable key (e.g. blog post slug) so the same page shows the
            same featured set across reloads / users.
        limit: Maximum number of services to return.

    Returns:
        Up to `limit` Service rows, vendor-deduplicated.
    """
    limit = max(1, min(int(limit), 6))
    cache_key = _cache_key(context_kind, category, seed_key, limit)
    cached = cache.get(cache_key)
    if cached is not None:
        # Cache stores Service IDs to keep the entry small; rehydrate.
        services = list(_approved_services_qs().filter(pk__in=cached))
        order = {pk: i for i, pk in enumerate(cached)}
        services.sort(key=lambda s: order.get(s.pk, 999))
        return services

    rng = random.Random(  # noqa: S311 — ad-slot rotation, not crypto
        _seed_int(seed_key) or random.randint(1, 1_000_000),  # noqa: S311
    )
    preferred = (category,) if category else _preferred_categories(context_kind)

    try:
        chosen = _select_with_fallback(preferred, rng, limit)
    except Exception:
        log.exception("featured.pick_for_context failed; returning empty")
        chosen = []

    if chosen:
        cache.set(cache_key, [s.pk for s in chosen], CACHE_TTL_SECONDS)
    return chosen
