"""Public vendor URLs — mounted at /api/public/v1/vendors/."""
from django.urls import path

from .views import (
    PublicVendorDetailView,
    PublicVendorListView,
    PublicVendorServicesView,
)

urlpatterns = [
    path("", PublicVendorListView.as_view(), name="vendors-list"),
    path("<slug:slug>/", PublicVendorDetailView.as_view(), name="vendors-detail"),
    path("<slug:vendor_slug>/services/", PublicVendorServicesView.as_view(),
         name="vendors-services-list"),
]
