"""Public tool meta routes — /api/public/v1/tools/."""
from django.urls import path

from .views import ToolMetaDetailView, ToolMetaListView

urlpatterns = [
    path("",              ToolMetaListView.as_view(),   name="tools-meta-list"),
    path("<slug:slug>/",  ToolMetaDetailView.as_view(), name="tools-meta-detail"),
]
