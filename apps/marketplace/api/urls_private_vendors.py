"""Private vendor URLs — mounted at /api/v1/vendors/."""
from django.urls import path

from .views import VendorOnboardStepView, VendorProfileMeView

urlpatterns = [
    path("me/", VendorProfileMeView.as_view(), name="vendors-me"),
    path("onboard/<str:step>/", VendorOnboardStepView.as_view(),
         name="vendors-onboard-step"),
]
