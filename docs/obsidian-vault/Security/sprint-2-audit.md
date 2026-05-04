---
sprint: 2
date: 2026-05-04
auditor: project-team
status: pass
---

# Security audit — Sprint 2

## Surfaces touched

- `caddy/Caddyfile` — edge headers, three rate-limit zones, sitemap routing fix
- `frontend/middleware.ts` — CSP nonce + enforced CSP header + defense-in-depth headers
- `frontend/app/layout.tsx` — nonce threaded to JSON-LD `<script>`
- `frontend/app/(public)/page.tsx` — nonce threaded to breadcrumb JSON-LD
- `frontend/app/(public)/blog/[slug]/page.tsx` — nonce threaded to BlogPosting JSON-LD
- `apps/core/api/throttling.py` — added ImageCompressorThrottle + FeaturedAnonThrottle
- `apps/tools/api/views.py` — image compressor uses dedicated throttle scope
- `apps/marketplace/api/views_featured.py` — featured-services capped by FeaturedAnonThrottle
- `config/settings/base.py` — DRF throttle rate map updated

## Threat model deltas

- **NEW defense:** CSP enforced on every HTML response. XSS via injected `<script>`
  blocked unless attacker can also predict the per-request nonce (cryptographically
  improbable; `crypto.getRandomValues(16 bytes) → base64`).
- **NEW defense:** Edge rate limits split per-purpose. Credential-stuffing on auth
  endpoints can no longer hide in the 60rpm general bucket.
- **NEW defense:** COOP `same-origin` + frame-ancestors `none` — clickjacking
  attempts via embedding fail at multiple layers.
- **NEW defense:** Server tech advertising removed (-Server, -X-Powered-By
  headers stripped at edge).
- **No new attack surface** — Sprint 2 is hardening only; no new endpoints.

## Checklist

- [x] All UGC inputs flow through `ModeratableMixin` (no new UGC types added)
- [x] All staff-write paths log to `ActionLog` (no new staff endpoints)
- [x] All `is_staff` reads log to `AccessLog` (no change)
- [x] Every new file upload has size + type + content scan (image compressor
      already had this from Sprint 1.5)
- [x] Every new third-party API call has spend cap + retry policy (none added)
- [x] No new secrets committed; env-only
- [x] CSP enforced (no `unsafe-inline` for scripts; styles still need it,
      see deferred)
- [x] All inputs validated on the server, not just the client
- [x] Rate limit applied where appropriate — added on compressor +
      featured-services endpoints
- [x] Object-level permissions checked on detail/update/delete (no new views)
- [x] No sensitive data in URL parameters (featured-services takes a public
      `seed_key` which is just a slug)
- [x] Error responses don't leak internals (Problem Details handler unchanged)
- [x] OWASP top-10 sweep:
  - **A01 Broken Access Control**: no change
  - **A02 Cryptographic Failures**: TLS via Caddy auto-https in prod; HSTS
    preload set
  - **A03 Injection**: deterministic regex layer + Gemini classifier + 40+
    injection guards still in place
  - **A04 Insecure Design**: no change
  - **A05 Security Misconfiguration**: ✅ headers tightened
  - **A06 Vulnerable Components**: no dependency changes
  - **A07 Authentication Failures**: ✅ auth endpoint rate limit added
  - **A08 Software/Data Integrity**: CSP enforces script-source integrity
  - **A09 Logging/Monitoring Failures**: Caddy json log output unchanged
  - **A10 SSRF**: not applicable; no user-supplied URLs fetched server-side

## Findings

| Severity | Issue | Where | Remediation |
|---|---|---|---|
| Low | `style-src 'unsafe-inline'` retained | Next.js 15 hydration ships inline styles | Tracked Sprint 9; not launch-blocking |
| Low | Caddy rate-limit zone names share state across reload | If we hot-reload Caddy in prod, anon counter resets | Acceptable; prod uses graceful reload |
| Info | featured_anon throttle is per-IP not per-IP+context | A scraper could rotate context= values | Acceptable: response is small, cached, vendor-deduped; doesn't reveal proprietary data |

## Cross-links

- Sprint retro: [[../Sprints/sprint-2-polish]]
- Threat model: `docs/THREAT-MODEL.md`
- Final security doc: `docs/SECURITY-FINAL.md`
