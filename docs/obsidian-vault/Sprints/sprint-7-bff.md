---
sprint: 7
title: BFF / Network-Tab Obscuration
status: done
date: 2026-05-04
plan_file: .planning/phases/sprint-7-bff-obscuration/PLAN.md
---

# Sprint 7 — BFF / Network-Tab Obscuration

## Goal

Hide Django endpoint structure from the browser network tab by routing
client-driven mutations and interactive reads through `/api/bff/<opaque-id>`.
Server components keep direct Django calls (those don't appear in the
browser network tab anyway).

## What landed

- **Manifest** — [`frontend/lib/bff/routes.ts`](../../../frontend/lib/bff/routes.ts).
  Each entry assigns an opaque short ID to a `(method, path-template)` tuple.
  15 routes initially registered covering: marketplace mutations (lead,
  message, status, review), forum (vote, reply, thread), comments, flags,
  AI tool submissions, profile updates, newsletter subscription.
- **Proxy handler** — [`frontend/app/api/bff/[id]/route.ts`](../../../frontend/app/api/bff/[id]/route.ts).
  Looks up manifest, validates method, performs same-origin check + auth
  check (when route requires it), substitutes path params, forwards to
  Django with cookies + CSRF + IP headers. Streams the response back.
  Errors return RFC-7807 Problem Details without echoing internal paths.
- **Client helper** — [`frontend/lib/bff/client.ts`](../../../frontend/lib/bff/client.ts).
  `bffCall(id, { pathParams, query, body })` for client components.
  Mirrors the existing `apiFetch` shape so migration is a search-and-replace.

## Security model

- **Same-origin enforced.** Origin header must match Host. Cross-origin = 403.
- **Method-bound.** A POST manifest entry only answers POST. Wrong method = 405.
- **Auth-required routes need `yw_access` cookie.** Missing = 401.
- **Real Django paths never echoed.** Error responses use Problem Details.
- **Internal headers stripped.** Only `content-type`, `content-length`,
  `cache-control` pass through to the client.
- **Rate limit hint per route** in the manifest. The handler doesn't yet
  enforce these (Sprint 9); Caddy edge limits + DRF throttles already cover.

## What's deferred

- Migrating every existing client-component call to use `bffCall`. The
  infrastructure is in place; the migration is a search-and-replace pass
  (~25-40 call sites). Tracked as a Sprint 9 deliverable. Existing
  `apiFetch("/api/v1/...")` calls still work — they just appear in the
  network tab.
- BFF-layer rate limiting using Redis. The manifest carries the hint
  (`route.rateLimit`); the enforcement in the handler is Sprint 9.
- Streaming responses (SSE for AI tools). The `text/event-stream` path
  doesn't get BFF treatment because the BFF would have to terminate the
  stream and re-open it — added latency without much obscuration benefit.
  AI tool streams keep the direct path; flagged in the manifest.

## Verification

- ✓ Frontend `tsc --noEmit`: 0 errors after this sprint
- ✓ Frontend `next lint`: 0 errors after this sprint
- ⚠ End-to-end test: needs Docker; one Playwright spec to be added in
  Sprint 9 that asserts `/api/bff/...` traffic and zero `/api/v1/...` URLs
  in client-driven flows.

## Lessons

- **Don't BFF-route everything.** Server-rendered pages already hide their
  Django calls. Streaming endpoints lose more than they gain. The right
  scope is "client-driven mutations + interactive reads."
- **`X-Forwarded-*` headers** on the BFF→Django leg matter for downstream
  rate-limit accuracy. Without them, every BFF call appears to come from
  the same IP (the Next.js container's IP). Forward the original.
- **Manifest IDs need to be deployable.** The IDs are baked into the
  client bundle; renaming an ID breaks any client that hasn't reloaded.
  Add new IDs; never rename.

## Cross-links

- ADR-0011 (new): BFF / network-tab obscuration. Canonical doc: `docs/adr/0011-bff-obscuration.md`
- Security audit: [[../Security/sprint-7-audit]]
- Predecessor: [[sprint-6-delivery]]
