"""Post + Comment model tests."""
import pytest
from django.utils import timezone

from apps.content.models import Comment, Post, PostStatus, PostType
from apps.content.services.sanitize import render_markdown


@pytest.mark.django_db
class TestPost:
    def test_slug_auto(self, realtor):
        p = Post.objects.create(author=realtor, title="Yakima Market April",
                                body="hello", post_type=PostType.BLOG)
        assert p.slug == "yakima-market-april"

    def test_is_visible_requires_published_and_approved(self, realtor):
        p = Post.objects.create(author=realtor, title="t", body="hello",
                                status=PostStatus.PUBLISHED)
        # Default moderation_status is "pending"
        assert not p.is_visible
        p.moderation_status = "approved"
        p.save()
        assert p.is_visible

    def test_get_absolute_url(self, realtor):
        p = Post.objects.create(author=realtor, title="Hello World", body="x")
        assert "/blog/hello-world/" in p.get_absolute_url() or "hello-world" in p.get_absolute_url()


@pytest.mark.django_db
class TestComment:
    def test_threading(self, user, realtor):
        post = Post.objects.create(author=realtor, title="P", body="x",
                                    status=PostStatus.PUBLISHED, moderation_status="approved",
                                    published_at=timezone.now())
        parent = Comment.objects.create(post=post, author=user, body="hi")
        reply  = Comment.objects.create(post=post, author=realtor, body="hi back", parent=parent)
        assert reply.parent == parent
        assert parent.replies.count() == 1


class TestSanitize:
    def test_renders_basic_markdown(self):
        # h2-h4 allowed in body (h1 reserved for page title)
        html = render_markdown("## Hi\n\n**bold** [link](https://example.com)")
        assert "<h2" in html
        assert "<strong>bold</strong>" in html
        assert 'href="https://example.com"' in html

    def test_strips_h1_to_text(self):
        # h1 stripped — body shouldn't override page heading hierarchy
        html = render_markdown("# Page Title")
        assert "<h1" not in html

    def test_strips_script_tag(self):
        html = render_markdown('<script>alert(1)</script>OK')
        assert "<script" not in html
        assert "OK" in html

    def test_strips_javascript_url(self):
        html = render_markdown('[bad](javascript:alert(1))')
        assert "javascript:" not in html

    def test_strips_dangerous_attributes(self):
        html = render_markdown('<a href="x" onclick="alert(1)">hi</a>')
        assert "onclick" not in html
