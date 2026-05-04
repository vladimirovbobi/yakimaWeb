# Sprint 10 — Beta Launch (Private Invite)

> Predecessor: Sprint 9. Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Soft-launch to a private invite list. Monitor. Iterate fast on feedback.

## Tasks

1. **Invite list assembled.** ~50-100 Yakima Valley realtors + ~25 vendors. Personal outreach by founder; not cold email blast.
2. **Beta gate.** Feature flag `BETA_INVITE_ONLY=true` in env. Signup form requires invite code. Generate codes via `manage.py generate_invite_codes --count 100 --tag beta-2026-q2`.
3. **Monitoring dashboards live.**
   - Better Stack: uptime monitoring on `/healthz`, `/api/v1/auth/login`, `/`, `/blog`, `/services`
   - Sentry: error rate dashboards, top exceptions, performance breakdown
   - Custom Postgres dashboard: signups/day, posts/day, lead-conversion rate
4. **Feedback loop.** Slack channel `#yakima-web-beta-feedback`. Founder reads daily. Hot-fix queue triaged 1×/day.
5. **Iteration plan.** 4-week beta. Weekly retro. Adjust UX, fix bugs, add small enhancements based on real usage.
6. **Beta success criteria** documented in `docs/launch/BETA-PROGRAM.md`:
   - 80% of invited realtors complete signup
   - 50% post at least one piece of content in first 4 weeks
   - 30+ marketplace leads created
   - Net Promoter Score from beta survey ≥ 30

## Sign-off

- [ ] Invite codes generated and distributed
- [ ] Beta gate enforced
- [ ] Monitoring dashboards live and watchable
- [ ] Slack feedback loop active
- [ ] First-week issues triaged and addressed
- [ ] Sprint 10 commit pushed; STATE-OF-THE-PROJECT.md updated weekly through beta period
