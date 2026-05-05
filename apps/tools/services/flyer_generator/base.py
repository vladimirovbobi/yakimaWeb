"""Flyer generator backend contract.

All backends implement ``FlyerBackend.generate(...)`` and return a
``FlyerResult`` or raise ``FlyerGenerationError`` on failure.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..flyer_presets import FlyerPreset


class FlyerGenerationError(Exception):
    """Transient or hard failure during flyer HTML generation.

    Celery task wraps generate() and uses this to decide retry vs. fail.
    """


@dataclass
class FlyerResult:
    """Backend output. Caller persists html + tokens + cost on the ToolUsage row."""

    html: str
    backend_used: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: Decimal = field(default_factory=lambda: Decimal("0"))
    meta: dict[str, Any] = field(default_factory=dict)


class FlyerBackend(ABC):
    """Abstract backend. Subclasses implement ``generate``."""

    name: str = "abstract"

    @abstractmethod
    def generate(
        self,
        *,
        preset: FlyerPreset,
        property_info: dict[str, Any],
        creative_text: dict[str, Any],
        photo_urls: list[str],
        color_overrides: dict[str, str],
        font_overrides: dict[str, str],
    ) -> FlyerResult: ...
