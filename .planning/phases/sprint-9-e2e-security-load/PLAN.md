# Sprint 9 — E2E Critical Paths + Security Review + Load Test

> Predecessor: Sprint 8. Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Final-quality E2E coverage, full security review, k6 load test pass at 500 concurrent users.

## Tasks

1. **Playwright critical paths to 25-30 specs.** Existing 36 specs → consolidate (some overlap). New flows to cover:
   - Sprint 6 delivery service (vendor upload → buyer download)
   - Sprint 7 BFF (network tab shows only opaque URLs)
   - Sprint 4 lead messaging conversation full lifecycle
   - Sprint 3 furniture remover happy + adversarial paths
   - Sprint 2 CSP enforcement (no console violations)
2. **Security review.** Use `security-review` skill on the full repo diff since Sprint 0c. Checklist:
   - All UGC pipes inherit `ModeratableMixin` (no exceptions)
   - All auth endpoints have rate limit + 2FA where applicable
   - All file uploads have size + type + scan validation
   - All third-party API calls have spend cap + retry policy
   - All staff actions log to ActionLog
   - Every `is_staff` route IP-allowlisted or 2FA-gated
   - CSP enforced, all security headers present
   - No secrets committed, env-only
3. **k6 load test.** `tests/load/homepage.js` — 500 concurrent users, 5-min ramp + 10-min sustain. Targets: p95 < 500ms, error rate < 0.5%, no 5xx.
4. **`tests/load/marketplace.js`** — 200 concurrent users browsing marketplace, filtering, opening vendor profiles. Targets same as above.
5. **`tests/load/lead-flow.js`** — 100 concurrent buyers submitting lead inquiries. Targets: p95 < 1s, zero data loss.

## Verification

- Playwright suite passes locally + in CI
- Security review report in `docs/SECURITY-FINAL.md` shows zero high/critical issues
- k6 reports meet targets on all three scenarios
- Sentry shows zero unexpected errors during load test

## Sign-off

- [ ] 25-30 Playwright specs all green
- [ ] Security review complete, findings remediated
- [ ] k6 load tests pass on homepage, marketplace, lead-flow
- [ ] Sprint 9 commit pushed
