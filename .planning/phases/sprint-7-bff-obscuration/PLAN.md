# Sprint 7 — BFF / Network-Tab Obscuration (NEW)

> Predecessor: Sprint 6. Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Hide Django endpoint structure from the network tab. Public pages keep server-component direct calls (those don't appear in network tab anyway). Client-driven mutations and reads route through `/api/bff/[opaque-id]`.

## Approach (pragmatic)

- **Server components** call `safeServerFetch()` direct to Django. Browser never sees these. Leave as-is.
- **Client components** call `apiFetch("/api/bff/<opaque-id>", body)`. Next.js route handler at `app/api/bff/[id]/route.ts` looks up the mapping, proxies to Django, returns response.
- **Mapping table** in `frontend/lib/bff/routes.ts`. Opaque IDs are 16-char base32 strings keyed to a `(method, path-template)` tuple.
- **Generation**: opaque IDs generated at build time from a YAML manifest. Manifest is committed; IDs are deterministic per build (so client and server stay in sync without runtime registration).

## Tasks

1. **`frontend/lib/bff/routes.ts`** — opaque-id → real-Django-path map. Auto-generated from `frontend/lib/bff/manifest.yaml` via a build hook.
2. **`frontend/app/api/bff/[id]/route.ts`** — single dynamic handler. Looks up id, validates method, forwards to Django with cookies + auth headers, returns response transparently.
3. **Migrate client components** — find every `apiFetch("/api/v1/...")` call in client components → swap to `apiFetch("/api/bff/<id>", ...)`. Codemod pass via tsmorph.
4. **Rate limit + structured logging** at the BFF layer. `lib/bff/rate-limit.ts` uses Redis (via Upstash on prod, in-memory in dev) keyed on user-id+route. Logs: every BFF call gets a structured log line for observability.
5. **CORS + same-origin guard.** BFF only accepts same-origin requests (verified via `Origin` header). Non-same-origin → 403.
6. **Verification.** Open homepage in Chrome devtools → network tab. Should see only `/api/bff/...` URLs and Next.js asset paths. Zero `/api/v1/...` from the browser.

## Latency cost & decision rules

- BFF adds ~10-30ms per request (Next.js → Django roundtrip in same docker-compose network).
- Acceptable: all marketplace/forum/lead/comment mutations, secondary reads triggered by user actions.
- NOT acceptable: AI tool streaming (use direct WebSocket/SSE on a separate path), primary content fetches (already handled server-side).

## Sign-off

- [ ] `lib/bff/routes.ts` generated from manifest, all opaque IDs unique
- [ ] All client-component mutations route through `/api/bff/[id]`
- [ ] Network tab shows zero `/api/v1/...` URLs from client
- [ ] Same-origin enforcement works (cross-origin returns 403)
- [ ] Rate limit + logging at BFF layer functional
- [ ] pytest + Playwright green
- [ ] Sprint 7 commit pushed; ADR-0011 logged
