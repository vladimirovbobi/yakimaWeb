"""Content API views — public list/detail + private CRUD for posts and comments."""
from __future__ import annotations

from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, permissions
from rest_framework.response import Response

from apps.content.models import (
    Comment,
    NewsletterSubscription,
    Post,
    PostStatus,
    PostType,
    SocialEmbed,
)
from apps.core.api.pagination import TimeCursorPagination
from apps.core.api.permissions import IsOwnerOrReadOnly, IsRealtor
from apps.core.api.throttling import CommentThrottle

from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    NewsletterSubscriptionSerializer,
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    SocialEmbedSerializer,
)


# ──────────────────────────────────────────────────────────────────────────
# Public — Posts
# ──────────────────────────────────────────────────────────────────────────
class PublicPostListView(generics.ListAPIView):
    """GET /api/public/v1/posts/ — published + approved only."""

    serializer_class   = PostListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class   = TimeCursorPagination
    filter_backends    = [filters.SearchFilter]
    search_fields      = ["title", "excerpt"]

    def get_queryset(self):
        qs = (Post.objects
              .filter(status=PostStatus.PUBLISHED, moderation_status="approved")
              .select_related("author", "author__realtor_profile"))
        post_type = self.request.query_params.get("post_type") or self.request.query_params.get("type")
        if post_type in PostType.values:
            qs = qs.filter(post_type=post_type)
        return qs.order_by("-published_at", "-created_at")


class PublicPostDetailView(generics.RetrieveAPIView):
    """GET /api/public/v1/posts/<slug>/ — increments view_count atomically."""

    serializer_class   = PostDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = "slug"

    def get_queryset(self):
        return (Post.objects
                .filter(status=PostStatus.PUBLISHED, moderation_status="approved")
                .select_related("author", "author__realtor_profile"))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Post.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.view_count = (instance.view_count or 0) + 1
        return Response(self.get_serializer(instance).data)


# ──────────────────────────────────────────────────────────────────────────
# Public — Comments
# ──────────────────────────────────────────────────────────────────────────
class PublicCommentListView(generics.ListAPIView):
    """GET /api/public/v1/posts/<post_slug>/comments/ — approved only, threaded."""

    serializer_class   = CommentSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class   = TimeCursorPagination

    def get_queryset(self):
        post_slug = self.kwargs["post_slug"]
        post = get_object_or_404(
            Post,
            slug=post_slug,
            status=PostStatus.PUBLISHED,
            moderation_status="approved",
        )
        # Parents first then replies — both ordered by created_at.
        return (Comment.objects
                .filter(post=post, moderation_status="approved")
                .select_related("author", "author__realtor_profile", "parent")
                .order_by("parent_id", "created_at"))


# ──────────────────────────────────────────────────────────────────────────
# Public — Newsletter
# ──────────────────────────────────────────────────────────────────────────
class NewsletterSubscribeView(generics.CreateAPIView):
    """POST /api/public/v1/posts/newsletter/ — double-opt-in pending row."""

    queryset           = NewsletterSubscription.objects.all()
    serializer_class   = NewsletterSubscriptionSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # TODO(phase-7): trigger Celery task to send confirmation email.
        # Idempotent — same email will return existing pending row.
        email = serializer.validated_data["email"]
        sub, _ = NewsletterSubscription.objects.get_or_create(
            email=email,
            defaults={"source": serializer.validated_data.get("source", "")},
        )
        serializer.instance = sub


# ──────────────────────────────────────────────────────────────────────────
# Public — Social embeds
# ──────────────────────────────────────────────────────────────────────────
class SocialEmbedListView(generics.ListAPIView):
    """GET /api/public/v1/posts/social/ — pinned-first social cards."""

    serializer_class   = SocialEmbedSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class   = TimeCursorPagination

    def get_queryset(self):
        qs = SocialEmbed.objects.all()
        provider = self.request.query_params.get("provider")
        kind     = self.request.query_params.get("kind")
        if provider:
            qs = qs.filter(provider=provider)
        if kind:
            qs = qs.filter(kind=kind)
        return qs.order_by("-is_pinned", "-published_at", "sort_order")


# ──────────────────────────────────────────────────────────────────────────
# Private — Posts
# ──────────────────────────────────────────────────────────────────────────
class PostCreateView(generics.CreateAPIView):
    """POST /api/v1/posts/ — verified realtors author blog posts.

    Goes through ModeratableMixin (post_save signal fires moderation task).
    """

    serializer_class   = PostCreateUpdateSerializer
    permission_classes = [IsRealtor]

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            post_type=PostType.BLOG,
            status=PostStatus.DRAFT,
        )


class PostUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/PUT/DELETE /api/v1/posts/<slug>/ — owner-only writes."""

    serializer_class   = PostCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field       = "slug"

    def get_queryset(self):
        return Post.objects.select_related("author").all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PostDetailSerializer
        return PostCreateUpdateSerializer


# ──────────────────────────────────────────────────────────────────────────
# Private — Comments
# ──────────────────────────────────────────────────────────────────────────
class CommentCreateView(generics.CreateAPIView):
    """POST /api/v1/posts/<post_slug>/comments/ — auto-moderated on save."""

    serializer_class   = CommentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes   = [CommentThrottle]

    def get_serializer_context(self):
        ctx  = super().get_serializer_context()
        post = get_object_or_404(Post, slug=self.kwargs["post_slug"])
        ctx["post"] = post
        return ctx

    def perform_create(self, serializer):
        post = self.get_serializer_context()["post"]
        serializer.save(author=self.request.user, post=post)

    def create(self, request, *args, **kwargs):
        # Echo back full read-shape so client can render immediately.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        return Response(
            CommentSerializer(instance, context=self.get_serializer_context()).data,
            status=201,
        )


class CommentUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/posts/comments/<id>/ — owner-only writes."""

    serializer_class   = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field       = "pk"

    def get_queryset(self):
        return Comment.objects.select_related("author", "parent", "post").all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CommentCreateSerializer
        return CommentSerializer
