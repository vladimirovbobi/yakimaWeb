"""Sitemap generators.

Server-side sitemap remains because /sitemap.xml is a Caddy-routed Django endpoint.
Frontend Next.js publishes its own at /sitemap.ts (preferred); this one stays as a
canonical fallback for crawlers that hit the API host directly. URL paths are literal
Next.js routes (ADR-0005 split — no Django template routes remain post DEB-002).
"""
from django.contrib.sitemaps import Sitemap


# Static frontend routes; literal paths to avoid coupling to Django URL conf.
_STATIC_PATHS: tuple[tuple[str, str, float], ...] = (
    ("/",            "daily",   1.0),
    ("/about",       "monthly", 0.6),
    ("/blog",        "daily",   0.9),
    ("/community",   "hourly",  0.9),
    ("/services",    "daily",   0.85),
    ("/tools",       "weekly",  0.7),
    ("/videos",      "weekly",  0.5),
    ("/guidelines",  "monthly", 0.4),
    ("/privacy",     "yearly",  0.3),
    ("/terms",       "yearly",  0.3),
)


class StaticSitemap(Sitemap):
    def items(self):
        return list(_STATIC_PATHS)

    def location(self, item):
        return item[0]

    def changefreq(self, item):
        return item[1]

    def priority(self, item):
        return item[2]


class PostSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        from apps.content.models import Post, PostStatus
        return Post.objects.filter(status=PostStatus.PUBLISHED, moderation_status="approved")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/blog/{obj.slug}/"


class ServiceSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        from apps.marketplace.models import Service
        return Service.objects.filter(is_active=True, moderation_status="approved")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/services/{obj.slug}/"


class ForumSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        from apps.forum.models import ForumThread
        return ForumThread.objects.filter(moderation_status="approved")[:1000]

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/community/threads/{obj.slug}/"


SITEMAPS = {
    "static":      StaticSitemap,
    "posts":       PostSitemap,
    "services":    ServiceSitemap,
    "forum":       ForumSitemap,
}
