"""Current-user routes — /api/v1/me/."""
from django.urls import path

from .views import (
    MeView,
    MyRealtorProfileView,
    MyToolUsageListView,
    MyVendorProfileView,
)

urlpatterns = [
    path("",            MeView.as_view(),               name="me-detail"),
    path("realtor/",    MyRealtorProfileView.as_view(), name="me-realtor"),
    path("vendor/",     MyVendorProfileView.as_view(),  name="me-vendor"),
    path("tool-usage/", MyToolUsageListView.as_view(),  name="me-tool-usage"),
]
