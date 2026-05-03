"""Moderation: ModeratableMixin (abstract), ModerationDecision, Flag."""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class ModerationStatus(models.TextChoices):
    PENDING  = "pending",  _("Pending")
    APPROVED = "approved", _("Approved")
    REMOVED  = "removed",  _("Removed")
    SHADOW   = "shadow",   _("Shadow-banned")


class ModeratableMixin(models.Model):
    """Every UGC model inherits this. No exceptions."""

    moderation_status = models.CharField(
        max_length=10, choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING, db_index=True,
    )
    moderation_score = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-4 severity
    moderated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class ModerationLayer(models.TextChoices):
    DETERMINISTIC = "deterministic", _("Deterministic")
    AI            = "ai",            _("AI")
    HUMAN         = "human",         _("Human")


class ModerationAction(models.TextChoices):
    APPROVE = "approve", _("Approve")
    QUEUE   = "queue",   _("Queue for human")
    REMOVE  = "remove",  _("Remove")
    SHADOW  = "shadow",  _("Shadow-ban")


class ModerationDecision(TimeStampedModel):
    """Audit row per classification — Generic FK to whatever was moderated."""

    target_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    target_id   = models.PositiveBigIntegerField(null=True)
    target      = GenericForeignKey("target_type", "target_id")

    layer       = models.CharField(max_length=14, choices=ModerationLayer.choices)
    classifier_ver = models.CharField(max_length=32, default="moderation_v1")
    input_hash  = models.CharField(max_length=64, db_index=True)  # sha256
    output      = models.JSONField(default=dict)
    action      = models.CharField(max_length=8, choices=ModerationAction.choices)
    severity    = models.PositiveSmallIntegerField(null=True)
    reason      = models.CharField(max_length=300, blank=True)

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name="moderation_decisions")

    class Meta:
        verbose_name = "Moderation decision"
        verbose_name_plural = "Moderation decisions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self) -> str:
        return f"{self.layer}/{self.action} sev={self.severity} {self.created_at:%Y-%m-%d}"


class FlagReason(models.TextChoices):
    SPAM       = "spam",       _("Spam")
    HARASSMENT = "harassment", _("Harassment")
    OFF_TOPIC  = "off_topic",  _("Off-topic")
    DOXXING    = "doxxing",    _("Doxxing / personal info")
    FRAUD      = "fraud",      _("Fraud / misrepresentation")
    OTHER      = "other",      _("Other")


class FlagStatus(models.TextChoices):
    OPEN      = "open",      _("Open")
    DISMISSED = "dismissed", _("Dismissed")
    ACTIONED  = "actioned",  _("Actioned")


class Flag(TimeStampedModel):
    """User-reported content."""

    target_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True)
    target_id   = models.PositiveBigIntegerField(null=True)
    target      = GenericForeignKey("target_type", "target_id")

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="flags_filed")
    reason   = models.CharField(max_length=12, choices=FlagReason.choices)
    notes    = models.TextField(blank=True, max_length=1000)
    status   = models.CharField(max_length=10, choices=FlagStatus.choices,
                                default=FlagStatus.OPEN, db_index=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="flags_resolved")

    class Meta:
        verbose_name = "Flag"
        verbose_name_plural = "Flags"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_reason_display()} by {self.reporter} @ {self.created_at:%Y-%m-%d}"
