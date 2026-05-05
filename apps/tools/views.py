"""Tool views — auth required, rate-limited, async via Celery."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import Tool, ToolUsage
from .services.rate_limit import check_and_consume, daily_spend_usd, usage_today
from .tasks import run_description_writer


def tool_index(request: HttpRequest) -> HttpResponse:
    tools = Tool.objects.filter(is_enabled=True).order_by("name")
    return render(request, "tools/index.html", {"tools": tools})


@login_required
@require_http_methods(["GET", "POST"])
def description_writer(request: HttpRequest) -> HttpResponse:
    tool = get_object_or_404(Tool, slug="description-writer")
    today = usage_today(request.user, tool)
    limit = tool.daily_limit_for(request.user)

    if request.method == "POST":
        ok, reason = check_and_consume(request.user, tool)
        if not ok:
            messages.error(request, f"Rate limit hit ({reason}). Comes back tomorrow.")
            return redirect("tools:description_writer")

        usage = ToolUsage.objects.create(
            user=request.user, tool=tool,
            input_meta={"property_facts": request.POST.get("facts", "")[:5000]},
        )
        run_description_writer.delay(usage.pk)
        messages.info(request, "Generating — refresh in a few seconds.")
        return redirect("tools:description_writer_result", pk=usage.pk)

    recent = (request.user.tool_runs
              .filter(tool=tool).order_by("-created_at")[:5])
    return render(request, "tools/description_writer.html", {
        "tool": tool, "today": today, "limit": limit, "recent": recent,
    })


@login_required
def description_writer_result(request: HttpRequest, pk: int) -> HttpResponse:
    usage = get_object_or_404(ToolUsage, pk=pk, user=request.user)
    template = "tools/_description_partial.html" if request.htmx else "tools/description_writer_result.html"
    return render(request, template, {"usage": usage})


def furniture_remover(request: HttpRequest) -> HttpResponse:
    """Stub — full implementation in Phase 3 with React island."""
    return render(request, "tools/furniture_remover.html")


@login_required
def usage_today_json(request: HttpRequest, slug: str) -> JsonResponse:
    """For JS clients to show "X/Y today" counters."""
    tool = get_object_or_404(Tool, slug=slug)
    return JsonResponse({
        "today": usage_today(request.user, tool),
        "limit": tool.daily_limit_for(request.user),
        "spend_today_usd": daily_spend_usd(tool),
    })
