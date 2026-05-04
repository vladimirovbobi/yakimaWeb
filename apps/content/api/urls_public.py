"""Public content URLs — under /api/public/v1/posts/."""
from django.urls import path

from .views import (
    NewsletterSubscribeView,
    PublicCommentListView,
    PublicPostDetailView,
    PublicPostListView,
    PublicTagDetailView,
    PublicTagListView,
    SocialEmbedListView,
)

urlpatterns = [
    path("",                              PublicPostListView.as_view(),    name="posts-list"),
    path("newsletter/",                   NewsletterSubscribeView.as_view(), name="posts-newsletter"),
    path("social/",                       SocialEmbedListView.as_view(),   name="posts-social"),
    path("tags/",                         PublicTagListView.as_view(),     name="posts-tags-list"),
    path("tags/<slug:slug>/",             PublicTagDetailView.as_view(),   name="posts-tag-detail"),
    path("<slug:slug>/",                  PublicPostDetailView.as_view(),  name="posts-detail"),
    path("<slug:post_slug>/comments/",    PublicCommentListView.as_view(), name="posts-comments-list"),
]
