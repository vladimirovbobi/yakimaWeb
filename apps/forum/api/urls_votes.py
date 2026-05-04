"""Forum vote URL — under /api/v1/forum/."""
from django.urls import path

from .views import VoteView

urlpatterns = [
    path("items/<int:item_id>/vote/", VoteView.as_view(), name="forum-vote"),
]
