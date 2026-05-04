"""Trigger moderation pipeline on Post/Comment publish."""
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.moderation.tasks import moderate_content, moderate_image_task

from .models import Comment, Post


@receiver(post_save, sender=Post)
def _moderate_post(sender, instance: Post, created: bool, **kwargs):  # noqa: ANN001
    """Queue moderation for new + updated posts that have body content."""
    if not instance.body.strip():
        return
    # Only moderate when transitioning to published or on body edit
    if instance.moderation_status == "pending" or created:
        ct = ContentType.objects.get_for_model(Post)
        moderate_content.delay(ct.pk, instance.pk, text_attr="body", context="blog_post")


@receiver(post_save, sender=Comment)
def _moderate_comment(sender, instance: Comment, created: bool, **kwargs):  # noqa: ANN001
    if created and instance.body.strip():
        ct = ContentType.objects.get_for_model(Comment)
        moderate_content.delay(ct.pk, instance.pk, text_attr="body", context="comment")
    # Image moderation — runs whenever the image field is populated.
    # Routed to the dedicated `images` worker queue.
    if instance.image and instance.image.name:
        ct = ContentType.objects.get_for_model(Comment)
        moderate_image_task.apply_async(
            args=[ct.pk, instance.pk],
            kwargs={"image_attr": "image"},
            queue="images",
        )
