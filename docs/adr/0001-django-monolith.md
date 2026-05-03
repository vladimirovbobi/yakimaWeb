# ADR 0001 — Django Monolith with HTMX + Alpine + React Islands

**Status:** Accepted (2026-05-03)

## Context
Yakima Real Estate Hub is content-heavy with strong relational shape: users → realtors / vendors → posts / services / leads → reviews / moderation. Solo or small team. Target 10K MAU at launch, growing. Must support 8 distinct subsystems (blog, marketplace, forum, AI tools, moderation, control surfaces, social embeds, lead-gen) without rewriting.

We considered:
1. **Django monolith + HTMX/Alpine + React islands** (chosen)
2. **Next.js + Supabase + Vercel** — most polished UX out of box; SaaS auth/db lock-in; doubles cognitive load when we need server-side features (Celery, admin)
3. **Next.js + custom Node + Postgres + S3** — same UX bar without lock-in; more boilerplate; we'd rebuild auth/admin/migrations from scratch
4. **Hybrid Django backend + Next.js frontend** — best of both, doubles surface area

## Decision
Django monolith. Apps: `accounts`, `content`, `forum`, `marketplace`, `tools`, `moderation`, `admin_tools`, `operations`, `core`, `audit`. Postgres for storage (full-text via tsvector, JSONB flex, pgvector ready). Redis for cache + sessions + Celery broker + rate limiting. Celery for every AI call (no synchronous Gemini in views). HTMX + Alpine for 90% of interactivity. React islands (Vite-built, mounted in Django templates) only inside AI tool pages and marketplace search/filter UI. Cloudflare in front (R2 + CDN + WAF + image resize).

## Consequences
**Positive**
- Auth, admin, ORM, migrations, forms, permissions, templating ship out of box → 60% of codebase pre-written
- One repo, one deploy, one mental model
- Django ORM handles the heavy relational graph (vendor → service → package → bundle → lead → review) cleanly
- Admin panel doubles as initial CMS
- Owner has Django muscle memory (marketing-dashboard project) → ramp time minimal

**Negative / Accepted**
- Frontend less flashy than full SPA — mitigated with Motion One + Alpine + targeted React islands
- Two JS toolchains (Alpine for sprinkles, React for islands) — accepted because each is small and well-bounded
- Django template rendering is slower than React SSR at scale — irrelevant at 10K MAU; revisit at 100K
- Future microservices split (likely AI tool service) deferred until forced — standard "majestic monolith" approach

## Revisit when
- AI tool spend > $5K/mo → split AI service into its own repo + autoscale
- Single deploy unit ships > 50 commits/week → consider per-app repos
- We add real-time collaborative features (live document editing) → reconsider Phoenix LiveView or Next.js streaming
