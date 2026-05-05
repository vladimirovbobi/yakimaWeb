"""Prototype backend — subprocess to local ``claude`` CLI with /huashu-design.

Wired in commit 2 of the flyer-generator phase. This file is a scaffold so
the dispatcher in __init__.py can import the class even before the subprocess
plumbing exists.

Architecture (full impl lands in commit 2):
- Compose a prompt: preset.prompt_directive + property facts + creative copy
  + an explicit output contract ("single self-contained HTML, US Letter
  portrait, no <script>")
- Invoke ``claude -p <prompt> --output-format json --skill huashu-design``
  as a subprocess inside the img-worker container, with ~/.claude mounted
  read-write so token refresh persists
- Parse JSON output, extract HTML, validate (no <script>/<iframe>/on*=)
- Return FlyerResult(html=..., backend_used="claude_cli", cost_usd=0)

Token refresh + keep-alive are out-of-band concerns (commit 7's PowerShell
scripts handle them). This backend assumes the CLI is reachable and signed-in.
"""

from __future__ import annotations

from typing import Any

from ..base import FlyerBackend, FlyerGenerationError, FlyerResult


class ClaudeCLIBackend(FlyerBackend):
    name = "claude_cli"

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
        raise FlyerGenerationError("claude_cli backend not yet implemented — wired in commit 2")
