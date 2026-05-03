"""Accounts signals — touch_last_seen on login + grant role on verification."""
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RealtorProfile, Role, User, VerificationStatus


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
