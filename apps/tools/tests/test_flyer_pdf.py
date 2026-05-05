"""Tests for the Playwright HTML→PDF renderer + render_flyer_pdf Celery task.

Service-level tests stub the playwright import at module-resolution time so
they pass even on hosts where Chromium isn't installed (the dev box; only
img-worker has it). The Celery task is tested with the service stubbed.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.core.files.storage import default_storage

from apps.tools.models import Tool, ToolUsage, UsageStatus
from apps.tools.services import flyer_pdf as svc
from apps.tools.services.flyer_pdf import FlyerPDFError, FlyerPDFResult, render
from apps.tools.tasks import render_flyer_pdf


# ──────────────────────────────────────────────────────────────────────────
# Service: render(html)
# ──────────────────────────────────────────────────────────────────────────
class TestRenderArgs:
    def test_empty_html_raises(self):
        with pytest.raises(FlyerPDFError, match="empty HTML"):
            render("")

    def test_whitespace_html_raises(self):
        with pytest.raises(FlyerPDFError, match="empty HTML"):
            render("   \n\t  ")

    def test_unsupported_format_raises(self):
        with pytest.raises(FlyerPDFError, match="unsupported page format"):
            render("<html></html>", page_format="A6")


def _install_fake_playwright(pdf_bytes: bytes = b"%PDF-1.4 fake"):
    """Inject a fake `playwright.sync_api` module that returns canned PDF bytes."""
    fake_pkg = types.ModuleType("playwright")
    fake_sync = types.ModuleType("playwright.sync_api")

    class _FakeError(Exception):
        pass

    page = MagicMock()
    page.pdf.return_value = pdf_bytes
    browser = MagicMock()
    browser.new_page.return_value = page

    p = MagicMock()
    p.chromium.launch.return_value = browser

    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=p)
    cm.__exit__ = MagicMock(return_value=False)

    fake_sync.sync_playwright = MagicMock(return_value=cm)
    fake_sync.Error = _FakeError
    fake_pkg.sync_api = fake_sync
    sys.modules["playwright"] = fake_pkg
    sys.modules["playwright.sync_api"] = fake_sync
    return p, browser, page, _FakeError


@pytest.fixture
def fake_pw():
    saved = {k: sys.modules.get(k) for k in ("playwright", "playwright.sync_api")}
    p, browser, page, err = _install_fake_playwright()
    yield p, browser, page, err
    for k, v in saved.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


class TestRender:
    def test_happy_path_letter(self, fake_pw):
        _, browser, page, _ = fake_pw
        result = render("<!doctype html><html><body>X</body></html>", page_format="Letter")
        assert isinstance(result, FlyerPDFResult)
        assert result.pdf_bytes.startswith(b"%PDF")
        assert result.page_format == "Letter"
        assert result.byte_size > 0
        page.set_content.assert_called_once()
        page.emulate_media.assert_called_once_with(media="print")
        page.pdf.assert_called_once()
        browser.close.assert_called_once()

    def test_supports_a4(self, fake_pw):
        _, _, page, _ = fake_pw
        page.pdf.return_value = b"%PDF-1.4 a4"
        result = render("<!doctype html><html></html>", page_format="A4")
        assert result.page_format == "A4"
        kwargs = page.pdf.call_args.kwargs
        assert kwargs["format"] == "A4"
        assert kwargs["print_background"] is True
        assert kwargs["prefer_css_page_size"] is True

    def test_empty_pdf_raises(self, fake_pw):
        _, _, page, _ = fake_pw
        page.pdf.return_value = b""
        with pytest.raises(FlyerPDFError, match="empty PDF"):
            render("<!doctype html><html></html>")

    def test_playwright_error_wraps(self, fake_pw):
        _, _, page, err = fake_pw
        page.pdf.side_effect = err("page crashed")
        with pytest.raises(FlyerPDFError, match="playwright failure"):
            render("<!doctype html><html></html>")

    def test_missing_playwright_raises_helpful_error(self):
        """If playwright isn't installed at all, raise a helpful FlyerPDFError."""
        saved = {k: sys.modules.get(k) for k in ("playwright", "playwright.sync_api")}
        sys.modules.pop("playwright", None)
        sys.modules.pop("playwright.sync_api", None)
        # Make any attempt to import it raise ImportError.
        sys.modules["playwright"] = None  # type: ignore[assignment]
        try:
            with pytest.raises(FlyerPDFError, match="playwright not installed"):
                render("<!doctype html><html></html>")
        finally:
            sys.modules.pop("playwright", None)
            for k, v in saved.items():
                if v is not None:
                    sys.modules[k] = v


# ──────────────────────────────────────────────────────────────────────────
# Celery task: render_flyer_pdf(usage_id)
# ──────────────────────────────────────────────────────────────────────────
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
def usage_with_html(db, user, flyer_tool):
    return ToolUsage.objects.create(
        user=user,
        tool=flyer_tool,
        status=UsageStatus.RUNNING,
        output_meta={"html": "<!doctype html><html><body>X</body></html>"},
    )


@pytest.mark.usefixtures("_flush_cache")
class TestRenderFlyerPdfTask:
    def test_missing_usage_returns_missing(self, db):
        result = render_flyer_pdf.run(usage_id=999_999)
        assert result == {"status": "missing"}

    def test_no_html_sets_failed(self, db, user, flyer_tool):
        usage = ToolUsage.objects.create(
            user=user,
            tool=flyer_tool,
            status=UsageStatus.RUNNING,
            output_meta={},
        )
        result = render_flyer_pdf.run(usage_id=usage.pk)
        assert result["status"] == "failed"
        assert result["error"] == "no_html"
        usage.refresh_from_db()
        assert usage.status == UsageStatus.FAILED
        assert "no html" in usage.error

    def test_happy_path_saves_pdf_and_updates_usage(self, usage_with_html):
        fake_result = FlyerPDFResult(
            pdf_bytes=b"%PDF-1.4 hello world",
            page_format="Letter",
            byte_size=20,
        )
        with patch.object(svc, "render", return_value=fake_result):
            result = render_flyer_pdf.run(usage_id=usage_with_html.pk)
        assert result["status"] == "success"
        assert result["pdf_bytes"] == 20

        usage_with_html.refresh_from_db()
        assert usage_with_html.status == UsageStatus.SUCCESS
        meta = usage_with_html.output_meta or {}
        assert meta["pdf_path"].startswith("flyers/")
        assert meta["pdf_path"].endswith(".pdf")
        assert meta["pdf_bytes"] == 20
        assert meta["pdf_format"] == "Letter"
        # And the bytes actually landed in storage
        with default_storage.open(meta["pdf_path"], "rb") as f:
            data = f.read()
        assert data == b"%PDF-1.4 hello world"
        try:
            default_storage.delete(meta["pdf_path"])
        except Exception:
            pass

    def test_render_error_retries_then_fails(self, usage_with_html):
        with patch.object(svc, "render", side_effect=FlyerPDFError("boom")):
            result = render_flyer_pdf.apply(args=(usage_with_html.pk,)).get()
        assert result["status"] == "failed"
        assert result["error"] == "max_retries"
        usage_with_html.refresh_from_db()
        assert usage_with_html.status == UsageStatus.FAILED
        assert "boom" in usage_with_html.error

    def test_storage_save_failure_sets_failed(self, usage_with_html):
        fake_result = FlyerPDFResult(
            pdf_bytes=b"%PDF",
            page_format="Letter",
            byte_size=4,
        )
        with (
            patch.object(svc, "render", return_value=fake_result),
            patch.object(default_storage, "save", side_effect=OSError("disk full")),
        ):
            result = render_flyer_pdf.run(usage_id=usage_with_html.pk)
        assert result["status"] == "failed"
        assert result["error"] == "save_failed"
        usage_with_html.refresh_from_db()
        assert usage_with_html.status == UsageStatus.FAILED
        assert "disk full" in usage_with_html.error
