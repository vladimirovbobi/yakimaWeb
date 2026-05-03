"""Auto-log writes by staff users via post_save / post_delete on key models."""
import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .middleware import get_current_request, get_current_user
from .models import ActionLog

log = logging.getLogger(__name__)

# Models we audit on every write. Add to this list as new models ship.
AUDITED_MODELS = {
    "accounts.User", "accounts.RealtorProfile", "accounts.VendorProfile",
    "accounts.LicenseCheck", "moderation.ModerationDecision", "moderation.Flag",
}


def _model_label(instance) -> str:  # noqa: ANN001
    return f"{instance._meta.app_label}.{instance._meta.model_name.title()}"


def _request_meta() -> tuple[str, str]:
    """Pull IP + UA from current request (None safe)."""
    req = get_current_request()
    if req is None:
        return ("", "")
    ip = req.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or req.META.get("REMOTE_ADDR", "")
    ua = req.META.get("HTTP_USER_AGENT", "")[:400]
    return (ip, ua)


@receiver(post_save)
def _on_save(sender, instance, created, **kwargs):  # noqa: ANN001
    label = _model_label(instance)
    if label not in AUDITED_MODELS:
        return
    actor = get_current_user()
    if actor is None or not getattr(actor, "is_staff", False):
        return  # Only log staff writes — user signups etc. don't pollute the log

    ip, ua = _request_meta()
    try:
        ct = ContentType.objects.get_for_model(instance.__class__)
        ActionLog.objects.create(
            actor=actor,
            action=f"{label}.{'create' if created else 'update'}",
            target_type=ct, target_id=instance.pk,
            ip=ip or None, user_agent=ua,
        )
    except Exception as e:  # noqa: BLE001
        log.exception("audit signal failed: %s", e)


@receiver(post_delete)
def _on_delete(sender, instance, **kwargs):  # noqa: ANN001
    label = _model_label(instance)
    if label not in AUDITED_MODELS:
        return
    actor = get_current_user()
    if actor is None or not getattr(actor, "is_staff", False):
        return
    ip, ua = _request_meta()
    try:
        ct = ContentType.objects.get_for_model(instance.__class__)
        ActionLog.objects.create(
            actor=actor,
            action=f"{label}.delete",
            target_type=ct, target_id=instance.pk,
            ip=ip or None, user_agent=ua,
        )
    except Exception as e:  # noqa: BLE001
        log.exception("audit delete signal failed: %s", e)
