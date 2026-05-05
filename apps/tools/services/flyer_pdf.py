"""Headless-Chromium HTML→PDF renderer for the flyer generator.

Runs inside the dedicated img-worker container (the only worker with Playwright
+ Chromium installed). Pure sync; the Celery task wraps it.

Usage:

    result = render(html, page_format="Letter")
    bytes_ = result.pdf_bytes
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT_MS = 30_000  # 30s ceiling for content load
SUPPORTED_FORMATS = ("Letter", "A4", "Legal", "Tabloid")


class FlyerPDFError(Exception):
    """Raised when Playwright fails or HTML can't be rendered."""


@dataclass
class FlyerPDFResult:
    pdf_bytes: bytes
    page_format: str
    byte_size: int


def render(html: str, *, page_format: str = "Letter") -> FlyerPDFResult:
    """Render the given HTML to a PDF byte string. Raises FlyerPDFError on failure.

    Late-imports playwright so the module is importable in environments where
    Chromium isn't installed (e.g., dev machines running just the API tests).
    """
    if not html or not html.strip():
        raise FlyerPDFError("empty HTML — nothing to render")
    if page_format not in SUPPORTED_FORMATS:
        raise FlyerPDFError(f"unsupported page format: {page_format!r}")

    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise FlyerPDFError(
            "playwright not installed — `pip install playwright && playwright install chromium`"
        ) from exc

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                page.set_default_timeout(DEFAULT_TIMEOUT_MS)
                page.set_content(html, wait_until="networkidle")
                page.emulate_media(media="print")
                pdf = page.pdf(
                    format=page_format,
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise FlyerPDFError(f"playwright failure: {exc}") from exc

    if not pdf:
        raise FlyerPDFError("playwright returned empty PDF")

    return FlyerPDFResult(
        pdf_bytes=pdf,
        page_format=page_format,
        byte_size=len(pdf),
    )
