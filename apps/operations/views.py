"""Operator dashboard + Moderator console + audit viewer."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.models import Role
from apps.audit.models import AccessLog, ActionLog
from apps.moderation.models import (ModerationAction, ModerationDecision,
                                     ModerationStatus)

from .services.dashboard import all_cards


def _require_staff(request: HttpRequest):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        raise PermissionDenied("staff access required")
    if user.role not in (Role.STAFF, Role.ADMIN) and not user.is_superuser:
        raise PermissionDenied("staff role required")


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    _require_staff(request)
    cards = all_cards()
    return render(request, "operations/dashboard.html", {"cards": cards})


@login_required
def mod_queue(request: HttpRequest) -> HttpResponse:
    _require_staff(request)
    items = (ModerationDecision.objects
             .filter(action=ModerationAction.QUEUE)
             .select_related("target_type", "actor")
             .order_by("-severity", "-created_at")[:50])
    return render(request, "operations/mod_queue.html", {"items": items})


@login_required
@require_http_methods(["POST"])
def mod_action(request: HttpRequest, decision_id: int) -> HttpResponse:
    _require_staff(request)
    decision = get_object_or_404(ModerationDecision, pk=decision_id)
    new_action = request.POST.get("action")
    if new_action not in {"approve", "remove", "shadow"}:
        messages.error(request, "Invalid action.")
        return redirect("operations:mod_queue")

    target = decision.target
    if target is not None and hasattr(target, "moderation_status"):
        status_map = {
            "approve": ModerationStatus.APPROVED,
            "remove":  ModerationStatus.REMOVED,
            "shadow":  ModerationStatus.SHADOW,
        }
        target.moderation_status = status_map[new_action]
        target.moderated_at = timezone.now()
        target.save(update_fields=["moderation_status", "moderated_at"])

    # Log a new ModerationDecision (human layer) — never overwrite the AI decision row
    ModerationDecision.objects.create(
        target_type=decision.target_type,
        target_id=decision.target_id,
        layer="human",
        classifier_ver=f"human:{request.user.email}",
        input_hash=decision.input_hash,
        output={"prior_action": decision.action, "human_action": new_action,
                "reason": request.POST.get("reason", "")},
        action=new_action,
        severity=decision.severity,
        reason=request.POST.get("reason", "")[:300],
        actor=request.user,
    )
    messages.success(request, f"{new_action.capitalize()}d.")
    return redirect("operations:mod_queue")


@login_required
def audit_viewer(request: HttpRequest) -> HttpResponse:
    _require_staff(request)
    actions = ActionLog.objects.select_related("actor").order_by("-created_at")[:100]
    accesses = AccessLog.objects.select_related("actor").order_by("-created_at")[:100]
    return render(request, "operations/audit.html", {
        "actions": actions, "accesses": accesses,
    })
