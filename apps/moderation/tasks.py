"""Celery: moderate UGC asynchronously after save."""
import logging

from celery import shared_task
from django.contrib.contenttypes.models import ContentType

from .services.pipeline import moderate

log = logging.getLogger(__name__)


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
