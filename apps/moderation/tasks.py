"""Celery: moderate UGC asynchronously after save."""
import logging

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import ModerationDecision, ModerationLayer, ModerationStatus
from .services.image_moderation import moderate_image
from .services.pipeline import moderate

log = logging.getLogger(__name__)


_IMAGE_ACTION_TO_STATUS = {
    "approve": ModerationStatus.APPROVED,
    "queue":   ModerationStatus.PENDING,
    "remove":  ModerationStatus.REMOVED,
}


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def moderate_content(self, content_type_id: int, object_id: int,
                     text_attr: str = "body", *, context: str = "default") -> str:
    """Run moderation pipeline against a Generic-FK target."""
    try:
        ct = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist:
        return "missing_content_type"

    target = ct.model_class().objects.filter(pk=object_id).first()
    if target is None:
        return "missing_target"

    text = getattr(target, text_attr, "") or ""
    if not text.strip():
        return "empty_text"

    result = moderate(text, target=target, context=context)
    log.info("moderated %s pk=%s → %s sev=%s",
             ct.model, object_id, result.action, result.severity)
    return result.action


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def moderate_image_task(self, content_type_id: int, object_id: int,
                        image_attr: str = "image") -> str:
    """Run image moderation against a Generic-FK target with image field.

    Fail-closed: any error path defaults to queue, never approve.
    """
    try:
        ct = ContentType.objects.get_for_id(content_type_id)
    except ContentType.DoesNotExist:
        return "missing_content_type"

    target = ct.model_class().objects.filter(pk=object_id).first()
    if target is None:
        return "missing_target"

    img_field = getattr(target, image_attr, None)
    if not img_field or not getattr(img_field, "name", ""):
        return "no_image"

    try:
        with img_field.open("rb") as fh:
            data = fh.read()
    except Exception:  # noqa: BLE001
        log.exception("image_attr open failed")
        return "image_unreadable"

    mime = getattr(img_field.file, "content_type", "image/jpeg") or "image/jpeg"
    result = moderate_image(data, mime=mime)

    ModerationDecision.objects.create(
        target_type=ct,
        target_id=object_id,
        layer=ModerationLayer.AI,
        classifier_ver="image_moderation_v1",
        input_hash="",
        output={
            "allowed": result.allowed,
            "categories": result.categories,
            "severity": result.severity,
            "reason": result.reason,
            "action": result.action,
            "kind": "image",
        },
        action=result.action if result.action != "approve" else "approve",
        severity=result.severity,
        reason=result.reason[:300],
    )

    if hasattr(target, "moderation_status"):
        target.moderation_status = _IMAGE_ACTION_TO_STATUS.get(
            result.action, ModerationStatus.PENDING,
        )
        target.moderated_at = timezone.now()
        target.save(update_fields=["moderation_status", "moderated_at"])

    log.info("moderated_image %s pk=%s → %s sev=%s",
             ct.model, object_id, result.action, result.severity)
    return result.action
