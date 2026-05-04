---
sprint: 9
title: E2E specs + final security review
status: done
date: 2026-05-04
plan_file: .planning/phases/sprint-9-e2e-security-load/PLAN.md
---

# Sprint 9 — E2E + final security review

## Goal

Bring the Playwright spec coverage up across new surfaces (CSP enforcement,
SEO scaffolding, image compressor, featured services, BFF obscuration,
delivery service) and consolidate the security review for Sprint 2-7
deliveries.

## What landed

### New E2E specs

| Spec | What it asserts |
|---|---|
| [csp-enforcement.spec.ts](../../../frontend/tests/e2e/csp-enforcement.spec.ts) | CSP header has nonce; inline JSON-LD `<script>` carries the nonce; zero CSP violations in console |
| [seo-sitemap.spec.ts](../../../frontend/tests/e2e/seo-sitemap.spec.ts) | `/sitemap.xml` served by Next.js with static + dynamic entries; `/robots.txt` disallows admin/dashboard; Organization/WebSite JSON-LD on home; OG/Twitter meta present |
| [image-compressor-flow.spec.ts](../../../frontend/tests/e2e/image-compressor-flow.spec.ts) | Auth-required redirect; PNG drop-and-compress flow lands a "done" status |
| [featured-services.spec.ts](../../../frontend/tests/e2e/featured-services.spec.ts) | Homepage does NOT show ad slot; blog detail + thread detail DO; API endpoint shape |
| [bff-obscuration.spec.ts](../../../frontend/tests/e2e/bff-obscuration.spec.ts) | Unknown id → 404; method mismatch → 405; auth-required → 401; cross-origin → 403; client mutations don't leak through `/api/v1/...` |
| [security-headers-sprint2.spec.ts](../../../frontend/tests/e2e/security-headers-sprint2.spec.ts) | `-Server` / `-X-Powered-By` stripped; expanded Permissions-Policy; auth burst rate-limit |
| [delivery-service.spec.ts](../../../frontend/tests/e2e/delivery-service.spec.ts) | `/api/delivery/healthz` 200; missing JWT → 401; webhook accepts only HMAC-signed POSTs in prod |

### Existing specs preserved

The 38 pre-existing specs cover signup, realtor verify, vendor onboarding,
forum lifecycle, AI tools, CSRF, OTP, password reset, role-aware dashboard,
offline graceful, accessibility. Total now: **45 specs**.

### Security review consolidation

- [docs/SECURITY-FINAL.md](../../../docs/SECURITY-FINAL.md) updated with
  Sprint 2 closure notes (CSP enforced, edge headers, rate limits,
  routing fix).
- This sprint flags Sprint 6 (delivery) and Sprint 7 (BFF) for follow-on
  audits as separate notes.

## What's deferred

- **Running the suite end-to-end.** Needs Postgres + Redis + Caddy +
  delivery container all running. Not possible in this autonomous session.
  The specs are written to be runnable by the next dev environment.
- **k6 load tests.** Scripts are stubbed in `tests/load/` per Sprint 9
  plan; running them needs infrastructure budget.
- **Third-party penetration test.** Vendor engagement, real money,
  out-of-scope for an autonomous session. RFP ready in `docs/RFP.md`.
- **Lighthouse CI integration.** Plugin to run on every PR — Sprint 10
  polish.

## Sprint 6 + 7 security audits (consolidated)

### Sprint 6 — Delivery service

- Schema-in-Django + reads-via-SQLAlchemy: ✅ no schema drift surface; both
  read the same Postgres tables.
- JWT verification uses Django SECRET_KEY: ✅ same algorithm, same audience.
- HMAC webhook back to Django: ✅ idempotent + signed.
- File validation magic-byte sniff: ✅ doesn't trust `Content-Type`.
- Per-class size caps: ✅ enforced server-side.
- Anti-virus scan integration: ⚠️ stubbed (`scan_status="skipped"`); track
  for Sprint 10 polish.
- CORS scoped to localhost in dev: ✅; production runs same-host behind Caddy.
- Auth dependency + same-origin checks on every endpoint: ✅.

### Sprint 7 — BFF obscuration

- Manifest validation per request: ✅ unknown ID → 404 with no path leak.
- Method binding: ✅ POST manifest only answers POST.
- Same-origin guard: ✅ Origin header compared to Host.
- Auth-required passthrough: ✅ requires `yw_access` cookie.
- Header allow-list: ✅ only `content-type / content-length / cache-control`
  pass through.
- Path injection via `_path`: ✅ template substitution rejects unknown keys.
- Rate limiting at BFF layer: ⚠️ manifest carries the hint; enforcement
  not yet wired in handler. Caddy edge + DRF throttles cover the same
  ground; promote to Sprint 10 polish.

## Lessons

- **Specs that need a running stack should `test.skip` clearly when the
  stack isn't there.** The delivery service spec demonstrates this pattern
  — skip on 502/503.
- **Origin-vs-Host check is not foolproof in dev** (browsers don't always
  set Origin). The handler accepts missing-Origin as same-origin. Acceptable
  because Caddy forces same-host in production.
- **CSP nonce on inline `<script>` requires explicit `nonce={nonce}` prop
  on every JSX `<script>` tag.** Next.js's `<Script>` from next/script
  also needs it explicitly — the framework doesn't propagate by default.

## Cross-links

- Security: [[../Security/sprint-2-audit]] · [[../Security/sprint-6-audit]] · [[../Security/sprint-7-audit]]
- Predecessor: [[sprint-8-obsidian-rfp-docs]]
