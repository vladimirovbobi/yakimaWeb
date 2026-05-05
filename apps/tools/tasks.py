"""Celery tasks: every AI call goes through here. Never sync from views."""

import logging
import time
import uuid

from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.moderation.services.pipeline import moderate

from .models import ToolUsage, UsageStatus
from .services.description_writer import generate as gen_description
from .services.flyer_pdf import FlyerPDFError
from .services.flyer_pdf import render as render_flyer
from .services.furniture_remover import (
    FurnitureRemoverError,
)
from .services.furniture_remover import (
    run as run_furniture,
)
from .services.image_compressor import (
    ImageCompressorError,
    UnsupportedFormat,
)
from .services.image_compressor import (
    compress as compress_image,
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
    except Exception as e:
        log.exception("description_writer failed")
        usage.status = UsageStatus.FAILED
        usage.error = str(e)[:500]
        usage.duration_ms = int((time.time() - t0) * 1000)
        usage.save(update_fields=["status", "error", "duration_ms", "updated_at"])
        raise self.retry(exc=e) from e

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
    except Exception:
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
    except Exception as exc:
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
            countdown = 30 * (2**self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        except self.MaxRetriesExceededError:
            usage.status = UsageStatus.FAILED
            usage.error = str(exc)[:500]
            usage.save(update_fields=["status", "error", "updated_at"])
            return {"status": "failed", "error": "max_retries"}
    except Exception as exc:
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


# ──────────────────────────────────────────────────────────────────────────
# Image compressor (Sprint 1.5) — runs on the dedicated img-worker queue
# ──────────────────────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=2, queue="images")
def run_image_compressor(self, usage_id: int) -> dict:
    """Read the staged upload, run lossless compression, persist output.

    Pure local CPU. No spend cap (no $ per run), no Gemini call. We still
    rate-limit at the view boundary via the existing per-tool quota.
    """
    usage = ToolUsage.objects.select_related("tool", "user").filter(pk=usage_id).first()
    if usage is None:
        return {"status": "missing"}

    image_path = (usage.input_meta or {}).get("upload_path")
    filename = (usage.input_meta or {}).get("filename") or "image.jpg"
    if not image_path:
        usage.status = UsageStatus.FAILED
        usage.error = "no upload path on ToolUsage"
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "no_upload_path"}

    try:
        with default_storage.open(image_path, "rb") as f:
            payload = f.read()
    except Exception as exc:
        log.exception("image_compressor: read failed")
        usage.status = UsageStatus.FAILED
        usage.error = f"read_failed:{exc}"[:500]
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "read_failed"}

    usage.status = UsageStatus.RUNNING
    usage.save(update_fields=["status", "updated_at"])

    t0 = time.time()
    try:
        result = compress_image(payload, filename)
    except UnsupportedFormat as exc:
        usage.status = UsageStatus.BLOCKED
        usage.block_reason = "unsupported_format"
        usage.error = str(exc)[:500]
        usage.save(update_fields=["status", "block_reason", "error", "updated_at"])
        return {"status": "blocked", "block_reason": "unsupported_format"}
    except ImageCompressorError as exc:
        log.warning("image_compressor: transient error: %s", exc)
        try:
            countdown = 15 * (2**self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        except self.MaxRetriesExceededError:
            usage.status = UsageStatus.FAILED
            usage.error = str(exc)[:500]
            usage.save(update_fields=["status", "error", "updated_at"])
            return {"status": "failed", "error": "max_retries"}
    except Exception as exc:
        log.exception("image_compressor: unexpected error")
        usage.status = UsageStatus.FAILED
        usage.error = str(exc)[:500]
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "unhandled"}

    output_suffix = uuid.uuid4().hex[:8]
    output_path = (
        f"tools/image-compressor/{usage.user_id}/results/{output_suffix}-{result.output_filename}"
    )
    try:
        default_storage.save(output_path, ContentFile(result.output_bytes))
    except Exception as exc:
        log.exception("image_compressor: save failed")
        usage.status = UsageStatus.FAILED
        usage.error = f"save_failed:{exc}"[:500]
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "save_failed"}

    try:
        output_url = default_storage.url(output_path)
    except Exception:  # noqa: BLE001
        output_url = None
    try:
        input_url = default_storage.url(image_path)
    except Exception:  # noqa: BLE001
        input_url = None

    usage.status = UsageStatus.SUCCESS
    usage.cost_usd = 0
    usage.duration_ms = int((time.time() - t0) * 1000)
    usage.output_meta = {
        "filename": result.output_filename,
        "format": result.output_format,
        "input_size": result.input_size,
        "output_size": result.output_size,
        "bytes_saved": result.bytes_saved,
        "percent_saved": result.percent_saved,
        "width": result.width,
        "height": result.height,
        "method": result.method,
        "url": output_url,
        "output_path": output_path,
        "input_url": input_url,
    }
    usage.save()

    return {
        "status": "success",
        "input_url": input_url,
        "output_url": output_url,
        "input_size": result.input_size,
        "output_size": result.output_size,
        "percent_saved": result.percent_saved,
        "format": result.output_format,
        "runtime_ms": usage.duration_ms,
    }


# ──────────────────────────────────────────────────────────────────────────
# Flyer generator — PDF render stage (Sprint 2)
# ──────────────────────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=2, queue="images")
def render_flyer_pdf(self, usage_id: int) -> dict:
    """Render the HTML on a ToolUsage row into a PDF and persist it.

    Reads ``output_meta["html"]`` (set by ``run_flyer_generator`` in commit 4),
    runs Playwright Chromium on the dedicated img-worker, saves the bytes to
    default_storage at ``flyers/{user_id}/{usage_id}.pdf``, and stamps
    ``output_meta["pdf_url"]`` + ``status=SUCCESS``.

    Retries with an exponential countdown on transient Playwright failures.
    """
    usage = ToolUsage.objects.select_related("tool", "user").filter(pk=usage_id).first()
    if usage is None:
        return {"status": "missing"}

    html = (usage.output_meta or {}).get("html") or ""
    if not html:
        usage.status = UsageStatus.FAILED
        usage.error = "no html on ToolUsage.output_meta"
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "no_html"}

    t0 = time.time()
    try:
        result = render_flyer(html, page_format="Letter")
    except FlyerPDFError as exc:
        log.warning("render_flyer_pdf transient: %s", exc)
        try:
            countdown = 20 * (2**self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        except self.MaxRetriesExceededError:
            usage.status = UsageStatus.FAILED
            usage.error = str(exc)[:500]
            usage.save(update_fields=["status", "error", "updated_at"])
            return {"status": "failed", "error": "max_retries"}
    except Exception as exc:
        log.exception("render_flyer_pdf unexpected error")
        usage.status = UsageStatus.FAILED
        usage.error = str(exc)[:500]
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "unhandled"}

    output_path = f"flyers/{usage.user_id}/{usage.pk}.pdf"
    try:
        saved = default_storage.save(output_path, ContentFile(result.pdf_bytes))
    except Exception as exc:
        log.exception("render_flyer_pdf: storage save failed")
        usage.status = UsageStatus.FAILED
        usage.error = f"save_failed:{exc}"[:500]
        usage.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": "save_failed"}

    try:
        pdf_url = default_storage.url(saved)
    except Exception:  # noqa: BLE001
        pdf_url = None

    usage.status = UsageStatus.SUCCESS
    usage.duration_ms = (usage.duration_ms or 0) + int((time.time() - t0) * 1000)
    usage.output_meta = {
        **(usage.output_meta or {}),
        "pdf_url": pdf_url,
        "pdf_path": saved,
        "pdf_bytes": result.byte_size,
        "pdf_format": result.page_format,
    }
    usage.save()
    return {
        "status": "success",
        "pdf_url": pdf_url,
        "pdf_bytes": result.byte_size,
        "runtime_ms": usage.duration_ms,
    }
