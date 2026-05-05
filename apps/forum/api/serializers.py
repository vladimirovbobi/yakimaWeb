"""Forum API serializers — Flair, ForumThread, ForumReply, Vote."""
from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.accounts.api.serializers import PublicUserSerializer
from apps.content.services.sanitize import render_markdown
from apps.forum.models import Flair, ForumReply, ForumThread, Vote


# ──────────────────────────────────────────────────────────────────────────
# Flair
# ──────────────────────────────────────────────────────────────────────────
class FlairSerializer(serializers.ModelSerializer):
    """Tag categories — fixed list."""

    class Meta:
        model  = Flair
        fields = ("id", "slug", "label", "color", "sort_order")
        read_only_fields = fields


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _viewer_vote(viewer, target) -> int:
    """0 if no viewer / no vote, else -1 or 1."""
    if not viewer or not getattr(viewer, "is_authenticated", False):
        return 0
    ct = ContentType.objects.get_for_model(target.__class__)
    vote = Vote.objects.filter(
        target_type=ct, target_id=target.pk, voter=viewer,
    ).only("value").first()
    return vote.value if vote else 0


# ──────────────────────────────────────────────────────────────────────────
# Threads
# ──────────────────────────────────────────────────────────────────────────
class ForumThreadListSerializer(serializers.ModelSerializer):
    """Card view — flair nested, score + reply_count denormalized."""

    author = PublicUserSerializer(read_only=True)
    flair  = FlairSerializer(read_only=True)
    last_activity_at = serializers.SerializerMethodField()
    # Alias for frontend consumers expecting `vote_score`.
    vote_score = serializers.IntegerField(source="score", read_only=True)

    class Meta:
        model  = ForumThread
        fields = (
            "id", "slug", "title", "author", "flair",
            "score", "vote_score", "reply_count", "pinned", "locked",
            "created_at", "last_activity_at",
        )
        read_only_fields = fields

    def get_last_activity_at(self, obj: ForumThread):
        # Model has no last_activity_at column — fall back to created_at.
        return obj.created_at


class ForumThreadDetailSerializer(serializers.ModelSerializer):
    """Detail view — adds body_html + viewer_vote."""

    author       = PublicUserSerializer(read_only=True)
    flair        = FlairSerializer(read_only=True)
    body_html    = serializers.SerializerMethodField()
    viewer_vote  = serializers.SerializerMethodField()
    user_vote    = serializers.SerializerMethodField()
    vote_score   = serializers.IntegerField(source="score", read_only=True)

    class Meta:
        model  = ForumThread
        fields = (
            "id", "slug", "title", "author", "flair",
            "body", "body_html", "score", "vote_score", "reply_count",
            "pinned", "locked", "viewer_vote", "user_vote", "created_at",
        )
        read_only_fields = fields

    def get_user_vote(self, obj: ForumThread) -> int:
        request = self.context.get("request")
        return _viewer_vote(getattr(request, "user", None), obj)

    def get_body_html(self, obj: ForumThread) -> str:
        return render_markdown(obj.body or "")

    def get_viewer_vote(self, obj: ForumThread) -> int:
        request = self.context.get("request")
        return _viewer_vote(getattr(request, "user", None), obj)


class ForumThreadCreateUpdateSerializer(serializers.ModelSerializer):
    """Create / update — flair by slug."""

    flair = serializers.SlugRelatedField(slug_field="slug", queryset=Flair.objects.all())

    class Meta:
        model  = ForumThread
        fields = ("id", "title", "body", "flair", "slug")
        read_only_fields = ("id", "slug")


# ──────────────────────────────────────────────────────────────────────────
# Replies
# ──────────────────────────────────────────────────────────────────────────
class ForumReplySerializer(serializers.ModelSerializer):
    """Read shape — body_html + viewer_vote."""

    author      = PublicUserSerializer(read_only=True)
    parent      = serializers.PrimaryKeyRelatedField(read_only=True)
    body_html   = serializers.SerializerMethodField()
    viewer_vote = serializers.SerializerMethodField()
    user_vote   = serializers.SerializerMethodField()
    vote_score  = serializers.IntegerField(source="score", read_only=True)

    class Meta:
        model  = ForumReply
        fields = (
            "id", "body", "body_html", "author", "parent",
            "score", "vote_score", "viewer_vote", "user_vote", "created_at",
        )
        read_only_fields = fields

    def get_user_vote(self, obj: ForumReply) -> int:
        request = self.context.get("request")
        return _viewer_vote(getattr(request, "user", None), obj)

    def get_body_html(self, obj: ForumReply) -> str:
        return render_markdown(obj.body or "")

    def get_viewer_vote(self, obj: ForumReply) -> int:
        request = self.context.get("request")
        return _viewer_vote(getattr(request, "user", None), obj)


class ForumReplyCreateSerializer(serializers.ModelSerializer):
    """Create — body + optional parent (must be on same thread)."""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=ForumReply.objects.all(),
        required=False, allow_null=True,
    )

    class Meta:
        model  = ForumReply
        fields = ("body", "parent")

    def validate_parent(self, value: ForumReply | None) -> ForumReply | None:
        if value is None:
            return None
        thread = self.context.get("thread")
        if thread is None or value.thread_id != thread.pk:
            raise serializers.ValidationError(
                "Parent reply must belong to the same thread."
            )
        return value


# ──────────────────────────────────────────────────────────────────────────
# Votes
# ──────────────────────────────────────────────────────────────────────────
class VoteSerializer(serializers.Serializer):
    """value ∈ {-1, 0, 1}. 0 clears."""

    value = serializers.IntegerField(min_value=-1, max_value=1)
    target_type = serializers.ChoiceField(
        choices=[("forum_thread", "Forum thread"), ("forum_reply", "Forum reply")],
        required=False,
    )
