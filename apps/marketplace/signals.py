"""Marketplace moderation hooks."""
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.moderation.tasks import moderate_content

from .models import Bundle, Review, Service


@receiver(post_save, sender=Service)
def _moderate_service(sender, instance: Service, created: bool, **kwargs):  # noqa: ANN001
    if instance.description.strip():
        ct = ContentType.objects.get_for_model(Service)
        moderate_content.delay(ct.pk, instance.pk, text_attr="description",
                                context="service_description")


@receiver(post_save, sender=Bundle)
def _moderate_bundle(sender, instance: Bundle, created: bool, **kwargs):  # noqa: ANN001
    if instance.description.strip():
        ct = ContentType.objects.get_for_model(Bundle)
        moderate_content.delay(ct.pk, instance.pk, text_attr="description",
                                context="bundle_description")


@receiver(post_save, sender=Review)
def _moderate_review(sender, instance: Review, created: bool, **kwargs):  # noqa: ANN001
    if created and instance.body.strip():
        ct = ContentType.objects.get_for_model(Review)
        moderate_content.delay(ct.pk, instance.pk, text_attr="body", context="review")
