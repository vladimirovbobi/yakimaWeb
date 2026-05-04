"""Forum API views — public list/detail + private CRUD + voting."""
from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.pagination import TimeCursorPagination
from apps.core.api.permissions import IsOwnerOrReadOnly
from apps.core.api.throttling import ForumWriteThrottle, VoteThrottle
from apps.forum.models import Flair, ForumReply, ForumThread, Vote

from .serializers import (
    FlairSerializer,
    ForumReplyCreateSerializer,
    ForumReplySerializer,
    ForumThreadCreateUpdateSerializer,
    ForumThreadDetailSerializer,
    ForumThreadListSerializer,
    VoteSerializer,
)


# ──────────────────────────────────────────────────────────────────────────
# Public — Index + lists
# ──────────────────────────────────────────────────────────────────────────
class PublicForumIndexView(generics.ListAPIView):
    """GET /api/public/v1/community/ — list of flairs (boards)."""

    serializer_class   = FlairSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class   = None  # short fixed list

    def get_queryset(self):
        return Flair.objects.all().order_by("sort_order", "label")


def _sort_threads(qs, sort: str):
    """new → -created_at; top → -score; hot → Python sort over recent slice."""
    if sort == "top":
        return qs.order_by("-pinned", "-score", "-created_at")
    if sort == "hot":
        items = list(qs.order_by("-pinned", "-created_at")[:200])
        items.sort(key=lambda t: (-int(t.pinned), -t.hot_score))
        return items
    return qs.order_by("-pinned", "-created_at")


class PublicFlairThreadListView(generics.ListAPIView):
    """GET /api/public/v1/community/<flair_slug>/threads/ — sort = new|top|hot."""

    serializer_class   = ForumThreadListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class   = TimeCursorPagination

    def get_queryset(self):
        flair = get_object_or_404(Flair, slug=self.kwargs["flair_slug"])
        qs = (ForumThread.objects
              .filter(flair=flair, moderation_status="approved")
              .select_related("author", "author__realtor_profile", "flair"))
        sort = (self.request.query_params.get("sort") or "new").lower()
        return _sort_threads(qs, sort)


class PublicThreadDetailView(generics.RetrieveAPIView):
    """GET /api/public/v1/community/threads/<slug>/ — detail with body_html."""

    serializer_class   = ForumThreadDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field       = "slug"

    def get_queryset(self):
        return (ForumThread.objects
                .filter(moderation_status="approved")
                .select_related("author", "author__realtor_profile", "flair"))


class PublicThreadRepliesView(generics.ListAPIView):
    """GET /api/public/v1/community/threads/<slug>/replies/ — paginated."""

    serializer_class   = ForumReplySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class   = TimeCursorPagination

    def get_queryset(self):
        thread = get_object_or_404(
            ForumThread, slug=self.kwargs["slug"], moderation_status="approved",
        )
        return (ForumReply.objects
                .filter(thread=thread, moderation_status="approved")
                .select_related("author", "author__realtor_profile", "parent")
                .order_by("created_at"))


# ──────────────────────────────────────────────────────────────────────────
# Private — Threads
# ──────────────────────────────────────────────────────────────────────────
class ThreadCreateView(generics.CreateAPIView):
    """POST /api/v1/community/<flair_slug>/threads/ — moderated on save."""

    serializer_class   = ForumThreadCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes   = [ForumWriteThrottle]

    def perform_create(self, serializer):
        flair = get_object_or_404(Flair, slug=self.kwargs["flair_slug"])
        # Override flair from URL — body's flair value (if sent) is ignored here.
        serializer.save(author=self.request.user, flair=flair)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        out = ForumThreadDetailSerializer(instance, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class ThreadUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/PUT/DELETE /api/v1/community/threads/<slug>/ — owner-only writes."""

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field       = "slug"

    def get_queryset(self):
        return ForumThread.objects.select_related("author", "flair").all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ForumThreadDetailSerializer
        return ForumThreadCreateUpdateSerializer


# ──────────────────────────────────────────────────────────────────────────
# Private — Replies
# ──────────────────────────────────────────────────────────────────────────
class ReplyCreateView(generics.CreateAPIView):
    """POST /api/v1/community/threads/<slug>/replies/ — moderated."""

    serializer_class   = ForumReplyCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes   = [ForumWriteThrottle]

    def get_serializer_context(self):
        ctx    = super().get_serializer_context()
        thread = get_object_or_404(ForumThread, slug=self.kwargs["slug"])
        if thread.locked:
            raise PermissionDenied("Thread is locked.")
        ctx["thread"] = thread
        return ctx

    def perform_create(self, serializer):
        thread = self.get_serializer_context()["thread"]
        serializer.save(author=self.request.user, thread=thread)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        out = ForumReplySerializer(serializer.instance, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)


class ReplyUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/community/replies/<id>/ — owner-only writes."""

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_field       = "pk"

    def get_queryset(self):
        return ForumReply.objects.select_related("author", "parent", "thread").all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ForumReplyCreateSerializer
        return ForumReplySerializer


# ──────────────────────────────────────────────────────────────────────────
# Voting — generic FK on Vote
# ──────────────────────────────────────────────────────────────────────────
_TARGET_TYPE_MAP = {
    "forum_thread": ("forum", "forumthread", ForumThread),
    "forum_reply":  ("forum", "forumreply",  ForumReply),
    # Aliases also accepted for client convenience.
    "thread":       ("forum", "forumthread", ForumThread),
    "reply":        ("forum", "forumreply",  ForumReply),
}


def _resolve_target(target_type: str, item_id: int):
    """Map a target_type string → (ContentType, model instance). Default = thread."""
    key = (target_type or "forum_thread").lower()
    if key not in _TARGET_TYPE_MAP:
        raise ValidationError({"target_type": "Unknown target type."})
    app_label, model_name, model_cls = _TARGET_TYPE_MAP[key]
    ct = ContentType.objects.get(app_label=app_label, model=model_name)
    try:
        target = model_cls.objects.get(pk=item_id)
    except model_cls.DoesNotExist as exc:
        raise NotFound("Vote target not found.") from exc
    return ct, target, model_cls


class VoteView(APIView):
    """POST /api/v1/forum/items/<int:item_id>/vote/ — idempotent vote upsert."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes   = [VoteThrottle]

    def post(self, request, item_id: int):
        serializer = VoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value       = int(serializer.validated_data["value"])
        target_type = (
            serializer.validated_data.get("target_type")
            or request.query_params.get("target_type")
            or "forum_thread"
        )
        ct, target, model_cls = _resolve_target(target_type, item_id)

        with transaction.atomic():
            existing = (Vote.objects
                        .select_for_update()
                        .filter(target_type=ct, target_id=item_id, voter=request.user)
                        .first())
            if value == 0:
                # Clear vote.
                if existing:
                    delta = -existing.value
                    existing.delete()
                    model_cls.objects.filter(pk=item_id).update(score=F("score") + delta)
            elif existing is None:
                Vote.objects.create(
                    target_type=ct, target_id=item_id,
                    voter=request.user, value=value,
                )
                model_cls.objects.filter(pk=item_id).update(score=F("score") + value)
            elif existing.value != value:
                delta = value - existing.value
                existing.value = value
                existing.save(update_fields=["value", "updated_at"])
                model_cls.objects.filter(pk=item_id).update(score=F("score") + delta)
            # else: same value → no-op (idempotent).

            target.refresh_from_db(fields=["score"])
            user_value = 0
            if value != 0:
                user_value = value
            elif existing and existing.pk and existing.value == value:
                user_value = value

        return Response(
            {"score": target.score, "user_vote": user_value},
            status=status.HTTP_200_OK,
        )
