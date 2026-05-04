"""Private forum URLs — under /api/v1/community/."""
from django.urls import path

from .views import (
    ReplyCreateView,
    ReplyUpdateDestroyView,
    ThreadCreateView,
    ThreadUpdateDestroyView,
)

urlpatterns = [
    path("replies/<int:pk>/",                  ReplyUpdateDestroyView.as_view(),  name="community-reply-detail"),
    path("threads/<slug:slug>/",               ThreadUpdateDestroyView.as_view(), name="community-thread-mine"),
    path("threads/<slug:slug>/replies/",       ReplyCreateView.as_view(),         name="community-reply-create"),
    path("<slug:flair_slug>/threads/",         ThreadCreateView.as_view(),        name="community-thread-create"),
]
