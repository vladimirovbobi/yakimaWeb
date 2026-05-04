"""Image-input moderation pre-flight for AI tools.

Mirrors the fail-closed posture of `pipeline.moderate` for text but for image
bytes. Composed from:

  1. Pillow probe — format + dimensions, hard cap on side length.
  2. OCR keyword screen via `image_ocr.screen_image` (delegates to pytesseract
     when available; fails closed when not).

Returns an ImageInputDecision; callers inspect `.allowed`. When `.allowed` is
False, callers MUST refuse to dispatch the Gemini call.

This module is the entry point for *AI tool inputs* (e.g. furniture remover
uploads). For UGC image moderation see ``image_moderation.moderate_image``,
which adds a Gemini-Pro vision pass.
"""
from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass

log = logging.getLogger(__name__)

# Phrases we never want to find inside an uploaded photo. These are hand-picked
# from the prompt-injection literature; the regex is case-insensitive and
# whitespace-loose so OCR noise still matches.
INJECTION_KEYWORDS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(rules|instructions)",
    r"new\s+(rules|instructions|policy)\s*[:=]",
    r"system\s*[:=]\s*you\s+are",
    r"jailbreak",
    r"developer\s+mode",
    r"show\s+me\s+(other|all)\s+users?'?\s+photos?",
    r"reveal\s+(internal|system|secret)",
    r"export\s+all\s+(images|data|files)",
    r"override\s+safety",
    r"DAN\s+mode",
]

MAX_PIXELS_PER_SIDE = 4096


@dataclass
class ImageInputDecision:
    allowed: bool
    reason: str = ""
    width: int = 0
    height: int = 0
    detected_text: str = ""


def moderate_image_input(image_bytes: bytes) -> ImageInputDecision:
    """Pre-flight an image upload for known prompt-injection signals.

    Always returns a decision. Never raises. Fail-closed: any failure to read
    the image returns `allowed=False` so the upstream task records a BLOCKED
    ToolUsage instead of paying for a Gemini call on garbage.
    """
    if not image_bytes:
        return ImageInputDecision(allowed=False, reason="empty_image")

    try:
        from PIL import Image
    except ImportError:
        log.error("Pillow missing; refusing image moderation")
        return ImageInputDecision(allowed=False, reason="pillow_missing")

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        # verify() invalidates the file pointer; re-open for size probe.
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
    except Exception as exc:  # noqa: BLE001
        return ImageInputDecision(
            allowed=False, reason=f"image_unreadable:{type(exc).__name__}"
        )

    if width <= 0 or height <= 0:
        return ImageInputDecision(allowed=False, reason="zero_dimension")
    if width > MAX_PIXELS_PER_SIDE or height > MAX_PIXELS_PER_SIDE:
        return ImageInputDecision(
            allowed=False,
            reason=f"oversize:{width}x{height}",
            width=width, height=height,
        )

    detected_text = _ocr_text(image_bytes)
    if detected_text:
        lowered = detected_text.lower()
        for pattern in INJECTION_KEYWORDS:
            if re.search(pattern, lowered, re.IGNORECASE):
                return ImageInputDecision(
                    allowed=False,
                    reason="injection_text_detected",
                    width=width, height=height,
                    detected_text=detected_text[:500],
                )

    return ImageInputDecision(
        allowed=True, reason="ok",
        width=width, height=height,
        detected_text=detected_text[:500] if detected_text else "",
    )


def _ocr_text(image_bytes: bytes) -> str:
    """Best-effort OCR. Returns empty string if pytesseract isn't installed.

    Kept tiny + monkeypatchable; `image_ocr.extract_text` is the canonical
    primitive but we don't take its fail-closed semantics here — for AI-tool
    inputs we prefer to *allow* a clean photo even if OCR is unavailable, and
    rely on the inpaint prompt's own untrusted-data handling.
    """
    try:
        import pytesseract  # type: ignore[import-not-found]
    except ImportError:
        log.debug("pytesseract not installed; skipping image OCR")
        return ""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img) or ""
    except Exception as exc:  # noqa: BLE001
        log.warning("OCR failed: %s", exc)
        return ""
