# ADR-0006: Next.js 15 with App Router and React Server Components

- **Status:** Accepted
- **Date:** 2026-05-03
- **Supersedes:** —
- **Superseded by:** —
- **Deciders:** Yakima Real Estate Hub Engineering
- **Tags:** frontend, architecture, react, ssr

## Context

ADR-0005 mandates a split architecture with a dedicated frontend service. This ADR resolves the open question of *which* frontend framework that service runs.

The frontend has to satisfy four hard requirements that emerged from the Phase 0 design audit and Phase 2-5 product surface:

1. **SSR-first public reads.** Yakima Web posts, realtor blog index, lead-magnet landing pages, and marketplace category pages must render server-side for SEO and for first-paint feel on slow Selah / Yakima rural connections. Pure CSR (`create-react-app`-style) is disqualified.
2. **ISR for cached freshness.** Public pages should serve from a static cache and revalidate on a schedule or on demand (via tag invalidation when a post is moderated or a vendor profile updates), without redeploying the whole frontend.
3. **Mixed RSC + interactive islands.** Some routes are content (post detail, blog index) and want maximum server rendering; others are app-shaped (operator dashboard, furniture-remover canvas, marketplace search) and want client interactivity. The framework must let us pick per-component, not per-app.
4. **Native auth read at render-time.** With JWT in httpOnly cookies (ADR-0008), authenticated server-rendered pages must read the access cookie at render time and gate output before bytes leave the server. The framework needs first-class server-side cookie access.

## Decision

Use **Next.js 15 with the App Router**. Render with **React 19 + React Server Components by default**; opt into client components with the `"use client"` directive at the smallest scope that makes sense. Use TypeScript with `strict: true`. Tailwind 3.4 carries over from the existing `static/src/css/tailwind.config.js`, ported to `frontend/styles/tailwind.config.ts` so the design tokens (gold/dark palette, Cormorant serif, `ease-luxe` cubic) transfer 1:1 from `vrov-new` parity work.

This ADR is **subordinate to ADR-0005**: if ADR-0005 is ever superseded back to a monolith, this ADR is moot.

## Rationale

**Why App Router over Pages Router.** Pages Router is now in maintenance: no new features, RSC is App-Router-only, layouts are file-based-only with no nesting, and route groups don't exist. App Router gets nested layouts, route groups (`(public)/`, `(auth)/`, `(dashboard)/`, `(legal)/`), parallel routes (useful for Phase 6 operator dashboard split panels), intercepting routes (deferred — could be useful for modal-style realtor-profile previews on the marketplace), built-in `loading.tsx` / `error.tsx` per segment, and server actions for form mutations without manually wiring fetch. The migration story from Pages → App is painful, so starting on App is the only correct entry point in 2026.

**Why React Server Components by default.** RSC ships zero JavaScript for server-only components. For our blog/post pages this is the difference between ~120 KB of hydration JS and ~15 KB. RSC also keeps secrets server-side automatically (no risk of leaking the Gemini key into a client bundle by import-graph accident). Auth checks happen before render, not after a client-side flash. Trade-off: the RSC/CSR boundary is a real cognitive load — every component author must know which side they're writing.

**Alternatives evaluated.**

| Option | Verdict | Rationale |
|---|---|---|
| **Astro 4** | Rejected | Excellent for content-heavy SSG, but auth + RSC + ISR + heavy JS islands (furniture remover canvas, marketplace search filter UI) push it outside its sweet spot. Smaller ecosystem for Tailwind + Framer Motion + TanStack Query integrations. |
| **Remix v2 / React Router 7** | Rejected (revisit v2) | Modern RSC roadmap, loaders are clean, but ISR story less mature than Next.js as of 2026-05. Smaller production-deploy reference base for our hosting targets (Railway, Vercel). |
| **SvelteKit** | Rejected | Smaller ecosystem for AI tooling integrations (no first-party Vercel AI SDK Svelte equivalent at our maturity bar). Team has less production exposure. |
| **Nuxt 3 (Vue)** | Rejected | Same auth and RSC concerns as Astro plus a smaller talent pool than React. |
| **Pages Router (legacy Next.js)** | Rejected | Maintenance mode; RSC unavailable. |
| **Next.js 15 App Router (chosen)** | Accepted | Hits all four requirements directly. Largest ecosystem. Vercel hosting fallback (ADR-0005). Stable since 13.4 (~3 years of production stability by adoption). |

**Risks acknowledged.**

- **RSC/CSR boundary confusion.** New contributors will misplace `"use client"` and either bloat the bundle or break server-only imports. Mitigation: ESLint rule `@next/next/no-async-client-component`, code review checklist.
- **Library RSC support gaps.** Framer Motion has client requirements (use Motion One in RSC where possible; reserve Framer Motion for `"use client"` islands). TanStack Query is client-only by design. lucide-react works in both.
- **Server actions opinion.** Server actions are powerful but encourage a Rails-style coupling between form and handler. We'll prefer DRF endpoints + `fetch` over server actions for write paths so the API stays the source of truth (and so mobile apps in v2 can reuse it). Server actions allowed only for non-critical UX (e.g., newsletter signup) where double-submitting through DRF would be overkill.
- **Next.js version churn.** The framework moves faster than Django. Mitigation: pin `next@15.x` in `package.json`, evaluate minor bumps in a dedicated PR with a Lighthouse + smoke-test gate.

## Consequences

### Positive
- Server rendering + ISR for SEO without bolted-on caching layers.
- Smaller client bundles via RSC; faster Time-to-Interactive on rural connections.
- First-class server-side cookie reads pair cleanly with ADR-0008 JWT-in-cookie auth.
- Strong ecosystem alignment (Tailwind, lucide-react, Vercel AI SDK, TanStack Query).
- Vercel hosting works out-of-the-box if Railway capacity slips.

### Negative
- RSC/CSR boundary is a real cognitive overhead for contributors.
- Dual asset pipelines (Next.js + Django collectstatic for /admin) until Phase 6 lands.
- Framework moves faster than Django; frontend has more upgrade churn.

### Neutral
- TypeScript becomes mandatory on the frontend (it would have been recommended anyway for a project this size).
- Some libraries (Framer Motion specifically) are confined to client islands; Motion One handles RSC-compatible cases.

## Implementation notes

- Folder structure under `frontend/app/`:

  ```
  app/
    (public)/
      page.tsx                    home
      posts/page.tsx              blog index (RSC + ISR)
      posts/[slug]/page.tsx       post detail (RSC + ISR + tag-revalidate)
      tools/furniture-remover/page.tsx   client island canvas
      marketplace/page.tsx        search shell
    (auth)/
      login/page.tsx
      register/page.tsx
    (dashboard)/
      account/page.tsx            authenticated; cookie-read in RSC
      operator/...                Phase 6
    layout.tsx                    root layout, fonts, theme
    loading.tsx
    error.tsx
    not-found.tsx
  ```

- `next.config.ts`:
  - `productionBrowserSourceMaps: false`
  - `images: { remotePatterns: [...R2 + Cloudinary fallback] }`
  - `experimental: { serverActions: { bodySizeLimit: '2mb' } }`
  - Security headers (CSP, HSTS, X-Frame-Options, Referrer-Policy) — see ADR-0007 for which headers Caddy owns vs. Next.js.

- `middleware.ts`:
  - Runs on every request.
  - Reads `yw_access` cookie; if absent on a `(dashboard)` or `(auth)/login-required` route, redirects to `/login?next=...`.
  - Generates a per-request CSP nonce, stamps it on `request.headers` for Next.js to inject into inline scripts.
  - Does **not** verify JWT signature — that's the API's job. Middleware checks presence and shape only.

- TypeScript strict mode; `tsconfig.json` extends `next/core-web-vitals`.
- Tailwind: `frontend/styles/tailwind.config.ts` ports tokens; `globals.css` imports Tailwind layers.
- Fonts: `next/font` with `Cormorant_Garamond` (display) + `Inter` (body) — self-hosted, no FOIT.
- Data fetching: server components use `fetch(url, { next: { tags: [...], revalidate: 3600 } })`; client components use TanStack Query.

## Risks and mitigations

- **Risk:** A contributor disables RSC by adding `"use client"` to a layout. **Mitigation:** ESLint config + PR checklist; integration test that asserts `(public)/posts/[slug]/page` is rendered server-side (verify zero hydration script for the post body).
- **Risk:** ISR cache pollution from authenticated requests. **Mitigation:** authenticated routes live under `(dashboard)/` with `dynamic = 'force-dynamic'`; `(public)/` routes never read cookies.
- **Risk:** Next.js minor upgrade breaks RSC contracts. **Mitigation:** version pinned; upgrade PR triggers a full Lighthouse + Playwright critical-path run.
- **Risk:** Hydration mismatches from Tailwind class-name churn. **Mitigation:** `next/font` for stable font-family classes; no `Math.random()` in render paths.

## Validation

The decision is validated when:
- Lighthouse Performance ≥ 90 mobile on `/` and `/posts/[slug]`.
- Initial JS payload on `/posts/[slug]` < 80 KB gzipped.
- ISR revalidate-on-tag round-trip < 500 ms p95 from Postmark webhook → revalidate → next render.
- Operator dashboard (Phase 6) ships without rewriting any of the public surface.

We revisit if: Next.js 15 → 16 contains breaking RSC changes that cost more than two weeks to absorb; or if a Remix/RR7 successor consolidates RSC + ISR with a materially simpler model.

## References

- Internal: `docs/adr/0005-split-architecture.md`, `docs/adr/0007-caddy-reverse-proxy.md`, `docs/adr/0008-jwt-httponly-auth.md`, `docs/research/design-system-reference.md`, `CLAUDE.md`.
- External: Next.js 15 release notes; React Server Components RFC; Vercel AI SDK; Lighthouse scoring rubric.
