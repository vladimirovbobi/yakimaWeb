"""SEC-018: PIL.Image.MAX_IMAGE_PIXELS cap is engaged at app import time.

We don't try to fabricate a true zip-bomb PNG (that's what Pillow's own
DecompressionBombError handler is for). Instead we assert two contracts:

  1. The cap on Pillow's class attribute is exactly the value we set, which
     means importing apps.core (or apps.core.imaging) ran the side-effect.
  2. The defense fires for normal callsites: ImageUploadView's `_probe_image`
     converts DecompressionBombError into a clean ValidationError.

That second contract is the one that matters at runtime — it's what keeps
the upload path from 500-ing on a malicious payload.
"""
from __future__ import annotations

import io
from unittest.mock import patch

import pytest
from PIL import Image

from apps.core import imaging
from apps.core.api.uploads import _probe_image


def test_max_image_pixels_clamp_applied():
    """Importing apps.core.imaging mutates Pillow's global pixel cap."""
    assert Image.MAX_IMAGE_PIXELS == imaging.SAFE_MAX_IMAGE_PIXELS == 50_000_000


def test_normal_image_passes_probe():
    """Sanity: a tiny well-formed PNG passes the probe."""
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), (255, 0, 0)).save(buf, format="PNG")
    detected = _probe_image(buf.getvalue())
    assert detected == "image/png"


def test_decompression_bomb_raises_validation_error():
    """When Pillow flags the bomb, the upload probe surfaces a clean 400."""
    from rest_framework.exceptions import ValidationError

    # Image is imported lazily inside _probe_image; patch the canonical PIL
    # symbol so the lazy import resolves to our mock.
    with patch("PIL.Image.open") as mock_open:
        mock_open.side_effect = Image.DecompressionBombError("bomb")

        with pytest.raises(ValidationError) as exc:
            _probe_image(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)

        # ValidationError surfaces under .detail
        msg = str(exc.value.detail).lower()
        assert "too large" in msg or "process safely" in msg


def test_image_input_moderation_rejects_bomb():
    """The AI-tool image preflight returns allowed=False on a bomb."""
    from apps.moderation.services.image_input import moderate_image_input

    with patch("PIL.Image.open") as mock_open:
        mock_open.side_effect = Image.DecompressionBombError("bomb")

        decision = moderate_image_input(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
        assert decision.allowed is False
        assert decision.reason == "decompression_bomb"
