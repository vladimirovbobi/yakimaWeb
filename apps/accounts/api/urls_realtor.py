"""Realtor private routes — /api/v1/realtor/."""
from django.urls import path

from .views import RealtorProfilePartialUpdateView, RealtorVerifyView

urlpatterns = [
    path("verify/",  RealtorVerifyView.as_view(),                name="realtor-verify"),
    path("profile/", RealtorProfilePartialUpdateView.as_view(),  name="realtor-profile"),
]
