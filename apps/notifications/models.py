"""Notification: per-user inbox row with kind, payload, and read state."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class NotificationKind(models.TextChoices):
    LEAD_RECEIVED          = "lead_received",          _("New lead received")
    LEAD_MESSAGE           = "lead_message",           _("New message on lead")
    LEAD_WON               = "lead_won",               _("Lead marked won")
    REVIEW_RECEIVED        = "review_received",        _("New review")
    COMMENT_REPLY          = "comment_reply",          _("Reply to your comment")
    FORUM_REPLY            = "forum_reply",            _("Reply on your thread")
    MOD_DECISION           = "mod_decision",           _("Moderation decision")
    VENDOR_APPROVED        = "vendor_approved",        _("Vendor approved")
    LICENSE_EXPIRING_SOON  = "license_expiring_soon",  _("License expiring soon")


class Notification(TimeStampedModel):
    """A single user-facing notification row."""

    user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="notifications")
    kind    = models.CharField(max_length=32, choices=NotificationKind.choices, db_index=True)
    title   = models.CharField(max_length=200)
    body    = models.TextField(blank=True, max_length=2000)
    link    = models.CharField(max_length=512, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)
    emailed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "read_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind} → {self.user} @ {self.created_at:%Y-%m-%d}"

    @property
    def is_read(self) -> bool:
        return self.read_at is not None
