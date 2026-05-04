"""Sitemap generators."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["core:home", "core:about", "core:guidelines",
                "core:privacy", "core:terms",
                "content:post_list", "content:videos",
                "tools:index",
                "forum:thread_list",
                "marketplace:service_list"]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        from apps.content.models import Post, PostStatus
        return Post.objects.filter(status=PostStatus.PUBLISHED, moderation_status="approved")

    def lastmod(self, obj):
        return obj.updated_at


class ServiceSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        from apps.marketplace.models import Service
        return Service.objects.filter(is_active=True, moderation_status="approved")

    def lastmod(self, obj):
        return obj.updated_at


class ForumSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        from apps.forum.models import ForumThread
        return ForumThread.objects.filter(moderation_status="approved")[:1000]

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "static":      StaticSitemap,
    "posts":       PostSitemap,
    "services":    ServiceSitemap,
    "forum":       ForumSitemap,
}
