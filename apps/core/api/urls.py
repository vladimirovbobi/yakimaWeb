"""Core meta endpoints — mounted at /api/public/v1/meta/."""
from __future__ import annotations

from django.urls import path

from .views import HealthzView, SiteMetaView

urlpatterns = [
    path("",         SiteMetaView.as_view(),  name="meta"),
    path("healthz/", HealthzView.as_view(),   name="meta-healthz"),
]
