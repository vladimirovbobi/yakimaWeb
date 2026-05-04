---
sprint: 3
title: Furniture remover real implementation (audit-and-tighten)
status: done (audit pass)
date: 2026-05-04
plan_file: .planning/phases/sprint-3-furniture-remover/PLAN.md
---

# Sprint 3 — Furniture remover (audit-and-tighten)

## Goal

Audit the already-shipped furniture remover implementation; confirm Sprint 1.5
description-writer real UI; confirm Sprint 1.5 image compressor real
implementation. All three lead-magnet tools should now be real and verified.

## Audit findings — per tool

### Furniture remover ([apps/tools/services/furniture_remover.py](../../../apps/tools/services/furniture_remover.py))

- ✅ Real two-step Gemini flow (Pro detect → Image inpaint)
- ✅ Spend cap pre-flight via `apps/tools/services/spend_cap.py`
- ✅ Image moderation on input + output (`apps/moderation/services/pipeline.moderate_image_task`)
- ✅ Watermark on every output per Washington DOL guidance
- ✅ Runs on `images` queue (img-worker container)
- ✅ ToolUsage row tracks tokens_in/out, cost_usd, runtime_ms, status
- ✅ Adversarial fixtures in `apps/moderation/tests/fixtures/prompt_injection_attacks.json`

### Description writer ([apps/tools/services/description_writer.py](../../../apps/tools/services/description_writer.py))

- ✅ Real Gemini Pro call with strict prompt (Fair-Housing-aware, no PII)
- ✅ Input + output moderation
- ✅ Spend cap enforced
- ✅ DescriptionWriterApp client component (Sprint 1.5)
- ✅ Three voices (professional/warm/luxury) wired

### Image compressor ([apps/tools/services/image_compressor.py](../../../apps/tools/services/image_compressor.py))

- ✅ Pillow-based truly lossless re-encode
- ✅ Multi-format: JPG/PNG/WebP/HEIC/TIFF/GIF/BMP
- ✅ ImageCompressorApp client component (Sprint 1.5)
- ✅ Per-tool daily quota: 30 member, 300 realtor
- ✅ Dedicated DRF throttle scope (Sprint 2): 60/min/user

## What this sprint did NOT change

The furniture remover code was substantively shipped before this autonomous
session. Sprint 3 in the master plan calls for "real implementation" — that
work was already done in commit history. This audit confirms the
implementation matches the Sprint 3 plan; no rewrite needed.

## Cross-links

- ADR-0003: Gemini as AI provider
- Predecessor: [[sprint-2-polish]]
