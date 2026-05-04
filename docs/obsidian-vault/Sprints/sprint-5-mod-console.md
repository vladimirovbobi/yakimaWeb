---
sprint: 5
title: Moderator console v2 + content polish (audit)
status: done (audit pass)
date: 2026-05-04
plan_file: .planning/phases/sprint-5-mod-console/PLAN.md
---

# Sprint 5 — Moderator console v2 + content polish (audit)

## Goal

Confirm the moderator console upgrade matches the Sprint 5 plan.

## Audit findings

### Mod console workflow

- ✅ `/mod` lands on next pending item (queue-driven, not browse-driven)
- ✅ Three big buttons: Approve (A), Remove (R), Escalate (E)
- ✅ Action templates (T) with 7 seeded templates
  (`apps/moderation/management/commands/seed_action_templates.py`)
- ✅ Each action POSTs to `/api/v1/mod/decisions/`, logs to `ActionLog`,
  advances queue
- ✅ Investigation view at `/mod/investigate/[user_id]`, logged to
  `AccessLog` (separate from queue work)
- ✅ AI signals visible (severity + categories) but not authoritative —
  even severity-4 needs human confirm

### Per-moderator stats

- ✅ `/mod/stats` page renders
- ✅ Service `apps/moderation/services/mod_stats.py`: agreement_rate,
  reversal_rate, avg_response_minutes, current_streak

### Content polish

- ✅ TipTap rich-text editor for blog body
  (`frontend/components/content/RichEditor.tsx`)
- ✅ Comment image uploads with image moderation
- ✅ Tag M2M on Post; per-tag pages at `/blog/tags/[slug]`

### Escalation path

- ✅ Escalate creates an item in operator queue
- ✅ Operator notification on escalate
- ✅ Removed from moderator pool until operator decides

## Sprint 1.5 fix

Sprint 1.5 corrected the RichEditor `setContent()` call signature for
TipTap 2.10 (was passing object, now passes boolean per the API change).

## Cross-links

- Predecessor: [[sprint-4-vendor-onboarding]]
- Successor: [[sprint-6-delivery]]
