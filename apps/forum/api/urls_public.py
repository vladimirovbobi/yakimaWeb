"""Public forum URLs — under /api/public/v1/community/."""
from django.urls import path

from .views import (
    PublicAllThreadsListView,
    PublicFlairThreadListView,
    PublicForumIndexView,
    PublicThreadDetailView,
    PublicThreadRepliesView,
)

urlpatterns = [
    path("",                                       PublicForumIndexView.as_view(),     name="community-index"),
    path("threads/",                               PublicAllThreadsListView.as_view(),  name="community-thread-list"),
    path("threads/<slug:slug>/",                   PublicThreadDetailView.as_view(),   name="community-thread-detail"),
    path("threads/<slug:slug>/replies/",           PublicThreadRepliesView.as_view(),  name="community-thread-replies"),
    path("<slug:flair_slug>/threads/",             PublicFlairThreadListView.as_view(), name="community-flair-threads"),
]
