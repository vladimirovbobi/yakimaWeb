"""Tests for the notify() service + email digest + REST endpoints."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.notifications.services import (
    mark_all_read,
    mark_read,
    notify,
    unread_count,
)
from apps.notifications.tasks import deliver_email_digest

User = get_user_model()


@pytest.fixture
def member(db):
    return User.objects.create_user(email="m@example.com", password="pa$$word-12345")


@pytest.fixture
def auth_client(member):
    c = APIClient()
    c.force_authenticate(user=member)
    # Prime + mirror the yw_csrf cookie so StrictCSRFMixin's double-submit
    # check passes on POST/PATCH. EnsureCSRFCookieMiddleware sets the cookie
    # on any GET; we mirror it into the default header for subsequent unsafe
    # methods.
    c.get("/api/v1/me/")
    cookie = c.cookies.get("yw_csrf")
    if cookie is not None:
        c.defaults["HTTP_X_CSRFTOKEN"] = cookie.value
    return c


@pytest.mark.django_db
class TestNotificationModel:
    def test_save_and_str(self, member):
        n = Notification.objects.create(
            user=member, kind="lead_received",
            title="Test", body="hello",
        )
        assert n.pk is not None
        assert "lead_received" in str(n)
        assert n.is_read is False


@pytest.mark.django_db
class TestNotifyService:
    def test_notify_emits_row(self, member):
        n = notify(member, "lead_message", title="x", body="y", link="/z")
        assert n is not None
        assert Notification.objects.filter(user=member).count() == 1

    def test_notify_rejects_unknown_kind(self, member):
        n = notify(member, "fake_kind", title="x")
        assert n is None
        assert Notification.objects.filter(user=member).count() == 0

    def test_notify_handles_user_id_int(self, member):
        n = notify(member.pk, "lead_received", title="x")
        assert n is not None
        assert n.user_id == member.pk

    def test_unread_count_and_mark_read(self, member):
        notify(member, "lead_received", title="a")
        notify(member, "lead_received", title="b")
        assert unread_count(member) == 2
        ids = list(Notification.objects.filter(user=member).values_list("pk", flat=True))
        mark_read(member, ids[:1])
        assert unread_count(member) == 1
        mark_all_read(member)
        assert unread_count(member) == 0


@pytest.mark.django_db
class TestDigestTask:
    def test_digest_sends_one_email_per_user_with_unread(self, member, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        notify(member, "lead_received", title="hello", link="/x")
        notify(member, "lead_message", title="hi again", link="/y")
        from django.core import mail
        out = deliver_email_digest()
        assert out["users_emailed"] == 1
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [member.email]
        # Both notifications should be flagged as emailed.
        assert Notification.objects.filter(emailed_at__isnull=True).count() == 0

    def test_digest_skips_when_already_emailed(self, member, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        notify(member, "lead_received", title="hello")
        deliver_email_digest()
        from django.core import mail
        mail.outbox.clear()
        out = deliver_email_digest()
        assert out["users_emailed"] == 0
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestNotificationApi:
    def test_list_endpoint(self, auth_client, member):
        notify(member, "lead_received", title="a")
        notify(member, "forum_reply", title="b")
        url = reverse("v1:notifications-list")
        r = auth_client.get(url)
        assert r.status_code == 200
        data = r.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        assert len(results) == 2

    def test_unread_count_endpoint(self, auth_client, member):
        notify(member, "lead_received", title="a")
        url = reverse("v1:notifications-unread-count")
        r = auth_client.get(url)
        assert r.status_code == 200
        assert r.json() == {"count": 1}

    def test_mark_read_endpoint(self, auth_client, member):
        n = notify(member, "lead_received", title="a")
        url = reverse("v1:notifications-mark-read", kwargs={"pk": n.pk})
        r = auth_client.post(url)
        assert r.status_code == 200
        assert r.json() == {"updated": 1}
        assert Notification.objects.get(pk=n.pk).is_read

    def test_mark_all_read_endpoint(self, auth_client, member):
        notify(member, "lead_received", title="a")
        notify(member, "forum_reply", title="b")
        url = reverse("v1:notifications-read-all")
        r = auth_client.post(url)
        assert r.status_code == 200
        assert r.json() == {"updated": 2}
        assert unread_count(member) == 0

    def test_list_isolates_users(self, auth_client, member):
        other = User.objects.create_user(email="o@example.com", password="pa$$word-12345")
        notify(other, "lead_received", title="not yours")
        notify(member, "lead_received", title="yours")
        url = reverse("v1:notifications-list")
        r = auth_client.get(url)
        data = r.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        titles = [n["title"] for n in results]
        assert "yours" in titles
        assert "not yours" not in titles
