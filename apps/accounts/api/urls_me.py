"""Current-user routes — /api/v1/me/."""
from django.urls import include, path

from .views import (
    MeView,
    MyActivityView,
    MyRealtorProfileView,
    MyToolUsageListView,
    MyVendorProfileView,
)

urlpatterns = [
    path("",               MeView.as_view(),               name="me-detail"),
    path("activity/",      MyActivityView.as_view(),       name="me-activity"),
    path("realtor/",       MyRealtorProfileView.as_view(), name="me-realtor"),
    path("vendor/",        MyVendorProfileView.as_view(),  name="me-vendor"),
    path("tool-usage/",    MyToolUsageListView.as_view(),  name="me-tool-usage"),
    path("notifications/", include("apps.notifications.api.urls")),
]
