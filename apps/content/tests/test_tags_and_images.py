"""Sprint 5 content polish tests — Tag M2M + comment image moderation hook."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content.models import Comment, Post, PostStatus, PostType, Tag
from apps.content.services.sanitize import render_post_body, sanitize_html

User = get_user_model()


@pytest.fixture
def realtor(db):
    u = User.objects.create_user(email="realtor@example.com",
                                 password="pa$$word-1234",
                                 is_realtor=True)
    return u


def _png_bytes() -> bytes:
    """Tiny valid PNG (1x1 red dot)."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xcf"
        b"\xc0\x00\x00\x00\x03\x00\x01\xb1\xfd\x18\x96\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.mark.django_db
class TestTagModel:
    def test_auto_slug(self):
        t = Tag.objects.create(name="Yakima Market")
        assert t.slug == "yakima-market"

    def test_post_tag_m2m(self, realtor):
        post = Post.objects.create(author=realtor, title="P", body="x")
        t1 = Tag.objects.create(slug="market", name="Market")
        t2 = Tag.objects.create(slug="trends", name="Trends")
        post.tags.add(t1, t2)
        assert post.tags.count() == 2
        assert t1.posts.first() == post


@pytest.mark.django_db
class TestTagListEndpoint:
    def test_returns_tags_with_counts(self, realtor):
        t = Tag.objects.create(slug="market", name="Market")
        post = Post.objects.create(
            author=realtor, title="P", body="x",
            status=PostStatus.PUBLISHED, moderation_status="approved",
            published_at=timezone.now(),
        )
        post.tags.add(t)

        url = reverse("public_v1:posts-tags-list")
        resp = APIClient().get(url)
        assert resp.status_code == 200
        data = resp.data
        slugs = [item["slug"] for item in data]
        assert "market" in slugs
        market = next(item for item in data if item["slug"] == "market")
        assert market["post_count"] == 1

    def test_tag_detail_lists_posts(self, realtor):
        t = Tag.objects.create(slug="market", name="Market")
        post = Post.objects.create(
            author=realtor, title="Yakima April", body="x",
            status=PostStatus.PUBLISHED, moderation_status="approved",
            published_at=timezone.now(),
        )
        post.tags.add(t)

        url = reverse("public_v1:posts-tag-detail", kwargs={"slug": "market"})
        resp = APIClient().get(url)
        assert resp.status_code == 200
        assert resp.data["tag"]["slug"] == "market"
        results = resp.data.get("results", [])
        assert len(results) == 1


@pytest.mark.django_db
class TestCommentImageModeration:
    def test_image_save_fires_signal(self, realtor):
        post = Post.objects.create(
            author=realtor, title="P", body="x",
            status=PostStatus.PUBLISHED, moderation_status="approved",
            published_at=timezone.now(),
        )
        with patch(
            "apps.content.signals.moderate_image_task.apply_async",
        ) as mock_apply:
            comment = Comment.objects.create(
                post=post, author=realtor, body="check this out",
                image=SimpleUploadedFile("a.png", _png_bytes(),
                                          content_type="image/png"),
            )
            assert mock_apply.called
            kwargs = mock_apply.call_args.kwargs
            # Routed to dedicated images queue with positional args.
            assert kwargs.get("queue") == "images"
            assert kwargs["args"][1] == comment.pk
            assert kwargs["kwargs"].get("image_attr") == "image"

    def test_no_image_no_signal(self, realtor):
        post = Post.objects.create(
            author=realtor, title="P", body="x",
            status=PostStatus.PUBLISHED, moderation_status="approved",
            published_at=timezone.now(),
        )
        with patch(
            "apps.content.signals.moderate_image_task.apply_async",
        ) as mock_apply:
            Comment.objects.create(post=post, author=realtor, body="no image")
            assert not mock_apply.called


class TestSanitize:
    def test_sanitize_html_blocks_script(self):
        html = sanitize_html("<p>ok</p><script>alert(1)</script>")
        assert "<script" not in html
        assert "<p>ok</p>" in html

    def test_render_post_body_html_path(self):
        # TipTap output is raw HTML — render_post_body should sanitize, not re-markdown.
        out = render_post_body("<p>hello</p><h2>world</h2>")
        assert "<p>hello</p>" in out
        assert "<h2>world</h2>" in out

    def test_render_post_body_markdown_path(self):
        # Plain markdown still works.
        out = render_post_body("**bold**")
        assert "<strong>bold</strong>" in out
