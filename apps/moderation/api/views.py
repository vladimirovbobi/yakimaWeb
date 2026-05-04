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
    ActionTemplate,
    Flag,
    FlagStatus,
    ModerationAction,
    ModerationDecision,
    ModerationLayer,
    ModerationStatus,
)
from ..services.mod_stats import stats_for_moderator, stats_timeseries
from .serializers import (
    ActionTemplateSerializer,
    DecisionCreateSerializer,
    EscalateSerializer,
    EscalationListItemSerializer,
    FlagCreateSerializer,
    FlagSerializer,
    InvestigateUserResultSerializer,
    ModeratorStatsSerializer,
    QueueItemSerializer,
)

log = logging.getLogger(__name__)
User = get_user_model()


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
    """GET /api/v1/mod/templates/ — preset reasons for one-click decisions.

    Sourced from ActionTemplate model (Sprint 5). Seed via:
        python manage.py seed_action_templates
    """

    serializer_class = ActionTemplateSerializer
    permission_classes = (IsModerator,)
    pagination_class = None

    def get_queryset(self):
        return ActionTemplate.objects.filter(is_active=True).order_by("sort_order", "label")


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

        # Sprint 5 — pattern signals.
        # Heuristic A: same reporter mass-flagging this user (>=3 in 7 days)
        # Heuristic B: rapid posting velocity (>10 items in 24h)
        # Heuristic C: repeat offender (>=2 prior remove/shadow warnings)
        cutoff_7 = timezone.now() - timedelta(days=7)
        cutoff_30 = timezone.now() - timedelta(days=30)

        seen_counts: dict[int, int] = {}
        for f in Flag.objects.filter(target_id=target.pk, created_at__gte=cutoff_7):
            seen_counts[f.reporter_id] = seen_counts.get(f.reporter_id, 0) + 1
        repeat_reporter_ids = [uid for uid, c in seen_counts.items() if c >= 3]

        # Recent moderation decisions where this user was the actor.
        recent_decision_count_30d = ModerationDecision.objects.filter(
            created_at__gte=cutoff_30,
            actor=target,
        ).count()

        post_count_24h = 0
        try:
            from apps.content.models import Comment as _C
            from apps.content.models import Post as _P
            cutoff_24 = timezone.now() - timedelta(hours=24)
            post_count_24h = (_P.objects.filter(author=target, created_at__gte=cutoff_24).count()
                              + _C.objects.filter(author=target, created_at__gte=cutoff_24).count())
        except Exception:  # noqa: BLE001
            post_count_24h = 0

        pattern_signals: list[str] = []
        if repeat_reporter_ids:
            pattern_signals.append(
                f"mass_flagging_by_{len(repeat_reporter_ids)}_reporters"
            )
        if post_count_24h > 10:
            pattern_signals.append("rapid_posting_velocity")
        if warnings >= 2:
            pattern_signals.append("repeat_offender")

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
            "pattern_signals": pattern_signals,
            "post_count_24h": post_count_24h,
            "recent_decision_count_30d": recent_decision_count_30d,
        }
        ser = self.get_serializer(payload)
        return Response(ser.data, status=status.HTTP_200_OK)


# ─── Moderator stats ────────────────────────────────────────────────────
class ModStatsView(GenericAPIView):
    """GET /api/v1/mod/stats/ — own stats (mod) or any moderator's (?user_id=, op-only)."""

    serializer_class = ModeratorStatsSerializer
    permission_classes = (IsModerator,)

    def get(self, request: Request) -> Response:
        target_uid = request.query_params.get("user_id")
        if target_uid:
            try:
                target_uid_int = int(target_uid)
            except ValueError:
                return Response({"detail": "user_id must be int."},
                                status=status.HTTP_400_BAD_REQUEST)
            is_op = bool(
                request.user.is_superuser
                or request.user.groups.filter(name="operator").exists()
            )
            if target_uid_int != request.user.pk and not is_op:
                raise PermissionDenied("Operator role required to view another mod's stats.")
            user_id = target_uid_int
        else:
            user_id = request.user.pk

        data = stats_for_moderator(user_id)
        data["timeseries_30d"] = stats_timeseries(user_id, days=30)
        ser = self.get_serializer(data)
        return Response(ser.data, status=status.HTTP_200_OK)


# ─── Escalation list ────────────────────────────────────────────────────
class EscalationListView(ListAPIView):
    """GET /api/v1/mod/escalations/ — operator inbox of mod escalations.

    Escalations are ModerationDecision rows with `output.escalated == True`.
    See EscalateView for write path.
    """

    serializer_class = EscalationListItemSerializer
    permission_classes = (IsModerator,)
    pagination_class = TimeCursorPagination

    def get_queryset(self):
        # Only operators see escalations. Mods get an empty list per safety contract.
        u = self.request.user
        is_op = bool(
            u.is_superuser or u.groups.filter(name="operator").exists()
        )
        if not is_op:
            return ModerationDecision.objects.none()
        return (ModerationDecision.objects
                .filter(layer=ModerationLayer.HUMAN, output__escalated=True)
                .select_related("actor", "target_type")
                .order_by("-created_at"))
