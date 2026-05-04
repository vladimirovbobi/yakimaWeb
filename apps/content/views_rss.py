"""Atom feeds for realtor blogs (per-author)."""
from django.contrib.syndication.views import Feed
from django.http import Http404
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed

from .models import Post, PostStatus, PostType
from .services.rss import find_author_by_slug


class AuthorRSSFeed(Feed):
    feed_type = Atom1Feed

    def get_object(self, request, slug):
        author = find_author_by_slug(slug)
        if author is None:
            raise Http404("Author not found")
        return author

    def title(self, author):
        return f"{author.get_full_name()} — Yakima Web Blog"

    def link(self, author):
        return reverse("content:author_rss", kwargs={"slug": _author_slug(author)})

    def description(self, author):
        return f"Latest posts by {author.get_full_name()} on Yakima Web."

    def items(self, author):
        return (
            Post.objects.filter(
                author=author,
                post_type=PostType.BLOG,
                status=PostStatus.PUBLISHED,
                moderation_status="approved",
            )
            .order_by("-published_at", "-created_at")[:25]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or item.body[:300]

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_at or item.created_at

    def item_author_name(self, item):
        return item.author.get_full_name()


def _author_slug(user):
    from .services.rss import author_slug
    return author_slug(user)
