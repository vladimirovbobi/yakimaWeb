---
sprint: 10
title: Beta launch
status: prep complete (real launch out-of-scope for autonomous session)
date: 2026-05-04
plan_file: .planning/phases/sprint-10-beta/PLAN.md
---

# Sprint 10 — Beta launch

## Goal

Soft-launch to a private invite list of Yakima Valley realtors and
vendors. Monitor. Iterate fast on feedback.

## Status

**Real launch is out-of-scope for an autonomous coding session.** Beta
requires:

- Real outreach to 50-100 hand-picked realtors (founder relationship work)
- Real Slack channel for feedback
- Real third-party API keys (ARELLO sandbox, Gemini, Postmark, R2, Sentry)
- Hand-curated invite codes
- 4 weeks of monitoring + iteration

What an autonomous session CAN deliver — and has — is the launch-prep
artifact set.

## Artifacts ready

- [docs/launch/BETA-PROGRAM.md](../../../launch/BETA-PROGRAM.md) — goals,
  cohort plan, invite template, weekly cadence, success criteria
- [docs/launch/STATUS-PAGE.md](../../../launch/STATUS-PAGE.md) — components
  to monitor, probe cadence, status grouping
- [docs/launch/CRISIS-RESPONSE.md](../../../launch/CRISIS-RESPONSE.md) —
  incident response runbooks (10 scenarios)
- [docs/launch/LAUNCH-CHECKLIST.md](../../../launch/LAUNCH-CHECKLIST.md) —
  Day -14 to Day +1 timeline
- Coming-soon gated launch page at `/coming-soon` with
  `NEXT_PUBLIC_LAUNCH_GATE` env switch (feature-flag flip enables)

## What the launch session will run

When the user is ready:

1. Generate invite codes via management command
2. Flip `BETA_INVITE_ONLY=true` env
3. Distribute codes via founder outreach
4. Monitor Better Stack uptime + Sentry error rate + signups/day
5. Run weekly retros from [Templates/Sprint-Retro](../Templates/Sprint-Retro.md)
6. Iterate based on feedback

## Cross-links

- Predecessor: [[sprint-9-e2e-security]]
- Successor: [[sprint-11-public-launch]]
