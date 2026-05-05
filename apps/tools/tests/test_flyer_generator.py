"""End-to-end tests for the flyer-generator API + run_flyer_generator task.

These tests touch the DB; they pass once docker-compose's db + redis are up.
The pure-function backend tests live in test_flyer_generator_claude_cli.py;
the PDF-render task tests live in test_flyer_pdf.py.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from apps.tools.models import Tool, ToolUsage, UsageStatus
from apps.tools.services.flyer_generator.base import FlyerGenerationError, FlyerResult

GOOD_HTML = (
    "<!doctype html><html><head><style>body{font-family:serif}</style></head>"
    "<body><h1>142 Sample St</h1><p>Quiet light, north exposure.</p></body></html>"
)


@pytest.fixture
def _flush_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def flyer_tool(db):
    return Tool.objects.create(
        slug="flyer-generator",
        name="Realtor Flyer Generator",
        description="x",
        model_id="claude-opus-4-7",
        is_enabled=True,
    )


@pytest.fixture
def good_payload():
    return {
        "preset_slug": "editorial-architect",
        "property_info": {
            "address": "142 Sample St, Yakima WA 98901",
            "price": 725000,
            "beds": 3,
            "baths": 2,
            "sqft": 2400,
            "agent_name": "Jane Realtor",
        },
        "creative_text": {
            "headline": "Quiet light. North exposure.",
            "callouts": ["Quartz kitchen", "Original hardwoods"],
            "value_props": ["Walking distance to downtown."],
        },
        "photo_urls": ["https://cdn.example.com/photo1.jpg"],
    }


def _csrf_authed(user):
    """APIClient force-authenticated with a primed yw_csrf double-submit token."""
    c = APIClient()
    c.force_authenticate(user=user)
    c.get("/api/v1/me/")
    cookie = c.cookies.get("yw_csrf")
    if cookie is not None:
        c.defaults["HTTP_X_CSRFTOKEN"] = cookie.value
    return c


def _approve():
    """A moderation result that lets the task proceed."""
    obj = MagicMock()
    obj.action = "approve"
    obj.reason = "ok"
    return obj


def _block(reason: str = "policy_violation"):
    obj = MagicMock()
    obj.action = "remove"
    obj.reason = reason
    return obj


# ──────────────────────────────────────────────────────────────────────────
# Serializer + view + URL routing
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.usefixtures("_flush_cache")
class TestFlyerGeneratorRunView:
    def test_returns_202_and_queues_task(self, db, user, flyer_tool, good_payload):
        client = _csrf_authed(user)
        with (
            patch("apps.tools.api.views.run_flyer_generator", create=True),
            patch("apps.tools.tasks.run_flyer_generator.delay") as delay,
        ):
            resp = client.post(
                reverse("v1:tools-flyer-generator"),
                data=good_payload,
                format="json",
            )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "queued"
        usage = ToolUsage.objects.get(pk=body["task_id"])
        assert usage.user == user
        assert usage.tool == flyer_tool
        assert usage.input_meta["preset_slug"] == "editorial-architect"
        assert usage.input_meta["property_info"]["address"].startswith("142 Sample")
        delay.assert_called_once_with(usage.pk)

    def test_unauthenticated_rejected(self, db, flyer_tool, good_payload):
        client = APIClient()
        resp = client.post(
            reverse("v1:tools-flyer-generator"),
            data=good_payload,
            format="json",
        )
        assert resp.status_code in (401, 403)

    def test_invalid_preset_rejected(self, db, user, flyer_tool, good_payload):
        client = _csrf_authed(user)
        good_payload["preset_slug"] = "nope"
        resp = client.post(
            reverse("v1:tools-flyer-generator"),
            data=good_payload,
            format="json",
        )
        assert resp.status_code == 400
        assert "preset" in str(resp.json()).lower()

    def test_too_few_photos_rejected(self, db, user, flyer_tool, good_payload):
        client = _csrf_authed(user)
        good_payload["photo_urls"] = []
        resp = client.post(
            reverse("v1:tools-flyer-generator"),
            data=good_payload,
            format="json",
        )
        assert resp.status_code == 400

    def test_too_many_photos_rejected(self, db, user, flyer_tool, good_payload):
        client = _csrf_authed(user)
        good_payload["photo_urls"] = [f"https://cdn.example.com/{i}.jpg" for i in range(6)]
        resp = client.post(
            reverse("v1:tools-flyer-generator"),
            data=good_payload,
            format="json",
        )
        assert resp.status_code == 400

    def test_long_headline_rejected(self, db, user, flyer_tool, good_payload):
        client = _csrf_authed(user)
        good_payload["creative_text"]["headline"] = "x" * 81
        resp = client.post(
            reverse("v1:tools-flyer-generator"),
            data=good_payload,
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.usefixtures("_flush_cache")
class TestFlyerPresetsView:
    def test_lists_all_six_presets(self, db):
        client = APIClient()
        resp = client.get(reverse("public_v1:tools-flyer-presets"))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 6
        slugs = {p["slug"] for p in data}
        assert slugs == {
            "editorial-architect",
            "quiet-luxe",
            "bold-statement",
            "motion-geometry",
            "swiss-grid",
            "italian-editorial",
        }
        first = data[0]
        assert "palette" in first
        assert "fonts" in first
        assert first["palette"]["primary"].startswith("#")


# ──────────────────────────────────────────────────────────────────────────
# Celery task: run_flyer_generator(usage_id)
# ──────────────────────────────────────────────────────────────────────────
@pytest.fixture
def queued_usage(db, user, flyer_tool, good_payload):
    return ToolUsage.objects.create(
        user=user,
        tool=flyer_tool,
        input_meta={
            "preset_slug": good_payload["preset_slug"],
            "property_info": good_payload["property_info"],
            "creative_text": good_payload["creative_text"],
            "photo_urls": good_payload["photo_urls"],
            "color_overrides": {},
            "font_overrides": {},
        },
    )


@pytest.mark.usefixtures("_flush_cache")
class TestRunFlyerGenerator:
    def _import_task(self):
        from apps.tools.tasks import run_flyer_generator

        return run_flyer_generator

    def test_happy_path_chains_to_pdf_render(self, queued_usage):
        task = self._import_task()
        result = FlyerResult(
            html=GOOD_HTML,
            backend_used="claude_cli",
            tokens_in=1234,
            tokens_out=567,
            cost_usd=Decimal("0"),
            meta={"session_id": "abc"},
        )
        with (
            patch("apps.tools.tasks.moderate", return_value=_approve()),
            patch("apps.tools.tasks.gen_flyer", return_value=result),
            patch("apps.tools.tasks.render_flyer_pdf.delay") as render_delay,
        ):
            ret = task.run(usage_id=queued_usage.pk)
        assert ret == "html_generated"
        queued_usage.refresh_from_db()
        # status stays RUNNING; PDF task flips to SUCCESS
        assert queued_usage.status == UsageStatus.RUNNING
        assert queued_usage.output_meta["html"] == GOOD_HTML
        assert queued_usage.output_meta["preset_slug"] == "editorial-architect"
        assert queued_usage.output_meta["backend_used"] == "claude_cli"
        assert queued_usage.tokens_in == 1234
        assert queued_usage.tokens_out == 567
        render_delay.assert_called_once_with(queued_usage.pk)

    def test_input_moderation_blocks(self, queued_usage):
        task = self._import_task()
        with (
            patch("apps.tools.tasks.moderate", return_value=_block("policy_violation")),
            patch("apps.tools.tasks.gen_flyer") as gen,
            patch("apps.tools.tasks.render_flyer_pdf.delay") as render_delay,
        ):
            ret = task.run(usage_id=queued_usage.pk)
        assert ret == "blocked_input"
        queued_usage.refresh_from_db()
        assert queued_usage.status == UsageStatus.BLOCKED
        assert queued_usage.block_reason.startswith("input_moderation")
        gen.assert_not_called()
        render_delay.assert_not_called()

    def test_output_moderation_blocks(self, queued_usage):
        task = self._import_task()
        result = FlyerResult(
            html=GOOD_HTML,
            backend_used="claude_cli",
            cost_usd=Decimal("0"),
        )
        # First moderate() call (input) approves; second (output) removes.
        actions = [_approve(), _block("offensive_text")]
        with (
            patch("apps.tools.tasks.moderate", side_effect=actions),
            patch("apps.tools.tasks.gen_flyer", return_value=result),
            patch("apps.tools.tasks.render_flyer_pdf.delay") as render_delay,
        ):
            ret = task.run(usage_id=queued_usage.pk)
        assert ret == "blocked_output"
        queued_usage.refresh_from_db()
        assert queued_usage.status == UsageStatus.BLOCKED
        assert queued_usage.block_reason.startswith("output_moderation")
        render_delay.assert_not_called()

    def test_unknown_preset_fails(self, db, user, flyer_tool):
        usage = ToolUsage.objects.create(
            user=user,
            tool=flyer_tool,
            input_meta={
                "preset_slug": "nope",
                "property_info": {"address": "x", "price": 1},
                "creative_text": {},
                "photo_urls": ["https://x"],
            },
        )
        task = self._import_task()
        ret = task.run(usage_id=usage.pk)
        assert ret == "failed_unknown_preset"
        usage.refresh_from_db()
        assert usage.status == UsageStatus.FAILED

    def test_missing_usage_returns_missing(self, db):
        task = self._import_task()
        ret = task.run(usage_id=999_999)
        assert ret == "missing"

    def test_backend_error_retries_then_fails(self, queued_usage):
        task = self._import_task()
        with (
            patch("apps.tools.tasks.moderate", return_value=_approve()),
            patch("apps.tools.tasks.gen_flyer", side_effect=FlyerGenerationError("boom")),
            patch("apps.tools.tasks.render_flyer_pdf.delay") as render_delay,
        ):
            ret = task.apply(args=(queued_usage.pk,)).get()
        assert ret == "failed_max_retries"
        queued_usage.refresh_from_db()
        assert queued_usage.status == UsageStatus.FAILED
        assert "boom" in queued_usage.error
        render_delay.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────
# Adversarial property_info / creative_text — the new fixtures from
# prompt_injection_attacks.json must reach moderation and get blocked.
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.usefixtures("_flush_cache")
class TestAdversarialFixtures:
    """Verify the 5 new flyer-specific fixtures are picked up by moderation.

    We don't re-run moderation against Gemini; we just confirm the fixtures
    exist and serialize cleanly into ``property_info`` / ``creative_text``
    inputs the way an attacker would submit them.
    """

    def test_fixture_file_includes_flyer_attacks(self):
        import json
        from pathlib import Path

        path = Path("apps/moderation/tests/fixtures/prompt_injection_attacks.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        names = {f["name"] for f in data}
        assert {
            "flyer_property_info_injection",
            "flyer_creative_headline_jailbreak",
            "flyer_agent_name_override",
            "flyer_callout_schema_redefine",
            "flyer_address_rtl_smuggle",
        } <= names

    def test_pre_flag_catches_flyer_address_rtl_smuggle(self):
        # The fixture content is a JSON string; pre_flag operates on raw text.
        import json
        from pathlib import Path

        from apps.moderation.services.injection_guard import pre_flag

        data = json.loads(
            Path("apps/moderation/tests/fixtures/prompt_injection_attacks.json").read_text(
                encoding="utf-8"
            ),
        )
        item = next(f for f in data if f["name"] == "flyer_address_rtl_smuggle")
        result = pre_flag(item["content"])
        assert result.pre_flagged, "RTL-smuggle attack should be pre-flagged"
