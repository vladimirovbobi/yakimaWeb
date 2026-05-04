"""Operations API URLs — mounted at /api/v1/ops/."""
from __future__ import annotations

from django.urls import path

from .views import (
    ContentTakedownView,
    DashboardView,
    LicenseOverrideView,
    MetricCardView,
    UserSuspendView,
    VendorStatusUpdateView,
)

urlpatterns = [
    path("dashboard/",                        DashboardView.as_view(),          name="ops-dashboard"),
    path("metrics/<str:card_slug>/",          MetricCardView.as_view(),         name="ops-metric-card"),
    path("users/<int:user_id>/suspend/",      UserSuspendView.as_view(),        name="ops-user-suspend"),
    path("vendors/<int:vendor_id>/",          VendorStatusUpdateView.as_view(), name="ops-vendor-status"),
    path("licenses/<int:profile_id>/override/", LicenseOverrideView.as_view(),  name="ops-license-override"),
    path("content/takedown/",                 ContentTakedownView.as_view(),    name="ops-content-takedown"),
]
