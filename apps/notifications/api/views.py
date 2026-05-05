"""Notification REST endpoints — all scoped to request.user."""
from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.csrf import StrictCSRFMixin
from apps.core.api.pagination import TimeCursorPagination

from ..models import Notification
from ..services import mark_all_read, mark_read, unread_count
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/v1/me/notifications/?unread=1&kind=lead_received."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = TimeCursorPagination

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        params = self.request.query_params
        if params.get("unread") in ("1", "true", "yes"):
            qs = qs.filter(read_at__isnull=True)
        kind = params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        return qs


class NotificationMarkReadView(StrictCSRFMixin, APIView):
    """POST /api/v1/me/notifications/<id>/read/."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk: int, *args, **kwargs):
        n = mark_read(request.user, [pk])
        return Response({"updated": n}, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(StrictCSRFMixin, APIView):
    """POST /api/v1/me/notifications/read-all/."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        n = mark_all_read(request.user)
        return Response({"updated": n}, status=status.HTTP_200_OK)


class NotificationUnreadCountView(APIView):
    """GET /api/v1/me/notifications/unread-count/."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({"count": unread_count(request.user)})
