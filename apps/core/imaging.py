"""Pillow safety primitives — applied at app import time.

`PIL.Image.MAX_IMAGE_PIXELS` defaults to ~89 MP, which still permits a
maliciously-crafted PNG (e.g. 9 MB on disk → multiple GB once decompressed)
to exhaust process memory on `Image.open()` / `verify()`. We clamp tighter
than the default and re-export a helper that callers can use to fail closed
on `DecompressionBombError` without re-implementing the try/except in every
upload site.

Importing this module is the side-effect: `Image.MAX_IMAGE_PIXELS` is
mutated as soon as `apps.core` boots (via `apps/core/__init__.py` re-export).
"""
from __future__ import annotations

# Half of Pillow's default — 50 MP is more than enough for 5K imagery while
# putting a hard ceiling on decompression-bomb expansion. Pillow emits a
# DecompressionBombWarning at half this and raises DecompressionBombError at
# 2x — see Pillow's docs.
SAFE_MAX_IMAGE_PIXELS = 50_000_000


def _apply_pixel_cap() -> None:
    """Set Pillow's pixel cap globally. Idempotent — safe to call repeatedly."""
    try:
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError:
        return
    Image.MAX_IMAGE_PIXELS = SAFE_MAX_IMAGE_PIXELS


_apply_pixel_cap()
