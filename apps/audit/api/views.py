"""Audit views — read-only ActionLog + AccessLog endpoints.

Permission tiers:
- ActionLog list / AccessLog list : IsOperator (redacted before/after)
- ActionLog detail                : IsAdmin (raw before/after JSON)

Append-only contract: no PATCH/DELETE endpoints exist for these models.
"""
from __future__ import annotations

import django_filters
from rest_framework.generics import ListAPIView, RetrieveAPIView

from apps.core.api.pagination import TimeCursorPagination
from apps.core.api.permissions import IsAdmin, IsOperator

from ..models import AccessLog, ActionLog
from .serializers import (
    AccessLogSerializer,
    ActionLogDetailSerializer,
    ActionLogSerializer,
)

# ─── Filters ─────────────────────────────────────────────────────────────
class _ActionLogFilter(django_filters.FilterSet):
    actor = django_filters.NumberFilter(field_name="actor_id")
    action = django_filters.CharFilter(field_name="action", lookup_expr="icontains")
    target_type = django_filters.CharFilter(method="filter_target_type")
    created_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt")

    def filter_target_type(self, qs, name: str, value: str):  # noqa: ANN001, ARG002
        if "." in value:
            app, model = value.split(".", 1)
            return qs.filter(target_type__app_label=app, target_type__model=model)
        return qs.filter(target_type__model=value)

    class Meta:
        model = ActionLog
        fields = ("actor", "action", "target_type", "created_after", "created_before")


class _AccessLogFilter(django_filters.FilterSet):
    user = django_filters.NumberFilter(field_name="actor_id")
    path = django_filters.CharFilter(field_name="path", lookup_expr="icontains")
    status_code = django_filters.NumberFilter(field_name="status_code")
    surface = django_filters.CharFilter(field_name="surface")
    created_after = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt")

    class Meta:
        model = AccessLog
        fields = ("user", "path", "status_code", "surface",
                  "created_after", "created_before")


# ─── Views ───────────────────────────────────────────────────────────────
class ActionLogListView(ListAPIView):
    """GET /api/v1/audit/actions/ — operator-tier action history."""

    serializer_class = ActionLogSerializer
    permission_classes = (IsOperator,)
    pagination_class = TimeCursorPagination
    filterset_class = _ActionLogFilter

    def get_queryset(self):
        return (ActionLog.objects
                .select_related("actor", "target_type")
                .order_by("-created_at"))


class ActionLogDetailView(RetrieveAPIView):
    """GET /api/v1/audit/actions/<id>/ — raw before/after for admins only."""

    serializer_class = ActionLogDetailSerializer
    permission_classes = (IsAdmin,)
    queryset = ActionLog.objects.select_related("actor", "target_type")
    lookup_url_kwarg = "id"


class AccessLogListView(ListAPIView):
    """GET /api/v1/audit/access/ — staff-surface access trail."""

    serializer_class = AccessLogSerializer
    permission_classes = (IsOperator,)
    pagination_class = TimeCursorPagination
    filterset_class = _AccessLogFilter

    def get_queryset(self):
        return (AccessLog.objects
                .select_related("actor")
                .order_by("-created_at"))
