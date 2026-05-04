"""Server-Sent Events helper for tool task status streaming.

Frontend opens an EventSource at ``/api/v1/streams/tools/<task_id>/``. We
re-read the ToolUsage row every ``POLL_SECONDS`` and push a JSON envelope as a
``message`` event. Connection closes when the row reaches a terminal status
(success / failed / blocked) or when ``MAX_DURATION_SECONDS`` elapses.

Why polling and not Channels: Phase 3 keeps the deployment a single Django
process behind Caddy. Real WebSockets land in Phase 6 with the operator
dashboard. The cost of a one-row select every 2s is fine for the few dozen
concurrent runs we expect at 10K MAU.
"""
from __future__ import annotations

import json
import logging
import time
from collections.abc import Generator

from django.utils import timezone

from ..models import ToolUsage

log = logging.getLogger(__name__)

POLL_SECONDS = 2
MAX_DURATION_SECONDS = 5 * 60
TERMINAL_STATUSES = {"success", "failed", "blocked"}


def stream_task_status(usage_id: int, *, owner_id: int) -> Generator[bytes, None, None]:
    """Yield SSE frames until the run finishes or we hit the timeout."""
    deadline = time.monotonic() + MAX_DURATION_SECONDS
    last_payload: str | None = None
    yield b": connected\n\n"

    while time.monotonic() < deadline:
        usage = (ToolUsage.objects
                 .filter(pk=usage_id, user_id=owner_id)
                 .select_related("tool")
                 .first())
        if usage is None:
            yield _frame({"error": "task_not_found"})
            return

        payload = _build_payload(usage)
        as_json = json.dumps(payload, default=str)
        if as_json != last_payload:
            yield _frame(payload)
            last_payload = as_json
        if usage.status in TERMINAL_STATUSES:
            yield _frame({**payload, "final": True})
            return
        time.sleep(POLL_SECONDS)

    yield _frame({"error": "timeout", "final": True})


def _build_payload(usage: ToolUsage) -> dict:
    output = usage.output_meta or {}
    return {
        "task_id": usage.pk,
        "status": usage.status,
        "progress": _progress_for(usage.status),
        "result_url": output.get("url"),
        "input_url": output.get("input_url") or (usage.input_meta or {}).get("image_url"),
        "error": usage.error or None,
        "block_reason": usage.block_reason or None,
        "cost_usd": float(usage.cost_usd or 0),
        "runtime_ms": usage.duration_ms or 0,
        "checked_at": timezone.now().isoformat(),
    }


def _progress_for(status: str) -> int:
    return {
        "queued": 5,
        "running": 55,
        "success": 100,
        "failed": 100,
        "blocked": 100,
    }.get(status, 0)


def _frame(payload: dict) -> bytes:
    return f"data: {json.dumps(payload, default=str)}\n\n".encode()
