"""Audit Celery tasks — anomaly scan + notifier."""
from __future__ import annotations

import logging

from celery import shared_task

from apps.audit.services import anomaly_detector

log = logging.getLogger(__name__)


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

    if high:
        try:
            from apps.notifications.tasks import notify_operator  # type: ignore[attr-defined]

            for finding in high:
                notify_operator.delay(
                    subject=f"[anomaly:HIGH] {finding.pattern}",
                    body=(
                        f"target={finding.target_id}\n"
                        f"evidence={finding.evidence}"
                    ),
                )
        except Exception as exc:
            log.exception("Could not notify operator on HIGH anomaly: %s", exc)

    return len(findings)
