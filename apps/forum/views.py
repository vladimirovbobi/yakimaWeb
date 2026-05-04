"""Forum views: hot/new/top index, thread detail, create, reply, vote."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Flair, ForumReply, ForumThread, Vote


def _sort_threads(qs, sort: str):
    if sort == "new":
        return qs.order_by("-pinned", "-created_at")
    if sort == "top":
        return qs.order_by("-pinned", "-score", "-created_at")
    # hot — Python-side sort over recent items only (cap at 200 for speed)
    items = list(qs.order_by("-pinned", "-created_at")[:200])
    items.sort(key=lambda t: (-int(t.pinned), -t.hot_score))
    return items


def thread_list(request: HttpRequest) -> HttpResponse:
    sort = request.GET.get("sort", "hot")
    flair_slug = request.GET.get("flair")
    qs = (ForumThread.objects
          .filter(moderation_status="approved")
          .select_related("author", "flair"))
    if flair_slug:
        qs = qs.filter(flair__slug=flair_slug)
    threads = _sort_threads(qs, sort)
    return render(request, "forum/thread_list.html", {
        "threads": threads, "sort": sort,
        "flairs": Flair.objects.all(),
        "active_flair": flair_slug or "",
    })


def thread_detail(request: HttpRequest, slug: str) -> HttpResponse:
    thread = get_object_or_404(
        ForumThread.objects.select_related("author", "flair"),
        slug=slug,
    )
    if thread.moderation_status != "approved" and request.user.pk != thread.author_id:
        return render(request, "forum/_pending.html", {"thread": thread})

    replies = (thread.replies
               .filter(moderation_status="approved", parent__isnull=True)
               .select_related("author")
               .prefetch_related("children__author"))
    return render(request, "forum/thread_detail.html", {
        "thread": thread,
        "replies": replies,
        "user_votes": _user_vote_map(request.user, thread, replies),
    })


def _user_vote_map(user, thread, replies) -> dict:
    """Return {(model, pk): value} for the current user's votes on these items."""
    if not user.is_authenticated:
        return {}
    targets = [thread]
    for r in replies:
        targets.append(r)
        targets.extend(r.children.all())
    if not targets:
        return {}
    by_ct = {}
    for t in targets:
        ct = ContentType.objects.get_for_model(t.__class__)
        by_ct.setdefault(ct.pk, []).append(t.pk)
    votes = []
    for ct_id, ids in by_ct.items():
        votes += list(Vote.objects.filter(target_type_id=ct_id, target_id__in=ids, voter=user))
    return {(v.target_type.model, v.target_id): v.value for v in votes}


@login_required
@require_http_methods(["GET", "POST"])
def thread_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        flair_id = request.POST.get("flair")
        title    = (request.POST.get("title") or "").strip()
        body     = (request.POST.get("body") or "").strip()
        if not (flair_id and title and body):
            messages.error(request, "Title + flair + body required.")
            return redirect("forum:thread_create")
        flair = get_object_or_404(Flair, pk=flair_id)
        thread = ForumThread.objects.create(
            author=request.user, flair=flair, title=title[:240], body=body[:10000],
        )
        messages.info(request, "Posted — moderation will review before it's visible.")
        return redirect(thread.get_absolute_url())
    return render(request, "forum/thread_create.html", {"flairs": Flair.objects.all()})


@login_required
@require_http_methods(["POST"])
def reply_create(request: HttpRequest, slug: str) -> HttpResponse:
    thread = get_object_or_404(ForumThread, slug=slug)
    if thread.locked:
        messages.error(request, "Thread is locked.")
        return redirect(thread.get_absolute_url())
    body = (request.POST.get("body") or "").strip()
    if not body:
        return redirect(thread.get_absolute_url())
    parent_id = request.POST.get("parent_id")
    parent = None
    if parent_id and parent_id.isdigit():
        parent = ForumReply.objects.filter(pk=int(parent_id), thread=thread).first()
    ForumReply.objects.create(
        thread=thread, author=request.user, body=body[:10000], parent=parent,
    )
    messages.info(request, "Reply submitted — moderation pending.")
    return redirect(thread.get_absolute_url())


@login_required
@require_http_methods(["POST"])
def vote(request: HttpRequest, target_type: str, target_id: int) -> JsonResponse:
    """Toggle/change a vote. value=1 or -1 in POST body."""
    try:
        value = int(request.POST.get("value", "0"))
    except ValueError:
        return JsonResponse({"error": "value must be -1 or 1"}, status=400)
    if value not in (-1, 1):
        return JsonResponse({"error": "value must be -1 or 1"}, status=400)
    if target_type not in ("forumthread", "forumreply"):
        return JsonResponse({"error": "bad target_type"}, status=400)

    ct = ContentType.objects.get(app_label="forum", model=target_type)
    target_class = ct.model_class()
    target = get_object_or_404(target_class, pk=target_id)

    existing = Vote.objects.filter(target_type=ct, target_id=target_id, voter=request.user).first()
    if existing is None:
        Vote.objects.create(target_type=ct, target_id=target_id, voter=request.user, value=value)
    elif existing.value == value:
        # Same value → unvote
        existing.delete()
        target.refresh_from_db()
        return JsonResponse({"score": target.score, "user_value": 0})
    else:
        existing.value = value
        existing.updated_at = timezone.now()
        existing.save()
    target.refresh_from_db()
    return JsonResponse({"score": target.score, "user_value": value})
