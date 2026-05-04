"""Wire up cross-app notify() emit points.

This module is imported in apps.NotificationsConfig.ready(). It connects
post_save signals from other apps to the notify() service. Keeping the
wiring in this app means the producer apps stay unaware of notification.
"""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import notify


# ─── Marketplace: lead created ────────────────────────────────────────────
def _wire_marketplace() -> None:
    try:
        from apps.marketplace.models import Lead, LeadMessage
    except Exception:  # noqa: BLE001 — apps may load in any order
        return

    @receiver(post_save, sender=Lead, dispatch_uid="notify_lead_received")
    def _on_lead_created(sender, instance: Lead, created: bool, **kwargs):  # noqa: ANN001
        if not created:
            return
        vendor_user_id = instance.vendor.user_id
        notify(
            vendor_user_id,
            "lead_received",
            title=f"New lead from {instance.buyer.get_short_name()}",
            body=(instance.message or "")[:240],
            link=f"/dashboard/vendor/leads/{instance.pk}",
            payload={"lead_id": instance.pk},
        )

    @receiver(post_save, sender=LeadMessage, dispatch_uid="notify_lead_message")
    def _on_leadmessage_created(sender, instance: LeadMessage, created: bool, **kwargs):  # noqa: ANN001
        if not created:
            return
        lead = instance.lead
        sender_id = instance.sender_id
        # Notify whichever party did NOT send the message.
        recipient_id = (lead.buyer_id if sender_id == lead.vendor.user_id
                        else lead.vendor.user_id)
        if recipient_id == sender_id:
            return
        notify(
            recipient_id,
            "lead_message",
            title=f"New message from {instance.sender.get_short_name()}",
            body=(instance.body or "")[:240],
            link=f"/dashboard/vendor/leads/{lead.pk}",
            payload={"lead_id": lead.pk, "message_id": instance.pk},
        )


# ─── Forum: reply on a thread ────────────────────────────────────────────
def _wire_forum() -> None:
    try:
        from apps.forum.models import ForumReply
    except Exception:  # noqa: BLE001
        return

    @receiver(post_save, sender=ForumReply, dispatch_uid="notify_forum_reply")
    def _on_reply_created(sender, instance: ForumReply, created: bool, **kwargs):  # noqa: ANN001
        if not created:
            return
        thread = instance.thread
        if thread.author_id == instance.author_id:
            return
        notify(
            thread.author_id,
            "forum_reply",
            title=f"{instance.author.get_short_name()} replied to your thread",
            body=(instance.body or "")[:240],
            link=f"/forum/{thread.slug}",
            payload={"thread_id": thread.pk, "reply_id": instance.pk},
        )


# ─── Content: reply on a comment ─────────────────────────────────────────
def _wire_content() -> None:
    try:
        from apps.content.models import Comment
    except Exception:  # noqa: BLE001
        return

    @receiver(post_save, sender=Comment, dispatch_uid="notify_comment_reply")
    def _on_comment_reply_created(sender, instance: Comment, created: bool, **kwargs):  # noqa: ANN001
        if not created or not instance.parent_id:
            return
        parent = instance.parent
        if parent.author_id == instance.author_id:
            return
        notify(
            parent.author_id,
            "comment_reply",
            title=f"{instance.author.get_short_name()} replied to your comment",
            body=(instance.body or "")[:240],
            link=f"/posts/{instance.post.slug}#comment-{instance.pk}",
            payload={"post_id": instance.post_id, "comment_id": instance.pk},
        )


# ─── Moderation: decision-acted on user content ──────────────────────────
def _wire_moderation() -> None:
    try:
        from apps.moderation.models import ModerationDecision
    except Exception:  # noqa: BLE001
        return

    @receiver(post_save, sender=ModerationDecision, dispatch_uid="notify_mod_decision")
    def _on_decision_action_taken(sender, instance: ModerationDecision, created: bool, **kwargs):  # noqa: ANN001
        if not created:
            return
        if instance.action not in ("remove", "shadow"):
            return
        target = instance.target
        if not target:
            return
        # Best-effort: pull the author/owner from common attribute names.
        author_id = (getattr(target, "author_id", None)
                     or getattr(target, "sender_id", None)
                     or getattr(target, "user_id", None))
        if not author_id:
            return
        notify(
            author_id,
            "mod_decision",
            title=f"Your content was {instance.get_action_display().lower()}",
            body=instance.reason or "",
            link="/dashboard/notifications",
            payload={"decision_id": instance.pk, "action": instance.action},
        )


_wire_marketplace()
_wire_forum()
_wire_content()
_wire_moderation()
