"""OCR-based pre-flight for image uploads.

Wraps tesseract (via pytesseract) to extract any visible text from an image
and screen for prompt-injection keywords before forwarding to the Gemini Pro
vision classifier. Tesseract is pinned in the img-worker container; if it's
unavailable in the runtime, the function fails closed (returns ocr_unavailable
+ allowed=False) so we never silently approve.

This complements `image_input.moderate_image_input` — that function does
size/format probing + a denylist OCR; this one is the pure OCR primitive plus
explicit configurable keyword set.
"""
from __future__ import annotations

import io
import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from django.conf import settings

log = logging.getLogger(__name__)

# Default keyword set — overridable via settings.MODERATION_OCR_KEYWORDS.
DEFAULT_KEYWORDS = (
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(rules|instructions)",
    r"new\s+(rules|instructions|policy)\s*[:=]",
    r"system\s*[:=]\s*you\s+are",
    r"jailbreak",
    r"developer\s+mode",
    r"DAN\s+mode",
    r"override\s+safety",
    r"approve\s+(this|all|everything)",
    r"reveal\s+(internal|system|secret)",
    r"export\s+all\s+(images|data|files)",
    r"act\s+as\s+(admin|moderator|root)",
)


@dataclass
class OCRResult:
    """Outcome of OCR pre-flight.

    `allowed` only goes False when an injection keyword matched OR OCR is
    unavailable (fail-closed posture). Empty text + clean image -> allowed=True.
    """

    allowed: bool
    reason: str
    text: str = ""
    matched_pattern: str = ""
    keywords_used: tuple[str, ...] = field(default_factory=tuple)


def _keywords() -> tuple[str, ...]:
    cfg = getattr(settings, "MODERATION_OCR_KEYWORDS", None)
    if not cfg:
        return DEFAULT_KEYWORDS
    return tuple(cfg)


def extract_text(image_bytes: bytes) -> str | None:
    """Pure OCR pass. Returns None if pytesseract isn't installed.

    Caller decides what to do when None — `screen_image` chooses fail-closed.
    """
    try:
        import pytesseract  # type: ignore[import-not-found]
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError as exc:
        log.warning("OCR dependency missing: %s", exc)
        return None

    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:  # noqa: BLE001
        log.warning("OCR open failed: %s", exc)
        return ""

    try:
        return pytesseract.image_to_string(img) or ""
    except Exception as exc:  # noqa: BLE001
        log.warning("OCR run failed: %s", exc)
        return ""


def screen_image(
    image_bytes: bytes, *, keywords: Iterable[str] | None = None
) -> OCRResult:
    """Pre-flight an image. Fail-closed on missing OCR or matched keyword."""
    if not image_bytes:
        return OCRResult(allowed=False, reason="empty_image")

    kw = tuple(keywords) if keywords else _keywords()
    text = extract_text(image_bytes)

    if text is None:
        return OCRResult(
            allowed=False,
            reason="ocr_unavailable",
            keywords_used=kw,
        )
    if not text.strip():
        return OCRResult(
            allowed=True, reason="no_text", keywords_used=kw
        )

    lowered = text.lower()
    for pattern in kw:
        if re.search(pattern, lowered, re.IGNORECASE):
            return OCRResult(
                allowed=False,
                reason="injection_keyword",
                text=text[:500],
                matched_pattern=pattern,
                keywords_used=kw,
            )

    return OCRResult(
        allowed=True, reason="clean", text=text[:500], keywords_used=kw
    )
