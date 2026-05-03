"""Audit: ActionLog (writes) + AccessLog (reads of staff surfaces)."""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ActionLog(TimeStampedModel):
    """Every staff write — model creates / updates / deletes. Append-only."""

    actor       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name="actions")
    action      = models.CharField(max_length=64, db_index=True)  # e.g. "accounts.User.update"
    target_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    target_id   = models.PositiveBigIntegerField(null=True, blank=True)
    target      = GenericForeignKey("target_type", "target_id")

    before = models.JSONField(null=True, blank=True)
    after  = models.JSONField(null=True, blank=True)
    diff   = models.JSONField(null=True, blank=True)  # field-level diff for fast read
    ip     = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "Action log"
        verbose_name_plural = "Action logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self) -> str:
        return f"{self.actor or 'system'} {self.action} @ {self.created_at:%Y-%m-%d %H:%M}"


class Surface(models.TextChoices):
    ADMIN     = "admin",     _("Django admin")
    MOD       = "mod",       _("Moderator console")
    OPERATOR  = "operator",  _("Operator dashboard")


class AccessLog(TimeStampedModel):
    """Every staff route hit. For 'moderator was creeping' detection."""

    actor       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name="accesses")
    surface     = models.CharField(max_length=10, choices=Surface.choices, db_index=True)
    path        = models.CharField(max_length=500)
    method      = models.CharField(max_length=10)
    status_code = models.PositiveSmallIntegerField()
    ip          = models.GenericIPAddressField(null=True)
    user_agent  = models.CharField(max_length=400, blank=True)

    class Meta:
        verbose_name = "Access log"
        verbose_name_plural = "Access logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "surface", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.actor} {self.method} {self.path} → {self.status_code}"
