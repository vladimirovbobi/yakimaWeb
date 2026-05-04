"""Public realtor routes — /api/public/v1/realtors/."""
from django.urls import path

from .views import PublicRealtorDetailView, PublicRealtorListView

urlpatterns = [
    path("",                        PublicRealtorListView.as_view(),
         name="public-realtor-list"),
    path("<int:user_id>/",          PublicRealtorDetailView.as_view(),
         name="public-realtor-detail"),
]
