"""Moderation REST views — queue, decisions, flags, investigation.

Permissions:
- Queue / decisions / flag list / templates / investigate: IsModerator
- Flag create: IsAuthenticated (any signed-in user can flag)

Safety:
- ModerationDecision rows are append-only (we only POST new rows; never UPDATE/DELETE).
- Layer-2 free-text reason is redacted in QueueItemSerializer.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import django_filters
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.models import AccessLog, ActionLog, Surface
from apps.core.api.pagination import TimeCursorPagination
from apps.core.api.permissions import IsModerator
from apps.core.api.throttling import FlagThrottle

from ..models import (
    Flag,
    FlagStatus,
    ModerationAction,
    ModerationDecision,
    ModerationLayer,
    ModerationStatus,
)
from .serializers import (
    ActionTemplateSerializer,
    DecisionCreateSerializer,
    EscalateSerializer,
    FlagCreateSerializer,
    FlagSerializer,
    InvestigateUserResultSerializer,
    ModerationDecisionSerializer,
    QueueItemSerializer,
)

log = logging.getLogger(__name__)
User = get_user_model()

# ─── Hardcoded action templates (move to model in v1.1) ──────────────────
_ACTION_TEMPLATES: list[dict[str, str]] = [
    {"slug": "removed_spam", "label": "Removed — Spam",
     "action": "remove", "default_reason": "Removed: spam / promotional."},
    {"slug": "removed_harassment", "label": "Removed — Harassment",
     "action": "remove", "default_reason": "Removed: harassment / personal attack."},
    {"slug": "removed_off_topic", "label": "Removed — Off-topic",
     "action": "remove", "default_reason": "Removed: off-topic for this surface."},
    {"slug": "approved_with_edit", "label": "Approved — With edit",
     "action": "approve", "default_reason": "Approved after edit by moderator."},
    {"slug": "approved_no_change", "label": "Approved — No change",
     "action": "approve", "default_reason": "Approved as-is; classifier flagged borderline content."},
]


# ─── Filters ─────────────────────────────────────────────────────────────
class _QueueFilter(django_filters.FilterSet):
    severity = django_filters.NumberFilter(field_name="severity")
    severity_min = django_filters.NumberFilter(field_name="severity", lookup_expr="gte")
    category = django_filters.CharFilter(method="filter_category")

    def filter_category(self, qs, name: str, value: str):  # noqa: ANN001, ARG002
        return qs.filter(output__categories__contains=[value])

    class Meta:
        model = ModerationDecision
        fields = ("severity", "severity_min", "category")


class _FlagFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=FlagStatus.choices)
    category = django_filters.CharFilter(field_name="reason")

    class Meta:
        model = Flag
        fields = ("status", "category")


# ─── Queue: list + next ──────────────────────────────────────────────────
def _queue_qs():
    return (ModerationDecision.objects
            .filter(action=ModerationAction.QUEUE)
            .select_related("target_type", "actor")
            .order_by("-severity", "created_at"))


class QueueListView(ListAPIView):
    """GET /api/v1/mod/queue/ — items pending human review."""

    serializer_class = QueueItemSerializer
    permission_classes = (IsModerator,)
    pagination_class = TimeCursorPagination
    filterset_class = _QueueFilter
    ordering = ("-severity", "created_at")

    def get_queryset(self):
        return _queue_qs()


_QUEUE_LOCK_TTL = 300  # 5 min


def _queue_lock_key(decision_id: int) -> str:
    return f"mod:queue:lock:{decision_id}"


class NextQueueItemView(GenericAPIView):
    """GET /api/v1/mod/queue/next/ — next un-locked highest-severity item.

    Optionally locks the item for 5 min so two mods don't double-handle it.
    """

    serializer_class = QueueItemSerializer
    permission_classes = (IsModerator,)

    @extend_schema(responses=QueueItemSerializer)
    def get(self, request: Request) -> Response:
        for item in _queue_qs()[:50]:
            lock_key = _queue_lock_key(item.pk)
            holder = cache.get(lock_key)
            if holder and holder != request.user.pk:
                continue
            cache.set(lock_key, request.user.pk, _QUEUE_LOCK_TTL)
            ser = self.get_serializer(item)
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response({"detail": "Queue empty."}, status=status.HTTP_204_NO_CONTENT)


# ─── Decision create ─────────────────────────────────────────────────────
_ACTION_TO_STATUS = {
    "approve":  ModerationStatus.APPROVED,
    "remove":   ModerationStatus.REMOVED,
    "escalate": ModerationStatus.PENDING,  # stays pending until ops triages
}


class DecisionCreateView(CreateAPIView):
    """POST /api/v1/mod/items/<id>/decision/ — moderator decision on a queued item."""

    serializer_class = DecisionCreateSerializer
    permission_classes = (IsModerator,)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        decision_id = self.kwargs["id"]
        prior = get_object_or_404(ModerationDecision, pk=decision_id)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ser.validated_data["action"]
        reason = ser.validated_data.get("reason", "")[:300]
        template_slug = ser.validated_data.get("action_template", "") or None

        with transaction.atomic():
            target = prior.target
            new_status = _ACTION_TO_STATUS.get(action, ModerationStatus.PENDING)
            if target is not None and hasattr(target, "moderation_status"):
                target.moderation_status = new_status
                target.moderated_at = timezone.now()
                target.save(update_fields=["moderation_status", "moderated_at"])

            human_decision = ModerationDecision.objects.create(
                target_type=prior.target_type,
                target_id=prior.target_id,
                layer=ModerationLayer.HUMAN,
                classifier_ver=f"human:{request.user.email}",
                input_hash=prior.input_hash,
                output={
                    "prior_action": prior.action,
                    "human_action": action,
                    "reason": reason,
                    "template_slug": template_slug,
                },
                action=action if action != "escalate" else ModerationAction.QUEUE,
                severity=prior.severity,
                reason=reason,
                actor=request.user,
            )

            # Resolve any open flags on this target.
            if prior.target_type and prior.target_id:
                Flag.objects.filter(
                    target_type=prior.target_type,
                    target_id=prior.target_id,
                    status=FlagStatus.OPEN,
                ).update(
                    status=FlagStatus.ACTIONED if action == "remove" else FlagStatus.DISMISSED,
                    resolved_by=request.user,
                )

            cache.delete(_queue_lock_key(prior.pk))

        # ActionLog auto-fires via signals.py (staff write to ModerationDecision).
        return Response(
            {
                "decision_id": human_decision.pk,
                "action": action,
                "applied_at": human_decision.created_at,
            },
            status=status.HTTP_201_CREATED,
        )


# ─── Escalate ────────────────────────────────────────────────────────────
class EscalateView(CreateAPIView):
    """POST /api/v1/mod/items/<id>/escalate/ — flag for operator attention.

    TODO: Phase 6 — replace with a dedicated `Escalation` model + assignment to
    operator queue. For now we write a HUMAN-layer decision with action=queue
    and an `escalated=true` marker in `output`, plus an ActionLog row.
    """

    serializer_class = EscalateSerializer
    permission_classes = (IsModerator,)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        decision_id = self.kwargs["id"]
        prior = get_object_or_404(ModerationDecision, pk=decision_id)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        notes = ser.validated_data["notes"]

        escalation = ModerationDecision.objects.create(
            target_type=prior.target_type,
            target_id=prior.target_id,
            layer=ModerationLayer.HUMAN,
            classifier_ver=f"human:{request.user.email}",
            input_hash=prior.input_hash,
            output={
                "prior_action": prior.action,
                "human_action": "escalate",
                "escalated": True,
                "notes": notes,
            },
            action=ModerationAction.QUEUE,
            severity=max(prior.severity or 0, 4),
            reason=f"escalated: {notes[:240]}",
            actor=request.user,
        )

        # Manual ActionLog row tagged "escalate" so ops can filter on it.
        try:
            ct = ContentType.objects.get_for_model(ModerationDecision)
            ActionLog.objects.create(
                actor=request.user,
                action="moderation.ModerationDecision.escalate",
                target_type=ct, target_id=escalation.pk,
                reason=notes[:1000],
            )
        except Exception:  # noqa: BLE001
            log.exception("escalate ActionLog failed")

        cache.delete(_queue_lock_key(prior.pk))
        return Response(
            {"escalation_id": escalation.pk, "status": "escalated"},
            status=status.HTTP_201_CREATED,
        )


# ─── Flags ───────────────────────────────────────────────────────────────
class FlagCreateView(CreateAPIView):
    """POST /api/v1/mod/flags/ — any authenticated user can flag content."""

    serializer_class = FlagCreateSerializer
    permission_classes = (IsAuthenticated,)
    throttle_classes = (FlagThrottle,)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        flag = ser.save()
        return Response(FlagSerializer(flag).data, status=status.HTTP_201_CREATED)


class FlagListView(ListAPIView):
    """GET /api/v1/mod/flags/ — moderator inbox of open flags."""

    serializer_class = FlagSerializer
    permission_classes = (IsModerator,)
    pagination_class = TimeCursorPagination
    filterset_class = _FlagFilter

    def get_queryset(self):
        return (Flag.objects
                .select_related("reporter", "target_type")
                .order_by("-created_at"))


# ─── Action templates ────────────────────────────────────────────────────
class ActionTemplateListView(ListAPIView):
    """GET /api/v1/mod/templates/ — preset reasons for one-click decisions."""

    serializer_class = ActionTemplateSerializer
    permission_classes = (IsModerator,)
    pagination_class = None

    def get_queryset(self):
        return _ACTION_TEMPLATES

    def list(self, request, *args, **kwargs):  # noqa: ANN001, ARG002
        ser = self.get_serializer(_ACTION_TEMPLATES, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)


# ─── Investigate user ────────────────────────────────────────────────────
def _safe_qs(import_path: str, **filters) -> list:
    """Best-effort import + filter. Returns [] if app/model missing."""
    try:
        module_path, _, name = import_path.rpartition(".")
        from importlib import import_module
        module = import_module(module_path)
        model = getattr(module, name)
        return list(model.objects.filter(**filters).order_by("-created_at")[:10])
    except Exception:  # noqa: BLE001
        return []


def _mini(items: list, *, kind: str, excerpt_field: str = "body") -> list[dict]:
    out = []
    for it in items:
        excerpt = getattr(it, excerpt_field, "") or getattr(it, "title", "") or ""
        out.append({
            "id": it.pk,
            "kind": kind,
            "excerpt": str(excerpt)[:200],
            "created_at": getattr(it, "created_at", None),
            "moderation_status": getattr(it, "moderation_status", ""),
        })
    return out


class InvestigateUserView(GenericAPIView):
    """GET /api/v1/mod/investigate/<int:user_id>/ — composite user dossier.

    Logs an AccessLog row tagged `surface=mod`. The Surface enum doesn't have
    an "investigation" kind yet — TODO: add `Surface.INVESTIGATION` so
    investigations are filterable independently from generic mod views.
    """

    serializer_class = InvestigateUserResultSerializer
    permission_classes = (IsModerator,)

    @extend_schema(responses=InvestigateUserResultSerializer)
    def get(self, request: Request, user_id: int) -> Response:
        target = User.objects.filter(pk=user_id).first()
        if target is None:
            raise NotFound("User not found.")
        if target.is_superuser and not request.user.is_superuser:
            raise PermissionDenied("Cannot investigate superuser.")

        # Audit the access (TODO: use a dedicated Surface.INVESTIGATION value).
        try:
            AccessLog.objects.create(
                actor=request.user, surface=Surface.MOD,
                path=request.path[:500], method=request.method,
                status_code=200,
                ip=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:400],
            )
        except Exception:  # noqa: BLE001
            log.exception("investigate AccessLog failed")

        recent_posts = _mini(_safe_qs("apps.content.models.Post", author=target),
                             kind="post", excerpt_field="title")
        recent_comments = _mini(_safe_qs("apps.content.models.Comment", author=target),
                                kind="comment", excerpt_field="body")
        recent_threads = _mini(_safe_qs("apps.forum.models.ForumThread", author=target),
                               kind="forum_thread", excerpt_field="title")
        recent_replies = _mini(_safe_qs("apps.forum.models.ForumReply", author=target),
                               kind="forum_reply", excerpt_field="body")

        flags_against = list(
            Flag.objects.select_related("reporter", "target_type")
            .filter(target_id=target.pk)
            .order_by("-created_at")[:20]
        )
        decisions = list(
            ModerationDecision.objects.select_related("target_type", "actor")
            .filter(actor=target)
            .order_by("-created_at")[:20]
        )

        warnings = ModerationDecision.objects.filter(
            target_type__app_label="accounts",
            target_type__model="user",
            target_id=target.pk,
            action__in=[ModerationAction.REMOVE, ModerationAction.SHADOW],
        ).count()

        account_age_days = 0
        if target.created_at:
            account_age_days = (timezone.now() - target.created_at).days

        payload = {
            "user": target,
            "recent_posts": recent_posts,
            "recent_comments": recent_comments,
            "recent_threads": recent_threads,
            "recent_replies": recent_replies,
            "recent_flags_against": flags_against,
            "recent_decisions": decisions,
            "total_warnings": warnings,
            "last_seen": target.last_seen,
            "account_age_days": account_age_days,
        }
        ser = self.get_serializer(payload)
        return Response(ser.data, status=status.HTTP_200_OK)
