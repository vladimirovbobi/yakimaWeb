"""Celery tasks: morning digest email + maintenance."""
from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Notification

User = get_user_model()


@shared_task
def deliver_email_digest() -> dict:
    """Run daily: collate unread notifications per user → one email each.

    Sends a digest only to users with at least one un-emailed unread row.
    Marks rows as emailed_at after delivery so we don't double-send.
    """
    from django.core.mail import EmailMultiAlternatives

    cutoff = timezone.now() - timedelta(days=7)
    rows = (Notification.objects
            .filter(read_at__isnull=True, emailed_at__isnull=True,
                    created_at__gte=cutoff)
            .select_related("user")
            .order_by("user_id", "-created_at"))

    by_user: dict[int, list[Notification]] = {}
    for n in rows:
        by_user.setdefault(n.user_id, []).append(n)

    sent = 0
    for user_id, notes in by_user.items():
        user = notes[0].user
        if not user.email:
            continue
        ctx = {
            "user": user,
            "notes": notes[:25],
            "total_unread": len(notes),
            "site_name": getattr(settings, "SITE_NAME", "Yakima Real Estate Hub"),
        }
        html = render_to_string("emails/notification_digest.html", ctx)
        text = render_to_string("emails/notification_digest.txt", ctx)
        msg = EmailMultiAlternatives(
            subject=f"You have {len(notes)} new notifications",
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html, "text/html")
        try:
            msg.send(fail_silently=False)
        except Exception:  # noqa: BLE001
            continue
        ids = [n.pk for n in notes]
        Notification.objects.filter(pk__in=ids).update(emailed_at=timezone.now())
        sent += 1

    return {"users_emailed": sent, "rows": rows.count()}


@shared_task
def purge_old_notifications(days: int = 90) -> int:
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = Notification.objects.filter(
        created_at__lt=cutoff, read_at__isnull=False,
    ).delete()
    return deleted
