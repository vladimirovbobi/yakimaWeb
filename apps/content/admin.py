"""Locked-down content admin."""
from django.contrib import admin

from .models import Comment, NewsletterSubscription, Post, SocialEmbed, Tag
from .services.social import resolve


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display  = ("slug", "name", "created_at")
    search_fields = ("slug", "name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display  = ("title", "post_type", "status", "moderation_status",
                     "author", "published_at", "view_count")
    list_filter   = ("post_type", "status", "moderation_status")
    search_fields = ("title", "slug", "author__email")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "view_count",
                        "moderation_status", "moderation_score", "moderated_at")
    autocomplete_fields = ("author",)
    date_hierarchy = "published_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ("__str__", "moderation_status", "created_at")
    list_filter   = ("moderation_status",)
    search_fields = ("body", "author__email")
    readonly_fields = ("post", "author", "parent", "created_at", "updated_at",
                        "moderation_status", "moderation_score", "moderated_at")
    autocomplete_fields = ("author",)


@admin.register(NewsletterSubscription)
class NewsletterAdmin(admin.ModelAdmin):
    list_display  = ("email", "confirmed", "source", "created_at")
    list_filter   = ("confirmed", "source")
    search_fields = ("email",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(SocialEmbed)
class SocialEmbedAdmin(admin.ModelAdmin):
    list_display  = ("title", "provider", "kind", "is_pinned", "published_at")
    list_filter   = ("provider", "kind", "is_pinned")
    search_fields = ("title", "external_id", "canonical_url")
    readonly_fields = ("embed_html", "thumb_url", "last_refreshed",
                        "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        # Auto-resolve embed metadata from canonical_url
        if obj.canonical_url and not obj.external_id:
            r = resolve(obj.canonical_url)
            if r:
                obj.provider = r.provider
                obj.kind = r.kind
                obj.external_id = r.external_id
                obj.embed_html = r.embed_html
                obj.thumb_url = r.thumb_url
                obj.canonical_url = r.canonical_url
        super().save_model(request, obj, form, change)
