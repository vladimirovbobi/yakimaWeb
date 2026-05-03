# Phase 0 — Research & Reference

## Goal
Stand up the reference materials every later phase reads from. No production code. Reference docs become source of truth — design system tokens, ARELLO endpoints, moderation rubric, marketplace UX patterns.

## Done = all of these exist
- [ ] `docs/research/marketplace-patterns/fiverr-ux-teardown.md`
- [ ] `docs/research/marketplace-patterns/ebay-ux-teardown.md`
- [ ] `docs/research/marketplace-patterns/trust-signals-comparison.md`
- [ ] `docs/research/marketplace-patterns/search-filter-patterns.md`
- [ ] `docs/research/design-system-reference.md`
- [ ] `docs/research/arello-api-notes.md`
- [ ] `docs/research/platform-guidelines-v1.md`
- [ ] `docs/research/ai-moderation-prompt-injection.md`
- [ ] `docs/adr/0001-django-monolith.md`
- [ ] `docs/adr/0002-arello-for-license-verification.md`
- [ ] `docs/adr/0003-gemini-as-ai-provider.md`
- [ ] `docs/adr/0004-lead-gen-only-marketplace-v1.md`

## Tasks
| # | Task | Method |
|---|------|--------|
| 0.1 | ADRs (4 files) | Write directly from locked decisions in master plan |
| 0.2 | `design-system-reference.md` | Re-audit `vrov-new` tailwind.config + components, capture tokens + animation curves with file:line refs |
| 0.3 | `arello-api-notes.md` | Document endpoints from research + sandbox curl examples |
| 0.4 | `ai-moderation-prompt-injection.md` | Catalog known attack vectors + defenses |
| 0.5 | `platform-guidelines-v1.md` | Community standards + severity rubric — `/copy-editing` skill |
| 0.6 | `fiverr-ux-teardown.md` | Parallel Explore agent w/ Firecrawl/WebFetch |
| 0.7 | `ebay-ux-teardown.md` | Parallel Explore agent w/ Firecrawl/WebFetch |
| 0.8 | `trust-signals-comparison.md` | Synthesize from 0.6 + 0.7 |
| 0.9 | `search-filter-patterns.md` | Synthesize from 0.6 + 0.7 |

## Verification
- All 12 files exist with non-trivial content (>500 words each except ADRs which can be ~300)
- `arello-api-notes.md` has at least one curl example (mocked is fine)
- `design-system-reference.md` cites concrete file:line refs into vrov-new
- ADRs all follow consistent template (Status / Context / Decision / Consequences)

## Risks
- Fiverr/eBay block scraping → use Firecrawl MCP, fall back to architectural-review-style synthesis from public engineering blogs + Wikipedia
- ARELLO sandbox not granted → document expected schema, mark as TODO for execution
