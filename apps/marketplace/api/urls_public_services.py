"""Public service URLs — mounted at /api/public/v1/services/."""
from django.urls import path

from .views import (
    CategoryListView,
    PublicPackageListView,
    PublicServiceDetailView,
    PublicServiceListView,
)
from .views_featured import FeaturedServicesView

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="services-categories"),
    path("featured/",   FeaturedServicesView.as_view(), name="services-featured"),
    path("", PublicServiceListView.as_view(), name="services-list"),
    path("<slug:slug>/", PublicServiceDetailView.as_view(), name="services-detail"),
    path("<slug:service_slug>/packages/", PublicPackageListView.as_view(),
         name="services-packages-list"),
]
