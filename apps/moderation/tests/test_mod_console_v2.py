"""Sprint 5 mod-console-v2 tests — stats, escalations, action templates."""
from __future__ import annotations


import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.moderation.models import (
    ActionTemplate,
    ModerationAction,
    ModerationDecision,
    ModerationLayer,
)
from apps.moderation.services.mod_stats import stats_for_moderator

User = get_user_model()


@pytest.fixture
def moderator(db):
    u = User.objects.create_user(email="mod@example.com", password="pa$$word-1234",
                                  is_staff=True)
    grp, _ = Group.objects.get_or_create(name="moderator")
    u.groups.add(grp)
    return u


@pytest.fixture
def operator(db):
    u = User.objects.create_user(email="op@example.com", password="pa$$word-1234",
                                  is_staff=True)
    grp, _ = Group.objects.get_or_create(name="operator")
    u.groups.add(grp)
    return u


@pytest.fixture
def auth_client(moderator):
    c = APIClient()
    c.force_authenticate(user=moderator)
    return c


@pytest.fixture
def op_client(operator):
    c = APIClient()
    c.force_authenticate(user=operator)
    return c


# ────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
class TestSeedActionTemplates:
    def test_seed_creates_rows(self):
        call_command("seed_action_templates")
        assert ActionTemplate.objects.filter(slug="removed_spam").exists()
        assert ActionTemplate.objects.filter(slug="approved_no_change").exists()
        assert ActionTemplate.objects.count() >= 7

    def test_seed_idempotent(self):
        call_command("seed_action_templates")
        first = ActionTemplate.objects.count()
        call_command("seed_action_templates")
        second = ActionTemplate.objects.count()
        assert first == second

    def test_seed_updates_existing(self):
        ActionTemplate.objects.create(
            slug="removed_spam", label="Old label", action="remove",
            default_reason="Old reason", sort_order=1,
        )
        call_command("seed_action_templates")
        obj = ActionTemplate.objects.get(slug="removed_spam")
        assert obj.label == "Removed - Spam"
        assert obj.sort_order == 10


@pytest.mark.django_db
class TestActionTemplateEndpoint:
    def test_endpoint_returns_seeded_templates(self, auth_client):
        call_command("seed_action_templates")
        url = reverse("v1:mod-template-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        slugs = {item["slug"] for item in resp.data}
        assert "removed_spam" in slugs
        assert "approved_no_change" in slugs

    def test_inactive_excluded(self, auth_client):
        call_command("seed_action_templates")
        ActionTemplate.objects.filter(slug="removed_spam").update(is_active=False)
        url = reverse("v1:mod-template-list")
        resp = auth_client.get(url)
        slugs = {item["slug"] for item in resp.data}
        assert "removed_spam" not in slugs

    def test_unauth_blocked(self):
        url = reverse("v1:mod-template-list")
        resp = APIClient().get(url)
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestModStats:
    def test_stats_shape(self, auth_client, moderator):
        url = reverse("v1:mod-stats")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        for key in ("items_reviewed_30d", "items_reviewed_7d",
                    "agreement_rate", "reversal_rate",
                    "avg_response_minutes", "current_streak", "queue_position"):
            assert key in resp.data

    def test_stats_counts_human_decisions(self, moderator):
        ModerationDecision.objects.create(
            actor=moderator, layer=ModerationLayer.HUMAN,
            action=ModerationAction.APPROVE, severity=1, input_hash="h1",
        )
        ModerationDecision.objects.create(
            actor=moderator, layer=ModerationLayer.HUMAN,
            action=ModerationAction.REMOVE, severity=3, input_hash="h2",
        )
        result = stats_for_moderator(moderator.pk)
        assert result["items_reviewed_30d"] == 2

    def test_stats_user_id_param_op_only(self, auth_client, op_client, moderator):
        url = reverse("v1:mod-stats")
        # Mod cannot view another mod's stats by user_id
        other = User.objects.create_user(email="other@example.com", password="x")
        resp = auth_client.get(url, {"user_id": other.pk})
        assert resp.status_code == 403
        # Operator can
        resp_op = op_client.get(url, {"user_id": moderator.pk})
        assert resp_op.status_code == 200


@pytest.mark.django_db
class TestEscalationList:
    def test_mod_sees_empty(self, auth_client, moderator):
        # Create an escalation row.
        ModerationDecision.objects.create(
            actor=moderator, layer=ModerationLayer.HUMAN,
            action=ModerationAction.QUEUE, severity=4, input_hash="h",
            output={"escalated": True, "notes": "weird case"},
        )
        url = reverse("v1:mod-escalation-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        # Empty for non-operators per safety contract.
        results = resp.data.get("results", resp.data)
        assert len(results) == 0

    def test_op_sees_escalations(self, op_client, moderator):
        ModerationDecision.objects.create(
            actor=moderator, layer=ModerationLayer.HUMAN,
            action=ModerationAction.QUEUE, severity=4, input_hash="h",
            output={"escalated": True, "notes": "weird case"},
        )
        url = reverse("v1:mod-escalation-list")
        resp = op_client.get(url)
        assert resp.status_code == 200
        results = resp.data.get("results", resp.data)
        assert len(results) >= 1
        item = results[0]
        assert "notes" in item
        assert "escalated_by" in item

    def test_unauth_blocked(self):
        url = reverse("v1:mod-escalation-list")
        resp = APIClient().get(url)
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestImageModerationFailClosed:
    def test_empty_image_removed(self):
        from apps.moderation.services.image_moderation import moderate_image
        result = moderate_image(b"", mime="image/jpeg")
        assert result.action == "remove"
        assert not result.allowed

    def test_oversized_image_removed(self):
        from apps.moderation.services.image_moderation import moderate_image
        big = b"X" * (11 * 1024 * 1024)
        result = moderate_image(big, mime="image/jpeg")
        assert result.action == "remove"

    def test_bad_mime_removed(self):
        from apps.moderation.services.image_moderation import moderate_image
        result = moderate_image(b"hello", mime="application/pdf")
        assert result.action == "remove"

    def test_parse_error_queues_not_approves(self):
        from apps.moderation.services.image_moderation import _parse_vision_response
        # Garbage response -> queue, never approve.
        parsed = _parse_vision_response("not json")
        assert parsed["action"] == "queue"
        assert parsed["allowed"] is False


@pytest.mark.django_db
class TestInvestigatePatternSignals:
    def test_pattern_signals_in_response(self, auth_client, moderator):
        target = User.objects.create_user(email="tgt@example.com", password="x")
        url = reverse("v1:mod-investigate-user", kwargs={"user_id": target.pk})
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert "pattern_signals" in resp.data
        assert "post_count_24h" in resp.data
