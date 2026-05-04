"""Django-side views for the delivery surface — webhook receiver + read API.

Most write paths run on the FastAPI delivery service (see /delivery). The
Django side handles:

  - The signed webhook back from the delivery service when a package is
    finalized; this is what flips Lead.status to 'won'.
  - Read-only endpoints the buyer dashboard uses to show "this lead has
    deliveries" without going through the delivery service for every page
    render.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.marketplace.models import Lead, LeadStatus

from ..models import DeliveryPackage

log = logging.getLogger(__name__)


class FinalizeWebhookView(APIView):
    """The delivery service posts here on finalize. Flip the Lead to 'won'."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, *args, **kwargs):
        secret = getattr(settings, "DELIVERY_WEBHOOK_SECRET", "")
        signature = request.headers.get("X-Webhook-Signature", "")
        body = request.body or b""
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        # Allow trusted dev requests when no secret configured.
        if secret and not hmac.compare_digest(expected, signature):
            raise PermissionDenied("invalid_signature")

        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            return Response({"detail": "invalid_json"}, status=status.HTTP_400_BAD_REQUEST)

        package_id = payload.get("package_id")
        lead_id    = payload.get("lead_id")
        if not package_id or not lead_id:
            return Response({"detail": "missing_fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Idempotent: re-firing the webhook just no-ops.
        pkg = DeliveryPackage.objects.filter(pk=package_id).first()
        if pkg is None:
            return Response({"detail": "package_not_found"}, status=status.HTTP_404_NOT_FOUND)

        lead = Lead.objects.filter(pk=lead_id).first()
        if lead is None:
            return Response({"detail": "lead_not_found"}, status=status.HTTP_404_NOT_FOUND)

        if lead.status != LeadStatus.WON:
            lead.status = LeadStatus.WON
            lead.won_at = lead.won_at or timezone.now()
            lead.save(update_fields=["status", "won_at", "updated_at"])

        log.info("delivery webhook: pkg=%s lead=%s flipped to WON", package_id, lead_id)
        return Response({"status": "ok", "lead_status": lead.status})


class MyDeliveriesView(generics.ListAPIView):
    """GET /api/v1/me/deliveries/ — lists the buyer's finalized packages."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        packages = (
            DeliveryPackage.objects
            .filter(buyer=request.user, status="finalized")
            .select_related("lead", "vendor")
            .order_by("-finalized_at")[:100]
        )
        return Response({
            "results": [
                {
                    "id":            p.pk,
                    "name":          p.name,
                    "lead_id":       p.lead_id,
                    "vendor_id":     p.vendor_id,
                    "vendor_name":   (getattr(p.vendor, "full_name", "")
                                       or getattr(p.vendor, "email", "")),
                    "finalized_at":  p.finalized_at.isoformat() if p.finalized_at else None,
                    "file_count":    p.files.count(),
                }
                for p in packages
            ],
        })
