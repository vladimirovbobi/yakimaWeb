"""Public + authoring views for posts + comments."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import CommentForm, PostForm
from .models import Comment, Post, PostStatus, PostType
from .services.sanitize import render_markdown


def post_list(request: HttpRequest) -> HttpResponse:
    """List approved + published posts. Filter by post_type via querystring."""
    qs = (Post.objects
          .filter(status=PostStatus.PUBLISHED, moderation_status="approved")
          .select_related("author"))
    pt = request.GET.get("type")
    if pt in PostType.values:
        qs = qs.filter(post_type=pt)
    return render(request, "content/post_list.html", {
        "posts": qs[:30],
        "active_type": pt or "all",
    })


def post_detail(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_object_or_404(
        Post.objects.select_related("author"),
        slug=slug,
    )
    if not post.is_visible and (not request.user.is_authenticated or request.user.pk != post.author_id):
        raise PermissionDenied("post not visible")
    Post.objects.filter(pk=post.pk).update(view_count=F("view_count") + 1)
    comments = (post.comments
                .filter(moderation_status="approved", parent__isnull=True)
                .select_related("author")
                .prefetch_related("replies__author"))
    body_html = render_markdown(post.body)
    return render(request, "content/post_detail.html", {
        "post": post,
        "body_html": body_html,
        "comments": comments,
        "comment_form": CommentForm() if request.user.is_authenticated else None,
    })


@login_required
@require_http_methods(["POST"])
def comment_create(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_object_or_404(Post, slug=slug)
    form = CommentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Comment couldn't be saved.")
        return redirect(post.get_absolute_url())
    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    parent_id = request.POST.get("parent_id")
    if parent_id and parent_id.isdigit():
        comment.parent = Comment.objects.filter(pk=int(parent_id), post=post).first()
    comment.save()
    messages.info(request, "Comment submitted — visible after moderation.")
    return redirect(post.get_absolute_url())


@login_required
@require_http_methods(["GET", "POST"])
def post_authoring(request: HttpRequest) -> HttpResponse:
    """Verified realtors only — write blog posts."""
    if not request.user.is_realtor:
        raise PermissionDenied("realtor verification required")
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.post_type = PostType.BLOG
            if form.cleaned_data.get("publish"):
                post.status = PostStatus.PUBLISHED
                post.published_at = timezone.now()
            post.save()
            messages.success(request, "Saved — moderation will review before it goes live.")
            return redirect(post.get_absolute_url() if post.is_visible else "content:my_posts")
    else:
        form = PostForm()
    return render(request, "content/post_author.html", {"form": form})


@login_required
def my_posts(request: HttpRequest) -> HttpResponse:
    qs = Post.objects.filter(author=request.user).order_by("-created_at")
    return render(request, "content/my_posts.html", {"posts": qs})


def videos(request: HttpRequest) -> HttpResponse:
    """Public videos + Shorts page — pulls SocialEmbed records."""
    from .models import SocialEmbed
    items = SocialEmbed.objects.all()[:24]
    return render(request, "content/videos.html", {"items": items})
