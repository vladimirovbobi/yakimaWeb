"""Future commercial backend — Gemini 2.5 Pro via google-genai SDK.

Placeholder. Switching ``settings.FLYER_BACKEND`` to ``"gemini"`` is the only
production-readiness step required to remove the keep-alive / Claude CLI /
~/.claude mount infrastructure once realtors are paying.

Implementation outline (when this becomes real):
- Reuse ``genai.Client(api_key=settings.GEMINI_API_KEY)`` exactly like
  ``apps/tools/services/description_writer.py``.
- Same prompt shape as claude_cli but with the huashu-design directive
  inlined verbatim in the system instruction (Gemini has no skill mechanism).
- Return FlyerResult with realized tokens + cost (Pro rates).
"""

from __future__ import annotations

from typing import Any

from ..base import FlyerBackend, FlyerGenerationError, FlyerResult


class GeminiBackend(FlyerBackend):
    name = "gemini"

    def generate(
        self,
        *,
        preset,
        property_info: dict[str, Any],
        creative_text: dict[str, Any],
        photo_urls: list[str],
        color_overrides: dict[str, str],
        font_overrides: dict[str, str],
    ) -> FlyerResult:
        raise FlyerGenerationError(
            "gemini backend stubbed — wire up before commercializing the flyer tool"
        )
