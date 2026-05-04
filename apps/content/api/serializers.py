"""Content API serializers — Post, Comment, Newsletter, SocialEmbed."""
from __future__ import annotations

from rest_framework import serializers

from apps.accounts.api.serializers import PublicUserSerializer
from apps.content.models import (
    Comment,
    NewsletterSubscription,
    Post,
    PostType,
    SocialEmbed,
)
from apps.content.services.sanitize import render_markdown


# ──────────────────────────────────────────────────────────────────────────
# Posts
# ──────────────────────────────────────────────────────────────────────────
class PostListSerializer(serializers.ModelSerializer):
    """Card view — list endpoints."""

    author     = PublicUserSerializer(read_only=True)
    hero_image = serializers.ImageField(use_url=True, read_only=True)

    class Meta:
        model  = Post
        fields = (
            "id", "slug", "title", "excerpt", "hero_image",
            "post_type", "author", "published_at", "view_count",
        )
        read_only_fields = fields


class PostDetailSerializer(serializers.ModelSerializer):
    """Detail view — adds rendered body_html + comment_count."""

    author        = PublicUserSerializer(read_only=True)
    hero_image    = serializers.ImageField(use_url=True, read_only=True)
    body_html     = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model  = Post
        fields = (
            "id", "slug", "title", "excerpt", "hero_image",
            "post_type", "author", "published_at", "view_count",
            "body", "body_html", "comment_count",
        )
        read_only_fields = fields

    def get_body_html(self, obj: Post) -> str:
        return render_markdown(obj.body or "")

    def get_comment_count(self, obj: Post) -> int:
        return obj.comments.filter(moderation_status="approved").count()


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Create / update — markdown body, server-side post_type lock for non-staff."""

    hero_image = serializers.ImageField(use_url=True, required=False, allow_null=True)

    class Meta:
        model  = Post
        fields = (
            "id", "slug", "title", "excerpt", "body",
            "hero_image", "post_type",
        )
        read_only_fields = ("id", "slug")

    def validate_post_type(self, value: str) -> str:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_staff:
            return value
        if value != PostType.BLOG:
            raise serializers.ValidationError("Only blog posts may be authored here.")
        return value

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        user    = getattr(request, "user", None)
        post_type = attrs.get("post_type") or (
            self.instance.post_type if self.instance else PostType.BLOG
        )
        if post_type == PostType.BLOG and user and not user.is_staff:
            if not getattr(user, "is_realtor", False):
                raise serializers.ValidationError(
                    "Only verified realtors may author blog posts."
                )
            prof = getattr(user, "realtor_profile", None)
            if not (prof and prof.verification_status == "verified"):
                raise serializers.ValidationError(
                    "Realtor verification required."
                )
        return attrs


# ──────────────────────────────────────────────────────────────────────────
# Comments
# ──────────────────────────────────────────────────────────────────────────
class CommentSerializer(serializers.ModelSerializer):
    """Read view — body_html rendered, replies fetched separately by client."""

    author    = PublicUserSerializer(read_only=True)
    parent    = serializers.PrimaryKeyRelatedField(read_only=True)
    body_html = serializers.SerializerMethodField()

    class Meta:
        model  = Comment
        fields = (
            "id", "body", "body_html", "author", "parent",
            "created_at", "moderation_status",
        )
        read_only_fields = (
            "id", "body_html", "author", "parent",
            "created_at", "moderation_status",
        )

    def get_body_html(self, obj: Comment) -> str:
        return render_markdown(obj.body or "")


class CommentCreateSerializer(serializers.ModelSerializer):
    """Write — body + optional parent. Parent must be on the same post."""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        required=False, allow_null=True,
    )

    class Meta:
        model  = Comment
        fields = ("body", "parent")

    def validate_parent(self, value: Comment | None) -> Comment | None:
        if value is None:
            return None
        post = self.context.get("post")
        if post is None or value.post_id != post.pk:
            raise serializers.ValidationError(
                "Parent comment must belong to the same post."
            )
        return value


# ──────────────────────────────────────────────────────────────────────────
# Newsletter
# ──────────────────────────────────────────────────────────────────────────
class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    """Email-only — double-opt-in flow handled by view + signal."""

    class Meta:
        model  = NewsletterSubscription
        fields = ("id", "email", "source", "confirmed", "created_at")
        read_only_fields = ("id", "confirmed", "created_at")

    def validate_email(self, value: str) -> str:
        return (value or "").strip().lower()


# ──────────────────────────────────────────────────────────────────────────
# Social embeds
# ──────────────────────────────────────────────────────────────────────────
class SocialEmbedSerializer(serializers.ModelSerializer):
    """Read-only public surface. embed_html sanitized server-side at refresh."""

    class Meta:
        model  = SocialEmbed
        fields = (
            "id", "provider", "kind", "external_id",
            "title", "description", "thumb_url", "canonical_url",
            "embed_html", "published_at", "is_pinned",
        )
        read_only_fields = fields
