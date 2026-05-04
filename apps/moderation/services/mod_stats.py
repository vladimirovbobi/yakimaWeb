"""Per-moderator stats — computed on-the-fly via ModerationDecision queries.

Heuristics:
- items_reviewed: count of HUMAN-layer decisions by this moderator within window
- agreement_rate: human_action == prior AI action / total decisions
- reversal_rate: count of operator overrides on this mod's decisions / total
- avg_response_minutes: time between AI queue decision and human resolution
- current_streak: consecutive decisions without reversal
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.utils import timezone

from ..models import ModerationDecision, ModerationLayer


def _human_decisions_qs(user_id: int, since: timedelta):
    cutoff = timezone.now() - since
    return ModerationDecision.objects.filter(
        actor_id=user_id,
        layer=ModerationLayer.HUMAN,
        created_at__gte=cutoff,
    )


def _avg_response_minutes(qs) -> float:
    """Mean delta between (the prior AI decision on the same target) and the human decision.

    For each human decision, find prior AI decision on same target by input_hash.
    Cheap O(N) but bounded by `qs.count()` (small in practice).
    """
    deltas: list[float] = []
    for hd in qs.only("created_at", "input_hash", "target_type_id", "target_id"):
        prior = (ModerationDecision.objects
                 .filter(target_type_id=hd.target_type_id,
                         target_id=hd.target_id,
                         layer=ModerationLayer.AI,
                         created_at__lte=hd.created_at)
                 .order_by("-created_at").first())
        if prior is None:
            continue
        deltas.append((hd.created_at - prior.created_at).total_seconds() / 60.0)
    if not deltas:
        return 0.0
    return round(sum(deltas) / len(deltas), 2)


def _reversal_count(qs) -> int:
    """Count of decisions whose target had a *later* operator-override decision.

    An override is any HUMAN-layer decision by a different actor whose action
    differs from this moderator's action.
    """
    reversed_ = 0
    for d in qs.only("id", "target_type_id", "target_id", "action", "actor_id", "created_at"):
        later = ModerationDecision.objects.filter(
            target_type_id=d.target_type_id,
            target_id=d.target_id,
            layer=ModerationLayer.HUMAN,
            created_at__gt=d.created_at,
        ).exclude(actor_id=d.actor_id).exclude(action=d.action).exists()
        if later:
            reversed_ += 1
    return reversed_


def _agreement_rate(qs) -> float:
    """Human action matched the prior AI action / total decisions on items where AI had an opinion."""
    total = matched = 0
    for hd in qs.only("output", "action", "target_type_id", "target_id", "created_at"):
        prior = (ModerationDecision.objects
                 .filter(target_type_id=hd.target_type_id,
                         target_id=hd.target_id,
                         layer=ModerationLayer.AI,
                         created_at__lte=hd.created_at)
                 .order_by("-created_at").first())
        if prior is None:
            continue
        total += 1
        # Treat AI "queue" as match when human approved (mod confirmed AI uncertainty resolved).
        if prior.action == hd.action or (prior.action == "queue" and hd.action == "approve"):
            matched += 1
    if total == 0:
        return 0.0
    return round(matched / total, 3)


def _current_streak(user_id: int) -> int:
    """Latest consecutive decisions with no reversal."""
    streak = 0
    decisions = (ModerationDecision.objects
                 .filter(actor_id=user_id, layer=ModerationLayer.HUMAN)
                 .order_by("-created_at")
                 .only("id", "target_type_id", "target_id", "action", "actor_id", "created_at")[:200])
    for d in decisions:
        later = ModerationDecision.objects.filter(
            target_type_id=d.target_type_id,
            target_id=d.target_id,
            layer=ModerationLayer.HUMAN,
            created_at__gt=d.created_at,
        ).exclude(actor_id=d.actor_id).exclude(action=d.action).exists()
        if later:
            break
        streak += 1
    return streak


def _queue_position(user_id: int) -> int:  # noqa: ARG001
    """Best-effort 'where do you sit' relative to peers — by 30d throughput."""
    cutoff = timezone.now() - timedelta(days=30)
    counts: dict[int, int] = {}
    for d in (ModerationDecision.objects
              .filter(layer=ModerationLayer.HUMAN, created_at__gte=cutoff)
              .values("actor_id")
              .order_by()):
        # values() over only actor_id with implicit count requires annotate; do it manually
        counts.setdefault(d["actor_id"], 0)
    qs = (ModerationDecision.objects
          .filter(layer=ModerationLayer.HUMAN, created_at__gte=cutoff)
          .values_list("actor_id", flat=True))
    for actor_id in qs:
        if actor_id is None:
            continue
        counts[actor_id] = counts.get(actor_id, 0) + 1
    if not counts:
        return 1
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    for idx, (uid, _) in enumerate(ranked, start=1):
        if uid == user_id:
            return idx
    return len(ranked) + 1


def stats_for_moderator(
    user_id: int, since: timedelta = timedelta(days=30),
) -> dict[str, Any]:
    """Return moderator analytics dict.

    Returns:
        {
          items_reviewed_30d, items_reviewed_7d,
          agreement_rate, reversal_rate,
          avg_response_minutes, current_streak,
          queue_position
        }
    """
    qs_30 = _human_decisions_qs(user_id, since)
    qs_7 = _human_decisions_qs(user_id, timedelta(days=7))

    total_30 = qs_30.count()
    return {
        "items_reviewed_30d": total_30,
        "items_reviewed_7d": qs_7.count(),
        "agreement_rate": _agreement_rate(qs_30) if total_30 else 0.0,
        "reversal_rate": (
            round(_reversal_count(qs_30) / total_30, 3) if total_30 else 0.0
        ),
        "avg_response_minutes": _avg_response_minutes(qs_30),
        "current_streak": _current_streak(user_id),
        "queue_position": _queue_position(user_id),
    }


def stats_timeseries(
    user_id: int, days: int = 30,
) -> list[dict[str, Any]]:
    """Daily count of decisions for sparkline use. Returns [{day, count}, ...]."""
    cutoff = timezone.now() - timedelta(days=days)
    decisions = (ModerationDecision.objects
                 .filter(actor_id=user_id, layer=ModerationLayer.HUMAN, created_at__gte=cutoff)
                 .only("created_at"))
    buckets: dict[str, int] = {}
    for d in decisions:
        key = d.created_at.date().isoformat()
        buckets[key] = buckets.get(key, 0) + 1
    return [{"day": day, "count": count} for day, count in sorted(buckets.items())]
