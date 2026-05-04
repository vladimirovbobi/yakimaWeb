# Request for Proposal — Yakima Real Estate Hub

**Issued:** 2026-05-04
**Issuer:** Yakima Real Estate Hub (project)
**Status:** Reference document. Most engagements happen as direct outreach;
this RFP exists so vendor proposals share a common shape.

## 1. Project overview

Yakima Real Estate Hub is a community + marketplace + AI-tooling platform for
the Yakima Valley and wider Central Washington. It serves three audiences:

- **Buyers/sellers** — market truth, verified-realtor content, and discussion.
- **Realtors** — license-verified blog authorship, AI tools that save listing-prep time, marketplace lead generation.
- **Service vendors** — photographers, lenders, stagers, web/automation builders, junk haulers, inspectors, surveyors — getting found by realtors and homeowners locally.

Architecture is locked: Django REST API + Next.js 15 frontend + Caddy edge,
with Postgres + Redis + Celery + img-worker. See `docs/SAD.md` for the full
system architecture document.

## 2. Scope of engagements

This RFP covers vendor work in any of the following categories:

| Category | Examples |
|---|---|
| Brand & visual | Logo SVG + favicon set, OG image template, photography (Yakima Valley locations), illustrations |
| Content | Blog ghostwriting, copy-editing passes on enterprise docs, video scripts |
| Engineering augmentation | Targeted feature work (e.g. MLS connector, multi-language) |
| Legal | WA-licensed attorney review of Privacy/Terms, fair-housing review |
| Marketing | Press kit polish, launch outreach, paid acquisition pilots |
| Compliance | Penetration test, SOC 2 readiness assessment |

Engineering augmentation requires familiarity with our locked stack.

## 3. Success criteria

A successful engagement:

1. Delivers what was specified, on time.
2. Communicates blockers within 24 hours of discovering them.
3. Leaves the codebase / docs / assets in a state that doesn't require
   rework by the project team.
4. Respects our locked decisions (the 11 ADRs).

Project-level success metrics for v1 launch:

- 500 signups in first month post-launch
- 100+ blog posts published (mix of org + verified realtors)
- 50+ active vendors across the category tree
- Lighthouse ≥ 95 on the four primary public pages
- axe-core: zero serious/critical violations
- Sentry error rate < 0.5% sustained

## 4. Milestones + delivery cadence

For multi-week engagements:

- Week 1: kickoff + proposal sign-off + access provisioning
- Each week thereafter: written status update covering progress, risks, decisions
- Final week: handoff doc + walkthrough call

For one-shot deliverables:

- Sprint-shaped: 1-2 week turnaround typical
- Async written progress; synchronous calls only when blocked

## 5. Vendor expectations

### Technical

- All code passes `pytest`, `ruff check`, `ruff format --check`, `djlint`,
  `npm run lint`, `npx tsc --noEmit` before submission.
- All code follows the Conventional Commits convention with the project's
  scope conventions (see `CLAUDE.md`).
- All security-touching changes include adversarial test fixtures.
- All public pages remain mobile-responsive and Lighthouse-passing after the change.
- All third-party API additions go through Celery (no synchronous external calls in views).

### Communication

- Write-first culture: decisions live in markdown, not in DMs.
- Preferred async channel: GitHub PRs + issue comments.
- Synchronous calls are scoped: pre-agreed agenda or they don't happen.

### IP

- All code, copy, and assets created under engagement become property of
  Yakima Real Estate Hub on payment.
- Vendor may not reuse engagement-specific code or assets in other client work
  without written permission.
- Vendor retains the right to list the engagement on their portfolio if the
  project goes public, with platform approval of any specific imagery used.

### Security

- Vendors with backend access sign an NDA + a data-handling addendum.
- No production data leaves Railway/Fly secrets management.
- Real ARELLO/Gemini/Postmark/R2/Sentry keys are never committed and never
  shared via any synchronous channel; only via the platform's secret manager.

## 6. Selection process

### Initial response (1 week)

Submit:

1. Two-page proposal: scope understanding, approach, deliverables, timeline.
2. Three references with links to past similar work.
3. Hourly rate or fixed-price quote with assumption list.
4. Availability — start date, hours per week, any constraints.

### Shortlist (1 week)

Top 2-3 vendors get a 30-minute scoping call. Outcome is either signed scope
or polite decline.

### Engagement (varies)

Signed scope, 50% deposit if engagement is > $5k, weekly status, final
deliverable + handoff.

## 7. IP terms + licensing

- Code: copyright assigns to Yakima Real Estate Hub on payment.
- Assets (logos, illustrations, photos): exclusive perpetual license to
  Yakima Real Estate Hub. Vendor retains the moral right to be credited.
- Open-source dependencies: vendor flags any GPL / AGPL / SSPL inclusion
  in advance — the project's chosen license stack is permissive (MIT / BSD / Apache 2.0).
- Pre-existing vendor code: vendor warrants right to use; vendor grants
  perpetual license to project for any pre-existing code embedded in the deliverable.

## 8. Termination + dispute resolution

- Either party may terminate for convenience with 7 days' written notice.
- On termination: project pays for completed work; vendor delivers all
  in-progress materials in their current state.
- Disputes: 30-day good-faith negotiation, then mediation in Yakima County, WA.
- Governing law: Washington State.

## 9. Submission

Proposals to: `hello@yakimaweb.com` with subject line
`RFP / [your firm] / [category]`.

We respond within 7 business days even if the answer is "not at this time."

## 10. Versioning

This RFP is v1.0 (2026-05-04). Material changes get a new version letter
(v1.1, v1.2, ...) and a changelog at the bottom of the file.

---

## Changelog

- **v1.0** (2026-05-04) — initial RFP.
