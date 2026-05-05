"""Flyer generator — pluggable backend dispatch.

Public surface:
    generate(preset, property_info, creative_text, photo_urls, ...) -> FlyerResult

The active backend is selected at call time via ``settings.FLYER_BACKEND``.
Default ``"claude_cli"`` is the prototype path (subprocess to local ``claude``
CLI invoking the ``/huashu-design`` skill). Production swap is a one-line env
change to ``"gemini"`` or ``"anthropic_api"`` once those backends are filled.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

from .base import (
    FlyerBackend,
    FlyerGenerationError,
    FlyerResult,
)

log = logging.getLogger(__name__)

_BACKEND_CACHE: dict[str, FlyerBackend] = {}


def _load_backend(name: str) -> FlyerBackend:
    """Late-import the configured backend so missing optional deps don't break startup."""
    if name == "claude_cli":
        from .backends.claude_cli import ClaudeCLIBackend

        return ClaudeCLIBackend()
    if name == "gemini":
        from .backends.gemini import GeminiBackend

        return GeminiBackend()
    if name == "anthropic_api":
        from .backends.anthropic_api import AnthropicAPIBackend

        return AnthropicAPIBackend()
    raise FlyerGenerationError(f"unknown FLYER_BACKEND: {name!r}")


def get_active_backend() -> FlyerBackend:
    name = getattr(settings, "FLYER_BACKEND", "claude_cli") or "claude_cli"
    if name not in _BACKEND_CACHE:
        _BACKEND_CACHE[name] = _load_backend(name)
    return _BACKEND_CACHE[name]


def generate(
    *,
    preset_slug: str,
    property_info: dict[str, Any],
    creative_text: dict[str, Any],
    photo_urls: list[str],
    color_overrides: dict[str, str] | None = None,
    font_overrides: dict[str, str] | None = None,
) -> FlyerResult:
    """Dispatch to the active backend. Raises FlyerGenerationError on failure."""
    from ..flyer_presets import get_preset

    preset = get_preset(preset_slug)
    if preset is None:
        raise FlyerGenerationError(f"unknown preset_slug: {preset_slug!r}")

    backend = get_active_backend()
    log.info("flyer_generator: backend=%s preset=%s", backend.name, preset.slug)
    return backend.generate(
        preset=preset,
        property_info=property_info,
        creative_text=creative_text,
        photo_urls=photo_urls,
        color_overrides=color_overrides or {},
        font_overrides=font_overrides or {},
    )


__all__ = [
    "FlyerBackend",
    "FlyerGenerationError",
    "FlyerResult",
    "generate",
    "get_active_backend",
]
