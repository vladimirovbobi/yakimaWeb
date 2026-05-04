"""Lead URLs — mounted at /api/v1/leads/."""
from django.urls import path

from .views import (
    LeadCreateView,
    LeadDetailView,
    LeadMessageListCreateView,
    LeadStatusUpdateView,
    MyLeadListView,
    ReviewCreateView,
    ReviewResponseCreateView,
)

urlpatterns = [
    path("", LeadCreateView.as_view(), name="leads-create"),
    path("me/", MyLeadListView.as_view(), name="leads-mine"),

    # Review response by review id — defined before <int:pk> for clarity.
    path("reviews/<int:pk>/response/", ReviewResponseCreateView.as_view(),
         name="leads-review-response"),

    path("<int:pk>/", LeadDetailView.as_view(), name="leads-detail"),
    path("<int:pk>/status/", LeadStatusUpdateView.as_view(), name="leads-status"),
    path("<int:lead_id>/messages/", LeadMessageListCreateView.as_view(),
         name="leads-messages"),
    path("<int:lead_id>/review/", ReviewCreateView.as_view(), name="leads-review"),
]
