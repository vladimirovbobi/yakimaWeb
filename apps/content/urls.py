"""Per-author Atom RSS feed only — kept post-DEB-002 (Next.js owns blog routes)."""
from django.urls import path

from .views_rss import AuthorRSSFeed

app_name = "content"

urlpatterns = [
    path("<slug:slug>/rss/", AuthorRSSFeed(), name="author_rss"),
]
