"""Forum: Flair + Thread + Reply + Vote (Generic FK)."""
import math

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import TimeStampedModel
from apps.moderation.models import ModeratableMixin


class Flair(TimeStampedModel):
    """Tag categories — fixed list, edited by staff."""
    slug  = models.SlugField(max_length=32, unique=True)
    label = models.CharField(max_length=40)
    color = models.CharField(max_length=16, default="gold",
                              help_text="Tailwind color name: gold/ok/warn/err/mist")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "label"]

    def __str__(self) -> str:
        return self.label


class ForumThread(ModeratableMixin, TimeStampedModel):
    """A top-level forum post."""
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                related_name="threads")
    flair  = models.ForeignKey(Flair, on_delete=models.PROTECT, related_name="threads")
    title  = models.CharField(max_length=240)
    slug   = models.SlugField(max_length=280, unique=True, blank=True)
    body   = models.TextField(max_length=10_000)
    score  = models.IntegerField(default=0, db_index=True)  # denormalized vote sum
    reply_count = models.PositiveIntegerField(default=0)
    pinned = models.BooleanField(default=False, db_index=True)
    locked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-created_at"]
        indexes = [
            models.Index(fields=["flair", "-created_at"]),
            models.Index(fields=["-score"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = (slugify(self.title) + "-" + str(timezone.now().timestamp())[:10])[:280]
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        # Next.js public route (ADR-0005 split). Server-rendered legacy templates removed in DEB-002.
        return f"/community/threads/{self.slug}/"

    @property
    def hot_score(self) -> float:
        """Reddit-style hot ranking: log10(score) / age_hours^0.6."""
        age_h = max(1.0, (timezone.now() - self.created_at).total_seconds() / 3600)
        return math.log10(max(1, abs(self.score) + 1)) / (age_h ** 0.6)


class ForumReply(ModeratableMixin, TimeStampedModel):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="forum_replies")
    body   = models.TextField(max_length=10_000)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                                related_name="children")
    score  = models.IntegerField(default=0)

    class Meta:
        ordering = ["-score", "created_at"]

    def __str__(self) -> str:
        return f"{self.author} on thread {self.thread_id}"


class Vote(models.Model):
    """One vote per (user, target). Generic FK to thread or reply."""
    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id   = models.PositiveBigIntegerField()
    target      = GenericForeignKey("target_type", "target_id")
    voter       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name="votes")
    value       = models.SmallIntegerField()  # -1 or +1
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["target_type", "target_id", "voter"],
                                     name="unique_vote_per_user_target"),
            models.CheckConstraint(condition=models.Q(value__in=[-1, 1]),
                                    name="vote_value_in_range"),
        ]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.voter} voted {self.value} on {self.target_type.model} {self.target_id}"
