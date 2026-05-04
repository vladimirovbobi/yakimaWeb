"""Polymorphic Post (org/blog/landing) + threaded Comment. All UGC moderated."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.moderation.models import ModeratableMixin


class PostType(models.TextChoices):
    ORG     = "org",     _("Yakima Web (org-authored)")
    BLOG    = "blog",    _("Realtor blog")
    LANDING = "landing", _("Lead-magnet landing")


class PostStatus(models.TextChoices):
    DRAFT     = "draft",     _("Draft")
    PUBLISHED = "published", _("Published")
    ARCHIVED  = "archived",  _("Archived")


class Post(ModeratableMixin, TimeStampedModel):
    """Polymorphic post — org content, realtor blog, lead-magnet landing pages."""

    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name="posts")
    post_type  = models.CharField(max_length=10, choices=PostType.choices,
                                  default=PostType.BLOG, db_index=True)
    status     = models.CharField(max_length=10, choices=PostStatus.choices,
                                  default=PostStatus.DRAFT, db_index=True)
    title      = models.CharField(max_length=200)
    slug       = models.SlugField(max_length=240, unique=True, blank=True)
    excerpt    = models.CharField(max_length=300, blank=True,
                                  help_text="Shown on cards + meta description.")
    body       = models.TextField(help_text="Markdown — will be sanitized.")
    hero_image = models.ImageField(upload_to="content/hero/", null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    view_count = models.PositiveBigIntegerField(default=0)

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["post_type", "status", "-published_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:240]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("content:post_detail", kwargs={"slug": self.slug})

    @property
    def is_visible(self) -> bool:
        return (
            self.status == PostStatus.PUBLISHED
            and self.moderation_status == "approved"
        )


class Comment(ModeratableMixin, TimeStampedModel):
    """Threaded comment (1 level deep). Moderated like everything else."""

    post   = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="comments")
    body   = models.TextField(max_length=4000)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                                related_name="replies")

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "moderation_status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.author} on {self.post_id}"


class NewsletterSubscription(TimeStampedModel):
    """Email-only subscription — Phase 7 wires real sends."""
    email      = models.EmailField(unique=True)
    confirmed  = models.BooleanField(default=False)
    source     = models.CharField(max_length=64, blank=True)  # which page they signed up from

    class Meta:
        verbose_name = "Newsletter subscription"

    def __str__(self) -> str:
        return self.email


class SocialProvider(models.TextChoices):
    YOUTUBE   = "youtube",   _("YouTube")
    INSTAGRAM = "instagram", _("Instagram")
    TIKTOK    = "tiktok",    _("TikTok")


class SocialKind(models.TextChoices):
    VIDEO = "video", _("Video")
    SHORT = "short", _("Short / Reel")
    POST  = "post",  _("Post")


class SocialEmbed(TimeStampedModel):
    """A pinned/featured social post or video — surfaced on the platform.

    No 3rd-party JS SDKs. Server-resolves metadata via oEmbed; client renders
    a plain iframe with privacy-enhanced source.
    """
    provider     = models.CharField(max_length=12, choices=SocialProvider.choices, db_index=True)
    kind         = models.CharField(max_length=8, choices=SocialKind.choices)
    external_id  = models.CharField(max_length=64,
                                     help_text="YouTube video ID, IG post shortcode, etc.")
    title        = models.CharField(max_length=200, blank=True)
    description  = models.CharField(max_length=400, blank=True)
    thumb_url    = models.URLField(blank=True)
    canonical_url = models.URLField()
    embed_html   = models.TextField(blank=True,
                                     help_text="Cached safe iframe HTML (refreshed by beat task).")
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    sort_order   = models.PositiveSmallIntegerField(default=0)
    is_pinned    = models.BooleanField(default=False, db_index=True)
    last_refreshed = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Social embed"
        ordering = ["-is_pinned", "-published_at", "sort_order"]
        constraints = [
            models.UniqueConstraint(fields=["provider", "external_id"],
                                     name="unique_social_embed"),
        ]

    def __str__(self) -> str:
        return f"{self.get_provider_display()}: {self.title or self.external_id}"
