"""SEC-018: confirm Pillow's MAX_IMAGE_PIXELS clamp surfaces as a clean
BLOCKED decision instead of an unhandled OOM/500.

Strategy: monkeypatch `Image.MAX_IMAGE_PIXELS` to a small ceiling and feed in
an image whose pixel count exceeds it. Pillow raises `DecompressionBombError`
on the next decode call, which `moderate_image_input` must turn into
`allowed=False, reason="decompression_bomb"`.
"""
from __future__ import annotations

import io

import pytest

from apps.moderation.services.image_input import moderate_image_input


def _bomb_bytes(side: int) -> bytes:
    """Render a `side x side` PNG and return its bytes."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")
    buf = io.BytesIO()
    Image.new("RGB", (side, side), (255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


class TestDecompressionBombGuard:
    def test_pixel_cap_clamp_is_applied(self):
        from PIL import Image
        # apps.core.imaging is imported at app start; this assertion proves it.
        assert Image.MAX_IMAGE_PIXELS == 50_000_000

    def test_bomb_returns_blocked_decision(self, monkeypatch):
        from PIL import Image

        # Simulate a tighter bomb threshold so we don't actually allocate
        # gigabytes of RAM in the test. 100x100 = 10_000 pixels; cap to 100 →
        # any 11x11+ image is now a "bomb" from Pillow's POV.
        monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)
        decision = moderate_image_input(_bomb_bytes(64))
        assert decision.allowed is False
        assert decision.reason == "decompression_bomb"
