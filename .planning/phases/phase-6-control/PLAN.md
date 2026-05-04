# Phase 6 — Control Surfaces

## Goal
Two custom UIs distinct from Django admin:
1. **Moderator console** — queue UI for triage; one item, three actions, keyboard shortcuts.
2. **Operator dashboard** — read-mostly meta-view: signups, content velocity, mod queue depth, AI spend, license expirations, suspicious patterns.

## Done
- [ ] `/ops/mod/` — pending queue, severity-sorted; A/R/E keyboard shortcuts; templates dropdown
- [ ] `/ops/` — operator dashboard with 6 cards (signups, mod queue, AI spend, vendors w/o leads, license expirations, suspicious patterns)
- [ ] `/ops/audit/` — searchable AccessLog + ActionLog viewer
- [ ] All routes behind `@require_role` + `@require_otp`
- [ ] AccessLog populated for every page hit on these surfaces
- [ ] Tests for permission gates + queue ordering

## Skills: caveman, frontend-design (data-dense not flashy), security-review (highest-trust surface), karpathy-guidelines
