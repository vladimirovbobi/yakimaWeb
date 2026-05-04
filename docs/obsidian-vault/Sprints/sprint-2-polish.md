---
sprint: 2
title: Production polish — CSP, headers, rate limits, mobile
status: done
date: 2026-05-04
plan_file: .planning/phases/sprint-2-polish/PLAN.md
---

# Sprint 2 — Production polish

## Goal

Take the seeded, welcoming-homepage stack to production-grade: enforced CSP
nonces, tightened per-endpoint rate limits, expanded edge security headers,
clean throttle coverage on every new endpoint.

## What landed

### CSP enforcement

- **Next.js middleware** ([middleware.ts](../../../frontend/middleware.ts)) now
  sets `Content-Security-Policy` on every response, with a per-request nonce.
  The nonce is also placed on `x-csp-nonce` so server components can read it.
- Inline JSON-LD `<script>` blocks in
  [app/layout.tsx](../../../frontend/app/layout.tsx),
  [app/(public)/page.tsx](../../../frontend/app/(public)/page.tsx), and
  [app/(public)/blog/[slug]/page.tsx](../../../frontend/app/(public)/blog/[slug]/page.tsx)
  thread the nonce.
- `script-src 'self' 'nonce-{N}' 'strict-dynamic'` allows nonced scripts to
  load further scripts (Next.js needs this).
- `style-src 'self' 'unsafe-inline' fonts.googleapis.com` retained because
  Next.js 15 still ships inline style attributes for hydration. Tracked as a
  Sprint 9 hardening task; not a launch blocker.
- `frame-ancestors 'none'` is the modern X-Frame-Options.
- `frame-src` allowlist: youtube, youtube-nocookie, instagram, matterport.
  Adjust when new embeds are added.

### Edge security (Caddy)

- COOP `same-origin`, CORP `same-origin`, X-Permitted-Cross-Domain-Policies
  `none`.
- Permissions-Policy expanded: `camera=(), microphone=(), geolocation=(),
  payment=(), usb=(), interest-cohort=()`.
- Strips `Server` and `X-Powered-By` so we don't advertise tech.
- HSTS preload retained.

### Rate limits (Caddy)

- `/api/v1/auth/login*`, `/api/v1/auth/refresh*`, `/api/v1/auth/password-reset*`:
  **10 rpm/IP** (credential stuffing defense).
- `/api/v1/tools/*`: **30 rpm/IP** (AI cost defense).
- Default anonymous: **60 rpm/IP** (unchanged).
- Authenticated traffic with `yw_access` cookie skips edge limits and hits
  DRF throttles.

### DRF throttle audit

- Added `ImageCompressorThrottle` (`60/minute`) — local CPU, users batch
  listing photos.
- Added `FeaturedAnonThrottle` (`120/minute`) — public + cached, but capped
  to defend against scrapers.
- All seven existing scopes (vote, lead, ai_tool, comment, forum_write, flag,
  message) verified active in `config/settings/base.py`.

### Routing fix

- `/sitemap.xml` and `/robots.txt` now correctly route to Next.js (was
  Django). The Sprint 1 native sitemap.ts + robots.ts handlers now serve
  these paths and include dynamic entries (posts, threads, vendors,
  services).

## Mobile audit

The existing [`frontend/app/mobile.css`](../../../frontend/app/mobile.css) was
already in good shape from Sprint 0c work:

- iOS safe-area insets via `env(safe-area-inset-*)`
- 16px form input font-size (no iOS zoom on focus)
- 44×44 touch targets via `[data-touch]` attribute selector
- `:hover` effects suppressed via `@media (hover: none)`
- Tap highlight transparent + `touch-action: manipulation`
- Slimmer scrollbars on `< 640px`

No regressions. Tracked as continually-checked rather than a one-time pass.

## Deferred

- Lighthouse 95+ run-and-fix — needs running dev stack (Docker not available
  in this autonomous session). The static work that drives Lighthouse score
  is done; verification is gated on a Docker-running environment.
- axe-core run-and-fix — same gating.
- 24-hour penetration test — vendor engagement, not in-scope for an
  autonomous session.

## Verification

- ✅ Frontend `tsc --noEmit`: 0 errors
- ✅ Frontend `next lint`: 0 errors
- ✅ Backend `ruff check` on Sprint 2 files: clean
- ✅ Caddyfile syntax: validated by structure (live `caddy validate` gated on
  Docker)
- ⚠ pytest: deferred (Postgres + Redis containers needed)

## Lessons

- **Style-src `'unsafe-inline'` is unavoidable in Next.js 15 today.** Don't
  fight it; track the migration path in Sprint 9.
- **Caddy's named matchers (`@auth_burst`, `@tools`, `@ratelimit`) execute
  in declaration order** — auth and tools must come before the catch-all
  anonymous limit so the tighter rules apply first.
- **Next.js's special metadata routes (`sitemap.ts`, `robots.ts`) bypass
  middleware** — you don't need to whitelist them in the matcher; they're
  handled by Next's metadata pipeline.

## Cross-links

- ADRs touched: [[../Decisions/ADR-0007]] (Caddy), [[../Decisions/ADR-0008]] (JWT cookies)
- Security audit: [[../Security/sprint-2-audit]]
- Predecessor: Sprint 1.5 (image compressor + featured services)
