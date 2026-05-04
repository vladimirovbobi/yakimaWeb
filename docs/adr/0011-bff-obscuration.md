# ADR-0011: BFF / Network-Tab Obscuration

**Status:** Accepted
**Date:** 2026-05-04
**Deciders:** Project team

## Context

Browser network tab inspection reveals Django endpoint structure to anyone
opening DevTools — `/api/v1/marketplace/leads/`, `/api/v1/forum/votes/`,
etc. This is not a confidentiality issue (the API is documented), but it:

1. Tells attackers exactly which endpoints to target.
2. Reveals our internal information architecture.
3. Makes future API restructuring expensive (clients pin URL shapes).

A standard Backend-For-Frontend pattern routes client requests through a
thin Next.js layer that maps opaque IDs to real paths.

## Decision

Add a Next.js route at `/api/bff/[id]/route.ts` that looks up the opaque
`id` in a server-side manifest and proxies to the real Django path. The
manifest lives at `frontend/lib/bff/routes.ts`. Client components use a
helper, `bffCall(id, options)`, instead of `apiFetch("/api/v1/...")`.

Pragmatism: server components keep direct Django calls. They render
server-side and never appear in the browser network tab. Only client-
driven mutations and interactive reads use the BFF.

Streaming endpoints (SSE for AI tools) keep the direct path because the
BFF would have to terminate and re-open the stream — added latency without
much obscuration benefit.

## Consequences

### Easier

- Network tab inspection reveals `/api/bff/...` only.
- Future Django restructures don't break clients; the manifest absorbs the
  change.
- Centralized place to enforce same-origin + auth + rate limits.

### Harder

- One more layer of indirection. Adding a new client-driven endpoint now
  requires a manifest entry first.
- Manifest IDs are part of the client bundle; they can't be renamed
  without breaking deployed clients. Discipline: add IDs, never rename.
- Stack traces in dev mode have one more hop.
- BFF latency: ~10-30ms per request inside the docker network. Acceptable
  for mutations, expensive for streaming reads.

### Locked-in

- Manifest is a forever artifact; rotating IDs is a deploy event, not a
  code change.

## Alternatives considered

- **Use a generic GraphQL gateway.** Heavier; introduces a query language
  layer. Doesn't fit our REST-shaped backend.
- **Rewrite Django paths to use opaque slugs.** Tied to one URL scheme;
  doesn't help when we add a second client.
- **Skip obscuration entirely.** The network tab IS the documented public
  surface; defending it is theatrical. We chose to do it anyway because
  the marginal cost is low and the signal-to-attackers reduction is real.
- **Use a dedicated BFF service (separate container).** Overkill for v1.
  Next.js is already the public surface; adding a route handler is free.

## Cross-references

- Sprint plan: `.planning/phases/sprint-7-bff-obscuration/PLAN.md`
- Sprint retro: `docs/obsidian-vault/Sprints/sprint-7-bff.md`
- Implementation: `frontend/lib/bff/` and `frontend/app/api/bff/`
- Supersedes / superseded by: none
