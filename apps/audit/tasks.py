"""Audit Celery tasks — anomaly scan + operator notifier.

`notify_operator` lazy-imports `apps.notifications` to avoid the cycle:
    audit.tasks -> notifications.services -> notifications.signal_hooks -> audit.signals
"""
from __future__ import annotations

import logging
from typing import Any

from celery import shared_task

from apps.audit.services import anomaly_detector

log = logging.getLogger(__name__)


@shared_task(name="apps.audit.tasks.notify_operator", ignore_result=True)
def notify_operator(severity: str, pattern: str, evidence: Any) -> int:
    """Notify all active operators of an anomaly.

    Lazy-imports `apps.notifications` and `get_user_model` so the audit app
    stays importable even when notifications is not yet ready (e.g. during
    initial migrations).
    Returns the number of notifications written.
    """
    try:
        from django.contrib.auth import get_user_model

        from apps.notifications.services import notify
    except Exception:  # noqa: BLE001
        log.exception("notify_operator: lazy import failed")
        return 0

    User = get_user_model()
    title = f"[{severity}] {pattern}"[:200]
    body = str(evidence)[:500]

    sent = 0
    qs = User.objects.filter(groups__name="operator", is_active=True).distinct()
    for op in qs:
        if notify(op, "ops_alert", title=title, body=body) is not None:
            sent += 1
    return sent


@shared_task(name="apps.audit.tasks.run_anomaly_detection", ignore_result=True)
def run_anomaly_detection() -> int:
    """Run the hourly scan, log everything, page the operator on HIGH.

    Returns the number of findings (handy in tests).
    """
    findings = anomaly_detector.detect()
    high = [f for f in findings if f.severity == anomaly_detector.SEV_HIGH]

    for f in findings:
        log.warning(
            "audit.anomaly pattern=%s severity=%s target=%s evidence=%s",
            f.pattern,
            f.severity,
            f.target_id,
            f.evidence,
        )

    for finding in high:
        try:
            notify_operator.delay(
                severity=finding.severity,
                pattern=finding.pattern,
                evidence={"target_id": finding.target_id, **(finding.evidence or {})},
            )
        except Exception:  # noqa: BLE001
            log.exception("notify_operator dispatch failed")

    return len(findings)
