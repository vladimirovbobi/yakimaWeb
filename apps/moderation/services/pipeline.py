"""Three-layer moderation pipeline orchestrator.

Layer 1 (deterministic) → Layer 2 (AI) → Layer 3 (human queue).
Always writes a ModerationDecision audit row.
Always updates target.moderation_status / score / moderated_at.
"""
import logging
from dataclasses import dataclass

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from ..models import (ModerationAction, ModerationDecision, ModerationLayer,
                      ModerationStatus)
from . import injection_guard as ig
from .ai_classifier import classify as ai_classify
from .deterministic import deterministic_check, hash_input

log = logging.getLogger(__name__)

# action → moderation_status mapping
_ACTION_TO_STATUS = {
    ModerationAction.APPROVE: ModerationStatus.APPROVED,
    ModerationAction.QUEUE:   ModerationStatus.PENDING,
    ModerationAction.REMOVE:  ModerationStatus.REMOVED,
    ModerationAction.SHADOW:  ModerationStatus.SHADOW,
}


@dataclass
class PipelineResult:
    action: str
    severity: int
    reason: str
    layer: str


def moderate(content: str, *, target=None, context: str = "default",
             actor=None) -> PipelineResult:
    """Run the full pipeline against `content`. If `target` is given, update + log."""
    h = hash_input(content)

    # ─── Layer 1: deterministic ──────────────────────────────────────────
    det = deterministic_check(content, context=context)

    if det.blocked:
        result = PipelineResult(
            action=ModerationAction.REMOVE, severity=4, reason=det.reason,
            layer=ModerationLayer.DETERMINISTIC,
        )
        _record(target, result, h, layer_output={"flags": det.flags, "reason": det.reason},
                actor=actor)
        return result

    if det.queue:
        result = PipelineResult(
            action=ModerationAction.QUEUE, severity=3, reason=det.reason,
            layer=ModerationLayer.DETERMINISTIC,
        )
        _record(target, result, h, layer_output={"flags": det.flags, "reason": det.reason},
                actor=actor)
        return result

    # ─── Pre-guard for injection signals (informs Layer 2) ───────────────
    guard = ig.pre_flag(content)

    # ─── Layer 2: AI classifier ──────────────────────────────────────────
    cls = ai_classify(guard.sanitized_content, pre_flags=guard.pre_flagged)
    result = PipelineResult(
        action=cls.action, severity=cls.severity, reason=cls.reason,
        layer=ModerationLayer.AI,
    )
    _record(target, result, h,
            layer_output={
                "allowed": cls.allowed, "categories": cls.categories,
                "severity": cls.severity, "reason": cls.reason, "action": cls.action,
                "pre_flags": guard.pre_flagged, "classifier_ver": cls.classifier_ver,
            },
            actor=actor)
    return result


def _record(target, result: PipelineResult, input_hash: str,
            *, layer_output: dict, actor=None) -> None:
    """Write ModerationDecision + sync target.moderation_status."""
    target_type = ContentType.objects.get_for_model(target.__class__) if target else None
    target_id = target.pk if target else None

    ModerationDecision.objects.create(
        target_type=target_type,
        target_id=target_id,
        layer=result.layer,
        input_hash=input_hash,
        output=layer_output,
        action=result.action,
        severity=result.severity,
        reason=result.reason[:300],
        actor=actor,
    )

    if target is not None and hasattr(target, "moderation_status"):
        target.moderation_status = _ACTION_TO_STATUS.get(
            result.action, ModerationStatus.PENDING,
        )
        target.moderation_score = result.severity
        target.moderated_at = timezone.now()
        target.save(update_fields=["moderation_status", "moderation_score", "moderated_at"])
