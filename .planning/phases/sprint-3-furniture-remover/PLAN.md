# Sprint 3 — Furniture Remover Real Implementation

> Predecessor: Sprint 2 (production polish). Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Real furniture-removal AI tool. Port the Gemini Vision implementation from `C:\Users\vladi\OneDrive\Desktop\Projects\virtual-staging-app` into `apps/tools/services/furniture_remover.py`. Streaming progress UI. Per-user rate limit + spend cap. Per-image moderation pipeline (input + output).

## Tasks

1. **Port real implementation** from `virtual-staging-app/`:
   - Read its Gemini SDK usage (model, prompt, masking strategy, output format)
   - Adapt to our Celery img-worker queue (`@shared_task(queue="images")`)
   - Replace stubbed `apps/tools/services/furniture_remover.py` with real impl
2. **Two-step Gemini flow**:
   - Step 1: Vision detect — `gemini-2.5-flash` with vision input, returns bounding boxes + furniture labels
   - Step 2: Inpainting — pass mask + image to inpainting endpoint (Imagen 3 or comparable; if not available, document fallback to local SAM-based mask + diffusion)
3. **Input moderation**: image lands → `apps/moderation/services/pipeline.moderate_image_task` runs first → if approved, kicks off furniture remover task → if rejected, notify user with reason
4. **Output moderation**: result image → another moderation pass (catch any artifacts that synthesized inappropriate content) → if approved, store in R2 + return signed URL → if rejected, queue for human review
5. **Rate limits**: 5 runs/hr/user free tier, 30/hr/realtor, 100/hr/vendor. `ToolUsage` row per run; rate limit check reads from there
6. **Spend cap**: Pre-flight check via `spend_cap.check_budget()` before queueing the Celery task. Returns 429 if exceeded
7. **Streaming UI**: existing React island at `frontend/app/(dashboard)/tools/furniture-remover/page.tsx` — add SSE progress reporting (`processing → mask → inpaint → moderating output → done`) via existing celery task → notification stream
8. **Per-output disclosure footer**: every result image is watermarked with "AI-edited via Yakima Web" + tool version, per Washington DOL guidance. Watermark added at the API boundary, not optional

## Verification

- `pytest apps/tools/tests/test_furniture_remover.py` green
- Manual: upload a photo, see streaming progress, get edited output, watermark visible
- Adversarial: upload 5 known-bad images → all blocked at input moderation
- Spend cap: simulate daily budget exceeded → 429 returned with retry-after
- Rate limit: 6 runs in < 60min as free user → 6th returns 429
- Output stored in R2 under `tools/furniture-remover/{user_id}/{uuid}.jpg`

## Sign-off

- [ ] Real Gemini vision call works, end-to-end output quality acceptable
- [ ] Input + output moderation gates working
- [ ] Spend cap + rate limit enforced
- [ ] Watermark on every output
- [ ] Streaming UI progresses through stages
- [ ] Tests green
- [ ] Sprint 3 commit pushed
