"""Content API serializers — Post, Comment, Tag, Newsletter, SocialEmbed."""
from __future__ import annotations

from rest_framework import serializers

from apps.accounts.api.serializers import PublicUserSerializer
from apps.content.models import (
    Comment,
    NewsletterSubscription,
    Post,
    PostType,
    SocialEmbed,
    Tag,
)
from apps.content.services.sanitize import render_post_body


# ──────────────────────────────────────────────────────────────────────────
# Tags
# ──────────────────────────────────────────────────────────────────────────
class TagSerializer(serializers.ModelSerializer):
    """Tag with denormalized post_count for tag pages."""

    post_count = serializers.SerializerMethodField()

    class Meta:
        model  = Tag
        fields = ("id", "slug", "name", "post_count")
        read_only_fields = fields

    def get_post_count(self, obj: Tag) -> int:
        # Annotated when available; fall back to query.
        annotated = getattr(obj, "post_count_annotated", None)
        if annotated is not None:
            return int(annotated)
        return obj.posts.filter(
            status="published", moderation_status="approved",
        ).count()


# ──────────────────────────────────────────────────────────────────────────
# Posts
# ──────────────────────────────────────────────────────────────────────────
class PostListSerializer(serializers.ModelSerializer):
    """Card view — list endpoints."""

    author     = PublicUserSerializer(read_only=True)
    hero_image = serializers.ImageField(use_url=True, read_only=True)
    tags       = TagSerializer(many=True, read_only=True)

    class Meta:
        model  = Post
        fields = (
            "id", "slug", "title", "excerpt", "hero_image",
            "post_type", "author", "published_at", "view_count", "tags",
        )
        read_only_fields = fields


class PostDetailSerializer(serializers.ModelSerializer):
    """Detail view — adds rendered body_html + comment_count + tags."""

    author        = PublicUserSerializer(read_only=True)
    hero_image    = serializers.ImageField(use_url=True, read_only=True)
    body_html     = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    tags          = TagSerializer(many=True, read_only=True)

    class Meta:
        model  = Post
        fields = (
            "id", "slug", "title", "excerpt", "hero_image",
            "post_type", "author", "published_at", "view_count",
            "body", "body_html", "comment_count", "tags",
        )
        read_only_fields = fields

    def get_body_html(self, obj: Post) -> str:
        return render_post_body(obj.body or "")

    def get_comment_count(self, obj: Post) -> int:
        return obj.comments.filter(moderation_status="approved").count()


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Create / update — body accepts markdown OR TipTap HTML, sanitized server-side."""

    hero_image = serializers.ImageField(use_url=True, required=False, allow_null=True)
    tag_slugs  = serializers.ListField(
        child=serializers.SlugField(),
        required=False, allow_empty=True, write_only=True,
        help_text="Slugs (existing) or names (auto-slugged on create).",
    )
    tags       = TagSerializer(many=True, read_only=True)

    class Meta:
        model  = Post
        fields = (
            "id", "slug", "title", "excerpt", "body",
            "hero_image", "post_type", "tag_slugs", "tags",
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

    def _sync_tags(self, post: Post, tag_slugs: list[str]) -> None:
        from django.utils.text import slugify
        cleaned: list[Tag] = []
        for raw in tag_slugs[:8]:  # cap at 8 tags per post
            slug = slugify(raw)[:80]
            if not slug:
                continue
            tag, _ = Tag.objects.get_or_create(
                slug=slug, defaults={"name": raw[:80]},
            )
            cleaned.append(tag)
        post.tags.set(cleaned)

    def create(self, validated_data: dict) -> Post:
        tag_slugs = validated_data.pop("tag_slugs", [])
        post = super().create(validated_data)
        if tag_slugs:
            self._sync_tags(post, tag_slugs)
        return post

    def update(self, instance: Post, validated_data: dict) -> Post:
        tag_slugs = validated_data.pop("tag_slugs", None)
        post = super().update(instance, validated_data)
        if tag_slugs is not None:
            self._sync_tags(post, tag_slugs)
        return post


# ──────────────────────────────────────────────────────────────────────────
# Comments
# ──────────────────────────────────────────────────────────────────────────
class CommentSerializer(serializers.ModelSerializer):
    """Read view — body_html rendered, replies fetched separately by client."""

    author    = PublicUserSerializer(read_only=True)
    parent    = serializers.PrimaryKeyRelatedField(read_only=True)
    body_html = serializers.SerializerMethodField()
    image     = serializers.ImageField(use_url=True, read_only=True)

    class Meta:
        model  = Comment
        fields = (
            "id", "body", "body_html", "author", "parent",
            "image", "created_at", "moderation_status",
        )
        read_only_fields = (
            "id", "body_html", "author", "parent",
            "image", "created_at", "moderation_status",
        )

    def get_body_html(self, obj: Comment) -> str:
        return render_post_body(obj.body or "")


class CommentCreateSerializer(serializers.ModelSerializer):
    """Write — body + optional parent + optional image."""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        required=False, allow_null=True,
    )
    image  = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model  = Comment
        fields = ("body", "parent", "image")

    def validate_parent(self, value: Comment | None) -> Comment | None:
        if value is None:
            return None
        post = self.context.get("post")
        if post is None or value.post_id != post.pk:
            raise serializers.ValidationError(
                "Parent comment must belong to the same post."
            )
        return value

    def validate_image(self, value):
        # Hard cap matches MaxFileSizeValidator on the model field but enforce early.
        if value and value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image exceeds 10 MB.")
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
