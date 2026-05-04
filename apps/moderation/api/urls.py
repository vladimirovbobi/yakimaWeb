"""Moderation API URLs — mounted at /api/v1/mod/."""
from __future__ import annotations

from django.urls import path

from .views import (
    ActionTemplateListView,
    DecisionCreateView,
    EscalateView,
    EscalationListView,
    FlagCreateView,
    FlagListView,
    InvestigateUserView,
    ModStatsView,
    NextQueueItemView,
    QueueListView,
)

urlpatterns = [
    path("queue/",                          QueueListView.as_view(),         name="mod-queue-list"),
    path("queue/next/",                     NextQueueItemView.as_view(),     name="mod-queue-next"),
    path("items/<int:id>/decision/",        DecisionCreateView.as_view(),    name="mod-decision-create"),
    path("items/<int:id>/escalate/",        EscalateView.as_view(),          name="mod-escalate"),
    path("flags/",                          FlagListView.as_view(),          name="mod-flag-list"),
    path("flags/create/",                   FlagCreateView.as_view(),        name="mod-flag-create"),
    path("templates/",                      ActionTemplateListView.as_view(), name="mod-template-list"),
    path("investigate/<int:user_id>/",      InvestigateUserView.as_view(),   name="mod-investigate-user"),
    path("stats/",                          ModStatsView.as_view(),          name="mod-stats"),
    path("escalations/",                    EscalationListView.as_view(),    name="mod-escalation-list"),
]
