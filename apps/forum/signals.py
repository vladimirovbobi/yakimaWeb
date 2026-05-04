"""Forum signals: trigger moderation + maintain denormalized counters."""
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.moderation.tasks import moderate_content

from .models import ForumReply, ForumThread, Vote


@receiver(post_save, sender=ForumThread)
def _moderate_thread(sender, instance: ForumThread, created: bool, **kwargs):  # noqa: ANN001
    if created and instance.body.strip():
        ct = ContentType.objects.get_for_model(ForumThread)
        moderate_content.delay(ct.pk, instance.pk, text_attr="body", context="forum_thread")


@receiver(post_save, sender=ForumReply)
def _moderate_reply(sender, instance: ForumReply, created: bool, **kwargs):  # noqa: ANN001
    if created and instance.body.strip():
        ct = ContentType.objects.get_for_model(ForumReply)
        moderate_content.delay(ct.pk, instance.pk, text_attr="body", context="forum_reply")
        ForumThread.objects.filter(pk=instance.thread_id).update(
            reply_count=instance.thread.replies.count(),
        )


@receiver(post_save, sender=Vote)
@receiver(post_delete, sender=Vote)
def _resync_score(sender, instance: Vote, **kwargs):  # noqa: ANN001
    """Recompute score on the target whenever a vote is added/removed/changed."""
    target = instance.target
    if target is None:
        return
    total = (Vote.objects
             .filter(target_type=instance.target_type, target_id=instance.target_id)
             .aggregate(s=Sum("value"))["s"] or 0)
    target.__class__.objects.filter(pk=target.pk).update(score=total)
