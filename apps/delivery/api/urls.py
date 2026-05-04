"""URL routes — /api/v1/delivery/ namespace, plus /api/v1/me/deliveries/."""
from django.urls import path

from .views import FinalizeWebhookView, MyDeliveriesView

urlpatterns = [
    path("webhooks/finalize/", FinalizeWebhookView.as_view(), name="delivery-webhook-finalize"),
    path("my/",                MyDeliveriesView.as_view(),    name="delivery-my-list"),
]
