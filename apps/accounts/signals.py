"""Accounts signals — touch_last_seen on login + role flips + tagline moderation."""
import logging

from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import RealtorProfile, Role, User, VendorProfile, VerificationStatus

log = logging.getLogger(__name__)


@receiver(user_logged_in)
def _on_login(sender, request, user, **kwargs):  # noqa: ANN001
    user.touch_last_seen()


@receiver(post_save, sender=RealtorProfile)
def _on_realtor_profile_save(sender, instance: RealtorProfile, **kwargs):  # noqa: ANN001
    """Sync is_realtor flag on User based on RealtorProfile.verification_status."""
    user = instance.user
    should_be = instance.verification_status == VerificationStatus.VERIFIED
    if user.is_realtor != should_be:
        user.is_realtor = should_be
        if should_be:
            user.role = Role.REALTOR
        elif user.role == Role.REALTOR:
            user.role = Role.MEMBER
        user.save(update_fields=["is_realtor", "role"])


# ─── Tagline moderation ──────────────────────────────────────────────────
# Vendor tagline is a CharField (not a ModeratableMixin model). Rather than
# migrating a tagline-specific model, hook pre_save: if the tagline changed,
# dispatch a Celery task that runs the moderation pipeline and clears the
# field if it's blocked. Keeps changes surgical.
@receiver(pre_save, sender=VendorProfile)
def _capture_tagline_change(sender, instance: VendorProfile, **kwargs):  # noqa: ANN001
    """Stash whether tagline changed so post_save can dispatch the task."""
    if not instance.pk:
        instance._tagline_changed = bool(instance.tagline)
        return
    try:
        prior = VendorProfile.objects.only("tagline").get(pk=instance.pk)
    except VendorProfile.DoesNotExist:
        instance._tagline_changed = bool(instance.tagline)
        return
    instance._tagline_changed = (prior.tagline or "") != (instance.tagline or "")


@receiver(post_save, sender=VendorProfile)
def _moderate_tagline(sender, instance: VendorProfile, **kwargs):  # noqa: ANN001
    """If tagline changed, queue moderation. Keeps cap small (160 chars)."""
    if not getattr(instance, "_tagline_changed", False):
        return
    if not (instance.tagline or "").strip():
        return
    try:
        from apps.accounts.tasks import moderate_vendor_tagline_task
        moderate_vendor_tagline_task.delay(instance.pk)
    except Exception:  # noqa: BLE001
        log.exception("failed to queue tagline moderation for vendor %s", instance.pk)
