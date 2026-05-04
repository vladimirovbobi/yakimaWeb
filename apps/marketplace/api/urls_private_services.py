"""Private vendor service URLs — mounted at /api/v1/services/."""
from django.urls import path

from .views import (
    BundleListCreateView,
    BundleUpdateDestroyView,
    PackageListCreateView,
    PackageUpdateDestroyView,
    ServiceCreateView,
    ServiceUpdateDestroyView,
)

urlpatterns = [
    # Bundles must come before <slug:slug> to avoid collision.
    path("bundles/", BundleListCreateView.as_view(), name="services-bundles-list"),
    path("bundles/<slug:slug>/", BundleUpdateDestroyView.as_view(),
         name="services-bundles-detail"),

    # Packages — by id (collision-free under /packages/).
    path("packages/<int:pk>/", PackageUpdateDestroyView.as_view(),
         name="services-packages-detail"),

    # Service create + per-service routes.
    path("", ServiceCreateView.as_view(), name="services-create"),
    path("<slug:slug>/", ServiceUpdateDestroyView.as_view(), name="services-detail-private"),
    path("<slug:service_slug>/packages/", PackageListCreateView.as_view(),
         name="services-packages-list-private"),
]
