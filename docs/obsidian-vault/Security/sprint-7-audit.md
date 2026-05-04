---
sprint: 7
date: 2026-05-04
auditor: project-team
status: pass with deferred items
---

# Security audit — Sprint 7 (BFF obscuration)

## Surfaces touched

- New Next.js route: `frontend/app/api/bff/[id]/route.ts`
- New manifest: `frontend/lib/bff/routes.ts` (15 entries)
- New client helper: `frontend/lib/bff/client.ts`

## Threat model deltas

- **NEW attack surface:** Open proxy concern — the BFF could be abused to
  access arbitrary Django paths if manifest validation is bypassable.
  Mitigated by:
  - Manifest is a hard allow-list; lookup miss → 404.
  - `:param` substitution rejects unknown keys.
  - `_path` body field is the only way to vary the URL; bound to the
    manifest entry's template.
- **NEW attack surface:** Same-origin bypass — a CSRF-style attack from a
  malicious origin could try to reuse the user's cookies. Mitigated by:
  - Origin header check (cross-origin = 403).
  - `yw_access` cookie is `SameSite=Strict`, so the browser doesn't send
    it to cross-origin POSTs anyway.
- **REDUCED attack surface:** Network tab no longer reveals Django endpoint
  structure to attackers reading client-side traffic.

## Checklist

- [x] Manifest is the only source of routable IDs (no dynamic registration)
- [x] Method-bound: each ID is single-method
- [x] Same-origin enforced via Origin header check
- [x] Auth-required routes verify `yw_access` cookie
- [x] Path param substitution validates required keys (`:param` missing → 400)
- [x] Real Django paths never echoed in error responses
- [x] Internal headers stripped (only content-type/length/cache-control pass)
- [x] Cookies forwarded for auth (yw_access, yw_refresh, csrftoken)
- [x] X-Forwarded-* headers preserved for downstream rate-limit accuracy
- [x] CSRF token forwarded if client sends it
- [x] Streaming endpoints (SSE) deliberately keep direct path

## Findings

| Severity | Issue | Where | Remediation |
|---|---|---|---|
| Low | BFF-layer rate limiting not yet enforced | `app/api/bff/[id]/route.ts` | Manifest carries the hint; Caddy + DRF cover same ground; Sprint 10 polish |
| Low | Client-side migration to `bffCall` is incremental | various client components | Existing `apiFetch("/api/v1/...")` calls still work — just visible in network tab; full migration is Sprint 10 polish |
| Info | BFF adds ~10-30ms per request | inherent | Acceptable for mutations; documented in ADR-0011 |

## Cross-links

- Sprint retro: [[../Sprints/sprint-7-bff]]
- ADR: `docs/adr/0011-bff-obscuration.md`
