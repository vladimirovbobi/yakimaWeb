# ADR-0005: Split Architecture (Django API + Next.js Frontend behind Caddy)

- **Status:** Accepted
- **Date:** 2026-05-03
- **Supersedes:** ADR-0001
- **Superseded by:** —
- **Deciders:** Yakima Real Estate Hub Engineering
- **Tags:** architecture, frontend, backend, infrastructure

## Context

ADR-0001 chose a Django monolith with HTMX + Alpine on the front-end. That decision was correct under the constraints at the time: solo-developer velocity, a 10K-MAU steady-state target, and a single deploy surface. Since then three forces have shifted the trade-off:

1. **Visual quality bar.** The product target is parity with `vrov-new` — heavy use of staggered reveals, choreographed transitions, choreography-aware components, and a mobile-first layout where interaction polish matters as much as content. HTMX + Alpine can express this but at high authoring cost and with a brittle SSR/CSR boundary.
2. **SSR + ISR for SEO.** Public read paths (Yakima Web posts, realtor blog index, marketplace category pages) need server-rendered output for SEO and incremental static regeneration for cache freshness. Django's template stack is server-rendered but lacks an ISR primitive; bolting cache layers around HTMX partials is awkward.
3. **Operational separation.** A separate frontend service is now a hard requirement of the platform plan: it permits independent deploy cadence for visual changes, reduces blast radius (a frontend bug cannot 500 the API), and lets us push the frontend onto Vercel as a fallback if Railway capacity slips (ADR-0001 Phase 1 hosting).

The cost-benefit math from ADR-0001 ("single repo, single deploy, fastest path to first 10K MAU") has flipped enough that staying monolithic now blocks the visual and SEO targets that the business plan requires.

## Decision

Split the Django monolith into two services: a **Django REST API backend** (`api`) and a **Next.js 15 frontend** (`frontend`), with **Caddy 2** acting as the reverse proxy in front of both. The full local-and-prod compose graph is **8 services**: `caddy`, `frontend`, `api`, `db` (Postgres + pgvector), `redis`, `celery` (worker), `beat` (scheduler), and `img-worker` (Pillow-heavy image ops, isolated from the request-serving worker pool).

This decision **supersedes ADR-0001**. The other locked stack choices (Postgres, Redis, Celery, Gemini, ARELLO, Postmark, Cloudflare R2, Sentry, Better Stack) are unchanged and carry forward.

## Rationale

Four alternatives were evaluated.

**(a) Stay monolithic with HTMX + Alpine.** Cheapest in the short term — zero migration cost. Rejected: HTMX cannot reach RSC + ISR caching natively. Reaching `vrov-new` polish across blog, forum, marketplace, and tools would require a growing maze of Alpine state machines and HTMX swaps. The blast-radius problem (a moderation queue page bug breaks the public site) does not get better with time.

**(b) Monolith + React islands inside Django templates.** A common middle path. Rejected: dual asset pipelines (Django collectstatic + Vite) create a complex SSR/CSR boundary; islands don't get RSC; you still pay for Django sessions on every front-end navigation; and front-end engineers must learn Django templates to ship. The current `static/src/react/` islands plan would have hit ~6 islands by Phase 5 and become the slowest part of the stack to evolve.

**(c) Split with Next.js 15 (chosen).** RSC + App Router + ISR solve the "SSR for SEO + interactive for app" problem natively. Vercel offers an escape valve from Railway capacity issues (ADR-0001 Phase 1 hosting) without rewriting. Next.js 15 is stable, has stable App Router as of v13.4, and has the largest ecosystem for our adjacent integrations (TanStack Query, lucide-react, Framer Motion).

**(d) Split with Astro + Vue.** Astro's island model is excellent for content-heavy sites but its ecosystem (auth, forms, AI tooling, community moderation primitives) is materially smaller than React's. Rejected.

**(e) Split with Remix v2 / React Router 7.** Modern, RSC-bound roadmap, but ISR story less mature than Next.js as of 2026-05; loaders are server-only by default and the team has less production exposure. Rejected for v1; revisit at v2.

**Cost.** The migration is scoped at roughly three weeks in Sprint 0c: Caddy + compose rewrite (2 days), Next.js scaffolding and route group layout (3 days), Django DRF + JWT (ADR-0008) endpoints to back the existing flows (5 days), porting auth/license-verify/admin shells (4 days), and contract testing (1 day). Operational cost rises: two codebases, two build pipelines, two deployment targets. The payback is faster front-end iteration after migration, smaller client bundles via RSC, and a security posture where most rendering happens on the server.

**Why 8 services.** Caddy as ingress (auto-TLS, rate-limit, compression, security headers — see ADR-0007). Separate `celery` worker for moderation/audit/email tasks vs. `img-worker` so a slow Pillow op cannot starve the moderation pipeline (ADR-0003 makes every Gemini call async; preserving worker headroom is mandatory). `beat` as its own service so a worker restart never drops the schedule.

## Consequences

### Positive
- Frontend can iterate on RSC + ISR without touching Django.
- Smaller client bundles; auth checks happen server-side via cookies (ADR-0008).
- Blast-radius separation: a frontend deploy cannot break `/api/v1/auth/`.
- Vercel-as-fallback hosting story for the frontend.
- `img-worker` isolation keeps Phase 3 (furniture remover) latency from interfering with moderation throughput.

### Negative
- Two repos-in-one (`apps/` and `frontend/`) means engineers must hold both stacks in their head.
- Two deploy pipelines, two CI runs, two sets of secrets.
- Cross-service contract drift is now a real failure mode — must be covered by contract tests (drf-spectacular OpenAPI schema + frontend type generation).
- Auth flows are more complex (httpOnly cookie + CSRF double-submit; see ADR-0008) than Django session-only.
- Initial migration is ~3 weeks of work that does not directly ship features.

### Neutral
- The 8-service compose file is more to read but each service has a single, narrow responsibility.
- `caddy/Caddyfile` becomes a config artifact under version control (vs. nginx + certbot scripts).

## Implementation notes

- `pyproject.toml` adds: `djangorestframework`, `djangorestframework-simplejwt`, `drf-spectacular`, `django-cors-headers`, `django-csp`, `strawberry-graphql` (deferred GraphQL endpoint for Phase 6 operator dashboard).
- New top-level `frontend/` directory with Next.js 15 App Router project (see ADR-0006).
- New `caddy/Caddyfile` (see ADR-0007).
- New `docker-compose.yml` replaces the existing one; old single-service compose archived in `docs/research/legacy-compose.yml`.
- API surface lives at `apps/*/api/` (views, serializers, urls). Existing Django templates remain only for `/admin/` and the email-confirmation flows that allauth owns.
- `config/settings/base.py` adds `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, JWT cookie auth defaults.

## Risks and mitigations

- **Risk:** Migration overruns 3-week budget. **Mitigation:** Sprint 0c plan in master plan has each stream gated; if any stream slips >1 day, escalate to descope rather than absorb.
- **Risk:** Contract drift between OpenAPI schema and frontend types. **Mitigation:** CI runs `drf-spectacular --validate` and re-generates frontend types from the schema; PR fails on diff.
- **Risk:** Operating two services on Railway exceeds free-tier compute. **Mitigation:** Railway Pro tier is budgeted; Vercel fallback for `frontend` keeps the API on Railway alone.
- **Risk:** Two-codebase fatigue for the solo-developer phase. **Mitigation:** Convention-heavy scaffolding (CLAUDE.md skill mapping); shared linters; shared CI.

## Validation

The decision is validated when:
- Sprint 0c closes with all 8 services healthy in compose and on Railway.
- `frontend` Lighthouse score ≥ 90 on `/` and `/posts/[slug]` (mobile).
- API p95 latency < 200 ms on auth + content read paths under 100 RPS load test.
- Two deploys-in-one-day demonstrated (frontend visual fix + API bugfix, independent).

We revisit if: contract drift produces three or more production bugs in any quarter, or if frontend hosting cost on Vercel exceeds 30 % of total infra spend.

## References

- Internal: `docs/adr/0001-django-monolith.md` (superseded), `docs/adr/0006-nextjs-app-router.md`, `docs/adr/0007-caddy-reverse-proxy.md`, `docs/adr/0008-jwt-httponly-auth.md`, `docs/adr/0009-pgvector-future-proof.md`, `CLAUDE.md`, master plan.
- External: Next.js 15 release notes; Caddy 2 docs; DRF + SimpleJWT docs; Vercel Next.js hosting reference architecture.
