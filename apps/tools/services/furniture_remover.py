"""Furniture remover — Gemini 2.5 Flash Image inpaint.

Port reference: virtual-staging-app project (two-call design).
This stub returns the original image until Phase 3 wires Gemini Image API.
"""
import io
import logging
from dataclasses import dataclass

from django.conf import settings

log = logging.getLogger(__name__)


@dataclass
class FurnitureResult:
    output_bytes: bytes
    width: int
    height: int
    tokens_in: int
    tokens_out: int
    error: str = ""


def remove_furniture(image_bytes: bytes, *, mime: str = "image/jpeg") -> FurnitureResult:
    """Empty a room by inpainting furniture out. Stub for Phase 3 implementation."""
    if not settings.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY missing; furniture remover returning stub")
        return FurnitureResult(
            output_bytes=image_bytes, width=0, height=0,
            tokens_in=0, tokens_out=0,
            error="GEMINI_API_KEY not configured — stub mode",
        )

    # PHASE 3 IMPLEMENTATION:
    # 1. Probe image dimensions via Pillow
    # 2. Two-call pattern from virtual-staging-app:
    #    a. First call: Gemini Pro identifies furniture regions → JSON masks
    #    b. Second call: Gemini Image inpaints with empty-room target
    # 3. Return PNG bytes
    # See: C:\Users\vladi\OneDrive\Desktop\Projects\virtual-staging-app
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        return FurnitureResult(
            output_bytes=image_bytes, width=img.width, height=img.height,
            tokens_in=0, tokens_out=0,
            error="(Phase 3 stub — port from virtual-staging-app)",
        )
    except Exception as e:  # noqa: BLE001
        return FurnitureResult(
            output_bytes=image_bytes, width=0, height=0,
            tokens_in=0, tokens_out=0,
            error=f"image probe failed: {e}",
        )
