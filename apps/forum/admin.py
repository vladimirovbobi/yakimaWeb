"""Forum admin."""
from django.contrib import admin

from .models import Flair, ForumReply, ForumThread, Vote


@admin.register(Flair)
class FlairAdmin(admin.ModelAdmin):
    list_display  = ("label", "slug", "color", "sort_order")
    prepopulated_fields = {"slug": ("label",)}


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display  = ("title", "author", "flair", "score", "reply_count",
                     "moderation_status", "pinned", "locked", "created_at")
    list_filter   = ("flair", "moderation_status", "pinned", "locked")
    search_fields = ("title", "body", "author__email")
    readonly_fields = ("score", "reply_count", "moderation_status",
                        "moderation_score", "moderated_at", "created_at", "updated_at")
    autocomplete_fields = ("author",)


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display  = ("__str__", "score", "moderation_status", "created_at")
    list_filter   = ("moderation_status",)
    search_fields = ("body", "author__email")
    readonly_fields = ("thread", "author", "parent", "score",
                        "moderation_status", "moderation_score", "moderated_at",
                        "created_at", "updated_at")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "voter", "target_type", "target_id", "value")
    list_filter   = ("value",)
    search_fields = ("voter__email",)
    readonly_fields = tuple(f.name for f in Vote._meta.fields)
