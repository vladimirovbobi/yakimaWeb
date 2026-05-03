# ADR 0003 — Google Gemini as AI Provider

**Status:** Accepted (2026-05-03)

## Context
Two AI workloads on the platform:
1. **Moderation** — every UGC item (post, comment, blog, review, gig description, forum reply) classified for spam / harassment / off-topic / prompt-injection / policy-violation. Latency-sensitive (sub-second), high volume, low cost per call.
2. **Lead-magnet tools** — furniture remover (image inpainting), description writer (long-form generation), more later. Latency-tolerant (Celery async), lower volume, higher cost per call.

We considered:
1. **Google Gemini end-to-end** (chosen)
2. **Anthropic Claude end-to-end** — strongest safety reasoning; higher per-call cost; new SDK to integrate
3. **OpenAI GPT-4o-mini + moderation API** — cheapest moderation; no continuity with existing infra
4. **Hybrid: Claude for moderation, Gemini for tools** — best of both safety + cost; doubles SDK surface area; deferred until Phase 6 if Gemini moderation underperforms

## Decision
Google Gemini for both workloads. Models:
- **Gemini 2.5 Flash** — moderation classifier (cheap, fast, strict JSON via response schema)
- **Gemini 2.5 Pro** — description writer (longer context, better prose)
- **Gemini 2.5 Flash Image** (or successor) — furniture remover via inpainting (port from `virtual-staging-app` project)

## Why
- Owner has Gemini muscle memory (marketing-dashboard ADK service + virtual-staging-app)
- Existing two-call inpainting pattern in `virtual-staging-app` ports directly → Phase 3 ships faster
- Gemini structured output (JSON schema response) is best-in-class for moderation JSON contract
- Pricing competitive on Flash tier; Pro acceptable for tools where we charge usage

## Consequences
**Positive**
- One SDK, one billing dashboard, one set of failure modes to learn
- Existing virtual-staging code is plug-in compatible
- Gemini's safety filters catch obvious egregious content even before our moderation prompt runs
- 1M-token context window on Pro lets us include full platform guidelines in moderation prompt without truncation

**Negative / Accepted**
- Single-vendor risk → mitigated: every AI call goes through `apps/moderation/services/ai_classifier.py` and tool wrappers; swap is one file
- Gemini safety filters can over-filter benign real-estate slang (e.g. "blast" the listing, "killer" deal) → tune via `safety_settings` per call; log false positives via moderation review tooling
- Prompt injection defenses must be bespoke (no built-in Anthropic-style constitutional guardrails) → addressed by `apps/moderation/services/injection_guard.py` (delimited input + fail-closed JSON schema + adversarial test suite)

## Cost guardrails
- Per-user rate limits on every AI tool from day 1 (enforced in Celery via Redis token bucket)
- Daily spend cap per Gemini API key (Cloud Console alert + auto-suspend at ceiling)
- Operator dashboard shows daily spend by tool + by user; flags anomalies

## Revisit when
- Moderation false-positive rate > 5% after tuning → evaluate Claude Haiku side-by-side
- Image-tool quality drops below user expectations → evaluate Imagen, FLUX, or similar
- Gemini pricing moves > 2x → renegotiate or switch
