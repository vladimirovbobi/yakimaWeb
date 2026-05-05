"""Future commercial backend — Anthropic API direct (Claude Sonnet 4.6).

Placeholder for the higher-quality / higher-cost commercial path. Selected
via ``settings.FLYER_BACKEND="anthropic_api"`` once an Anthropic API key is
provisioned (separate from the Claude Code Max subscription).

Implementation outline (when this becomes real):
- ``anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY).messages.create(...)``
- Inline huashu-design directive in the system message
- Use prompt caching on the system + preset blocks (they're stable across runs)
- Return FlyerResult with realized tokens + cost
"""

from __future__ import annotations

from typing import Any

from ..base import FlyerBackend, FlyerGenerationError, FlyerResult


class AnthropicAPIBackend(FlyerBackend):
    name = "anthropic_api"

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
            "anthropic_api backend stubbed — provision ANTHROPIC_API_KEY first"
        )
