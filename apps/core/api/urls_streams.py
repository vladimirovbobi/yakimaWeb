"""SSE stream URLs — mounted at /api/v1/streams/.

Wires real-time feeds for lead messages and the moderation queue. Each
backend view enforces its own permissions and a hard 5-minute timeout.
"""
from __future__ import annotations

from django.urls import path

from apps.marketplace.api.views import LeadMessageStreamView
from apps.moderation.api.views import ModQueueStreamView

urlpatterns = [
    path("leads/<int:lead_id>/messages/",
         LeadMessageStreamView.as_view(), name="streams-lead-messages"),
    path("mod-queue/",
         ModQueueStreamView.as_view(), name="streams-mod-queue"),
]
