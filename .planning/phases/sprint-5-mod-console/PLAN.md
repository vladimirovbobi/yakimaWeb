# Sprint 5 — Moderator Console v2 + Content Polish + Mobile Audit

> Predecessor: Sprint 4. Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Mod console UX upgrade per the prior brainstorm: one-queue-one-item-at-a-time, keyboard shortcuts (A/R/E/T), action templates wired, audit log linked. Per-moderator stats. Final mobile audit pass.

## Tasks

1. **Queue-driven workflow.** `/mod` lands on the next pending item. Three big buttons (Approve A, Remove R, Escalate E). Action templates dropdown (T). Each action POSTs to `/api/v1/mod/decisions/`, logs to ActionLog, advances queue.
2. **Investigation view.** Separate `/mod/investigate/[user_id]`. Logged differently in AccessLog. Stops moderators from creeping queue-wise.
3. **AI signals visible, not authoritative.** Each item shows AI classifier reasoning + severity, but the decision is the moderator's. Severity 4 still requires human confirmation (no auto-block).
4. **Per-moderator stats.** `/mod/stats`: items reviewed today/this-week/all-time, agreement rate when 2 mods see same item, reversal rate (operators overruling). Triggers operator alert if review rate > threshold or remove rate > 90%.
5. **Action templates.** Existing `apps/moderation/models.ActionTemplate`. Each template encodes: action (approve/remove/escalate), email-template-id, log-reason. Per-item confirmation modal lets mod pick template + tweak reason.
6. **Mobile final audit.** Re-run breakpoint sweep. Fix any regressions introduced since Sprint 2.

## Verification

- E2E: mod logs in → /mod loads next item → A approves and advances → R removes with template and advances → E escalates with notes
- Investigation: /mod/investigate/[id] logs in AccessLog (not ActionLog)
- Stats: review velocity matches actual actions
- Mobile breakpoint sweep clean

## Sign-off

- [ ] One-queue-one-item flow with keyboard shortcuts
- [ ] Investigation view separated with distinct logging
- [ ] AI signals shown, not authoritative
- [ ] Per-moderator stats render
- [ ] Action templates wired with email send + log entry
- [ ] Mobile audit clean
- [ ] Sprint 5 commit pushed
