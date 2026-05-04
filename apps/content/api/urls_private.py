"""Private content URLs — under /api/v1/posts/."""
from django.urls import path

from .views import (
    CommentCreateView,
    CommentUpdateDestroyView,
    PostCreateView,
    PostUpdateDestroyView,
)

urlpatterns = [
    path("",                                PostCreateView.as_view(),           name="posts-create"),
    path("comments/<int:pk>/",              CommentUpdateDestroyView.as_view(), name="posts-comment-detail"),
    path("<slug:slug>/",                    PostUpdateDestroyView.as_view(),    name="posts-mine-detail"),
    path("<slug:post_slug>/comments/",      CommentCreateView.as_view(),        name="posts-comment-create"),
]
