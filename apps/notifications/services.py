"""Single entry point: notify(user, kind, **kwargs) → Notification."""
from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from .models import Notification, NotificationKind

User = get_user_model()


def notify(
    user: Any,
    kind: str,
    *,
    title: str,
    body: str = "",
    link: str = "",
    payload: dict | None = None,
) -> Notification | None:
    """Emit one Notification. Returns None on invalid input.

    `user` may be a User instance or a user_id; we resolve it lazily to keep
    callers terse. `kind` MUST be one of NotificationKind values — unknowns are
    rejected so the inbox stays typed.
    """
    if user is None:
        return None
    if kind not in dict(NotificationKind.choices):
        return None
    user_id = user.pk if hasattr(user, "pk") else int(user)
    return Notification.objects.create(
        user_id=user_id,
        kind=kind,
        title=title[:200],
        body=(body or "")[:2000],
        link=(link or "")[:512],
        payload=payload or {},
    )


def mark_read(user, notification_ids: list[int]) -> int:
    from django.utils import timezone
    return (Notification.objects
            .filter(user=user, pk__in=notification_ids, read_at__isnull=True)
            .update(read_at=timezone.now()))


def mark_all_read(user) -> int:
    from django.utils import timezone
    return (Notification.objects
            .filter(user=user, read_at__isnull=True)
            .update(read_at=timezone.now()))


def unread_count(user) -> int:
    return Notification.objects.filter(user=user, read_at__isnull=True).count()
