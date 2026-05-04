# Phase 3 — AI Lead Magnets

## Goal
Two production tools: furniture remover (port virtual-staging-app Gemini code) + description writer.
Per-user rate limits, ToolUsage ledger, async via Celery.

## Done
- [ ] `/tools/furniture-remover` — upload photo → Gemini inpaint → before/after slider
- [ ] `/tools/description-writer` — fill structured form → Gemini Pro → editable output
- [ ] ToolUsage row per run (user, tool, tokens, cost, status)
- [ ] Per-user rate limits (Redis token bucket): 10 furniture-remover/day, 30 description-writer/day for member; 100 for realtor; unlimited for staff
- [ ] Per-tool daily spend cap enforced via env var (auto-disable on breach)
- [ ] All inputs go through moderation (`apps.moderation.tasks.moderate_content`) BEFORE the LLM call
- [ ] All AI outputs sanitized (description-writer output checked for hallucinated property data)
- [ ] Tests + 5 new prompt-injection fixtures specifically targeting tool prompts

## Models
- `Tool(TimeStampedModel)` — slug, name, description, model_id, is_enabled, cost_per_run_estimate
- `ToolUsage(TimeStampedModel)` — user FK, tool FK, status, input_meta JSONB, output_meta JSONB, tokens_in/out, cost_usd, error
- `RateLimit` (Redis-backed, no DB model)

## Skills: caveman, karpathy-guidelines (minimal abstractions), security-review (treat AI input as adversarial)
