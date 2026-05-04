"""Celery tasks: every AI call goes through here. Never sync from views."""
import logging
import time

from celery import shared_task
from django.core.files.storage import default_storage

from apps.moderation.services.pipeline import moderate

from .models import ToolUsage, UsageStatus
from .services.description_writer import generate as gen_description
from .services.furniture_remover import (
    FurnitureRemoverError,
    run as run_furniture,
)
from .services.spend_cap import SpendCapExceeded, check_budget, record_spend_usd

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────
# Description writer (Sprint 2)
# ──────────────────────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=2, retry_backoff=True)
def run_description_writer(self, usage_id: int) -> str:
    """Pull ToolUsage row, run moderation on input, call Gemini, persist output."""
    usage = ToolUsage.objects.select_related("tool", "user").filter(pk=usage_id).first()
    if usage is None:
        return "missing"

    facts = usage.input_meta.get("property_facts", "").strip()

    # Layer 1: moderate input BEFORE the LLM call (defense vs prompt-injection in tool input)
    mod_result = moderate(facts, target=None, context="tool_input")
    if mod_result.action != "approve":
        usage.status = UsageStatus.BLOCKED
        usage.block_reason = f"input_moderation:{mod_result.reason[:32]}"
        usage.error = "Input flagged by moderation."
        usage.save(update_fields=["status", "block_reason", "error", "updated_at"])
        return "blocked_input"

    # Spend cap pre-flight: bail out cheaply if today's budget is gone.
    try:
        check_budget()
    except SpendCapExceeded as exc:
        usage.status = UsageStatus.BLOCKED
        usage.block_reason = "spend_cap_exceeded"
        usage.error = str(exc)[:500]
        usage.cost_usd = 0
        usage.save(update_fields=["status", "block_reason", "error", "cost_usd", "updated_at"])
        return "blocked_spend_cap"

    usage.status = UsageStatus.RUNNING
    usage.save(update_fields=["status", "updated_at"])
    t0 = time.time()
    try:
        result = gen_description(facts)
    except Exception as e:  # noqa: BLE001
        log.exception("description_writer failed")
        usage.status = UsageStatus.FAILED
        usage.error = str(e)[:500]
        usage.duration_ms = int((time.time() - t0) * 1000)
        usage.save(update_fields=["status", "error", "duration_ms", "updated_at"])
        raise self.retry(exc=e)

    # Layer 2: moderate the OUTPUT before persisting
    out_mod = moderate(result.text, target=None, context="tool_output")
    if out_mod.action == "remove":
        usage.status = UsageStatus.BLOCKED
        usage.block_reason = f"output_moderation:{out_mod.reason[:32]}"
        usage.save(update_fields=["status", "block_reason", "updated_at"])
        return "blocked_output"

    usage.status = UsageStatus.SUCCESS
    usage.tokens_in = result.tokens_in
    usage.tokens_out = result.tokens_out
    usage.output_meta = {"text": result.text, "length": len(result.text)}
    # Approximate Gemini Pro pricing — refine in Phase 8
    usage.cost_usd = round((result.tokens_in / 1e6 * 1.25) + (result.tokens_out / 1e6 * 5.0), 4)
    usage.duration_ms = int((time.time() - t0) * 1000)
    usage.save()
    # Increment today's running cost so subsequent runs see the latest total.
    try:
        record_spend_usd(float(usage.cost_usd))
    except Exception:  # noqa: BLE001
        log.exception("spend_cap.record_spend_usd failed (non-fatal)")
    return "success"


# ──────────────────────────────────────────────────────────────────────────
# Furniture remover (Sprint 3)
# ──────────────────────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=3, queue="images")
def run_furniture_remover(self, usage_id: int) -> dict:
    """Image-queue task — runs on the dedicated img-worker container.

    Reads the staged input image from default_storage (path stored on the
    ToolUsage row), then delegates to the service which performs spend-cap +
    image-moderation pre-flight and the two Gemini calls. Retries with
    exponential backoff on transient errors.
    """
    usage = ToolUsage.objects.select_related("tool", "user").filter(pk=usage_id).first()
    if usage is None:
        return {"status": "missing"}

    image_path = (usage.input_meta or {}).get("upload_path")
    if not image_path:
        usage.status = UsageStatus.FAILED
        usage.error = "no upload path on ToolUsage"
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "no_upload_path"}

    try:
        with default_storage.open(image_path, "rb") as f:
            image_bytes = f.read()
    except Exception as exc:  # noqa: BLE001
        log.exception("failed to read uploaded image")
        usage.status = UsageStatus.FAILED
        usage.error = f"read_failed:{exc}"[:500]
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "read_failed"}

    try:
        result = run_furniture(usage, image_bytes)
    except SpendCapExceeded as exc:
        usage.status = UsageStatus.BLOCKED
        usage.block_reason = "spend_cap_exceeded"
        usage.error = str(exc)[:500]
        usage.save(update_fields=["status", "block_reason", "error", "updated_at"])
        return {"status": "blocked", "block_reason": "spend_cap_exceeded"}
    except FurnitureRemoverError as exc:
        log.warning("furniture remover transient error: %s", exc)
        try:
            countdown = 30 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        except self.MaxRetriesExceededError:
            usage.status = UsageStatus.FAILED
            usage.error = str(exc)[:500]
            usage.save(update_fields=["status", "error", "updated_at"])
            return {"status": "failed", "error": "max_retries"}
    except Exception as exc:  # noqa: BLE001
        log.exception("furniture remover unexpected error")
        usage.status = UsageStatus.FAILED
        usage.error = str(exc)[:500]
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "unhandled"}

    return {
        "status": result.status,
        "input_url": result.input_url,
        "output_url": result.output_url,
        "tokens_in": result.tokens_in,
        "tokens_out": result.tokens_out,
        "cost_usd": float(result.cost_usd),
        "runtime_ms": result.runtime_ms,
        "block_reason": result.block_reason,
        "error": result.error,
    }
