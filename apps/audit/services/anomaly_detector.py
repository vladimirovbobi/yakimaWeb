"""Anomaly detector — pattern detection over recent ActionLog/AccessLog rows.

Run hourly via Celery beat (`apps.audit.tasks.run_anomaly_detection`).
High-severity findings page the operator (notification stub).

Patterns:
  - mass_writes_by_staff: single staff user with > N writes/hour
  - shared_ip_multi_user: same /24 authenticating as > N distinct users in 5 min
  - new_account_burst: account created in last hour with > 10 user-side writes
  - mass_flagging: same reporter raising > 5 flags in 1 hour
  - vendor_review_surge: > 5 reviews on a vendor in 1 hour
"""
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.audit.models import AccessLog, ActionLog

log = logging.getLogger(__name__)


# Tunables — keep generous so we don't false-positive on a busy moderator.
MASS_WRITES_THRESHOLD = 50
SHARED_IP_USER_THRESHOLD = 3
SHARED_IP_WINDOW_MIN = 5
NEW_ACCOUNT_WRITES_THRESHOLD = 10
MASS_FLAG_THRESHOLD = 5
VENDOR_REVIEW_THRESHOLD = 5

# Severity tiers — high pages on-call, medium goes to weekly review.
SEV_LOW = "low"
SEV_MEDIUM = "medium"
SEV_HIGH = "high"


@dataclass
class Finding:
    pattern: str
    severity: str
    target_id: str
    evidence: dict = field(default_factory=dict)


def detect(now=None) -> list[Finding]:
    """Run all detectors and return a flat list of findings."""
    now = now or timezone.now()
    findings: list[Finding] = []
    findings.extend(_mass_writes_by_staff(now))
    findings.extend(_shared_ip_multi_user(now))
    findings.extend(_new_account_burst(now))
    findings.extend(_mass_flagging(now))
    findings.extend(_vendor_review_surge(now))
    return findings


def _mass_writes_by_staff(now) -> Iterable[Finding]:
    since = now - timedelta(hours=1)
    rows = (
        ActionLog.objects.filter(created_at__gte=since)
        .values("actor_id")
        .annotate(c=Count("id"))
        .filter(c__gt=MASS_WRITES_THRESHOLD)
    )
    for r in rows:
        yield Finding(
            pattern="mass_writes_by_staff",
            severity=SEV_HIGH,
            target_id=f"user:{r['actor_id']}",
            evidence={"writes_in_hour": r["c"]},
        )


def _shared_ip_multi_user(now) -> Iterable[Finding]:
    since = now - timedelta(minutes=SHARED_IP_WINDOW_MIN)
    by_subnet: dict[str, set] = defaultdict(set)
    for row in AccessLog.objects.filter(
        created_at__gte=since, actor__isnull=False
    ).values("actor_id", "ip"):
        ip = row["ip"] or ""
        if not ip:
            continue
        # IPv4 /24
        if ip.count(".") == 3:
            subnet = ".".join(ip.split(".")[:3]) + ".0/24"
        else:
            parts = ip.split(":")
            subnet = ":".join(parts[:3]) + "::/48"
        by_subnet[subnet].add(row["actor_id"])
    for subnet, users in by_subnet.items():
        if len(users) > SHARED_IP_USER_THRESHOLD:
            yield Finding(
                pattern="shared_ip_multi_user",
                severity=SEV_HIGH,
                target_id=f"subnet:{subnet}",
                evidence={
                    "distinct_users": len(users),
                    "user_ids": sorted(users)[:10],
                    "window_minutes": SHARED_IP_WINDOW_MIN,
                },
            )


def _new_account_burst(now) -> Iterable[Finding]:
    """Detects accounts created in last hour producing > N writes.

    Yakima Web's custom User model uses ``created_at`` (from TimeStampedModel),
    falling back to ``date_joined`` if a future migration restores it.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    since = now - timedelta(hours=1)
    join_field = (
        "created_at"
        if any(f.name == "created_at" for f in User._meta.fields)
        else "date_joined"
    )
    new_users = list(
        User.objects.filter(**{f"{join_field}__gte": since}).values_list(
            "id", flat=True
        )
    )
    if not new_users:
        return
    rows = (
        ActionLog.objects.filter(created_at__gte=since, actor_id__in=new_users)
        .values("actor_id")
        .annotate(c=Count("id"))
        .filter(c__gte=NEW_ACCOUNT_WRITES_THRESHOLD)
    )
    for r in rows:
        yield Finding(
            pattern="new_account_burst",
            severity=SEV_MEDIUM,
            target_id=f"user:{r['actor_id']}",
            evidence={"writes_in_hour": r["c"]},
        )


def _mass_flagging(now) -> Iterable[Finding]:
    """Same reporter raising > N flags in an hour."""
    since = now - timedelta(hours=1)
    counter: Counter = Counter()
    for row in ActionLog.objects.filter(
        created_at__gte=since, action__contains="Flag.create"
    ).values_list("actor_id", flat=True):
        if row:
            counter[row] += 1
    for user_id, count in counter.items():
        if count > MASS_FLAG_THRESHOLD:
            yield Finding(
                pattern="mass_flagging",
                severity=SEV_MEDIUM,
                target_id=f"user:{user_id}",
                evidence={"flags_in_hour": count},
            )


def _vendor_review_surge(now) -> Iterable[Finding]:
    """> N reviews on a single vendor in 1 hour — likely review-bombing."""
    since = now - timedelta(hours=1)
    counter: Counter = Counter()
    rows = ActionLog.objects.filter(
        created_at__gte=since, action__contains="Review.create"
    ).values_list("target_id", flat=True)
    for vendor_id in rows:
        if vendor_id:
            counter[vendor_id] += 1
    for vendor_id, count in counter.items():
        if count > VENDOR_REVIEW_THRESHOLD:
            yield Finding(
                pattern="vendor_review_surge",
                severity=SEV_MEDIUM,
                target_id=f"vendor:{vendor_id}",
                evidence={"reviews_in_hour": count},
            )
