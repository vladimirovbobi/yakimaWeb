"""AI tool registry + per-run usage ledger."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Tool(TimeStampedModel):
    """Registry of AI tools available on the platform. Edit via Django admin."""

    slug         = models.SlugField(max_length=64, unique=True)
    name         = models.CharField(max_length=120)
    description  = models.TextField()
    model_id     = models.CharField(max_length=64,
                                     help_text="e.g. gemini-2.5-flash-image, gemini-2.5-pro")
    is_enabled   = models.BooleanField(default=False)
    cost_per_run_estimate_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    # Per-role daily rate limits (0 = unlimited)
    member_daily_limit  = models.PositiveIntegerField(default=10)
    realtor_daily_limit = models.PositiveIntegerField(default=100)

    class Meta:
        verbose_name = "Tool"
        verbose_name_plural = "Tools"

    def __str__(self) -> str:
        return self.name

    def daily_limit_for(self, user) -> int:
        if not user.is_authenticated:
            return 0
        if user.is_staff:
            return 999_999
        if user.is_realtor:
            return self.realtor_daily_limit
        return self.member_daily_limit


class UsageStatus(models.TextChoices):
    QUEUED   = "queued",   _("Queued")
    RUNNING  = "running",  _("Running")
    SUCCESS  = "success",  _("Success")
    FAILED   = "failed",   _("Failed")
    BLOCKED  = "blocked",  _("Blocked (moderation/rate-limit/spend-cap)")


class ToolUsage(TimeStampedModel):
    """One row per tool run. Source of truth for rate limits + cost tracking."""

    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name="tool_runs")
    tool        = models.ForeignKey(Tool, on_delete=models.PROTECT, related_name="runs")
    status      = models.CharField(max_length=10, choices=UsageStatus.choices,
                                    default=UsageStatus.QUEUED, db_index=True)
    input_meta  = models.JSONField(default=dict)   # dimensions, model overrides, params
    output_meta = models.JSONField(default=dict)   # output URL, length, hash
    tokens_in   = models.PositiveIntegerField(default=0)
    tokens_out  = models.PositiveIntegerField(default=0)
    cost_usd    = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    error       = models.TextField(blank=True)
    block_reason = models.CharField(max_length=64, blank=True)  # rate_limit / moderation / spend_cap
    duration_ms = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Tool usage"
        verbose_name_plural = "Tool usage"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "tool", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} · {self.tool.slug} · {self.status}"
