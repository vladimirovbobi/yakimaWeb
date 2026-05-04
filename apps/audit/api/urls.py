"""Audit API URLs — mounted at /api/v1/audit/."""
from __future__ import annotations

from django.urls import path

from .views import AccessLogListView, ActionLogDetailView, ActionLogListView

urlpatterns = [
    path("actions/",            ActionLogListView.as_view(),    name="audit-actions-list"),
    path("actions/<int:id>/",   ActionLogDetailView.as_view(),  name="audit-actions-detail"),
    path("access/",             AccessLogListView.as_view(),    name="audit-access-list"),
]
