# CLAUDE.md — Yakima Real Estate Hub

> Onboarding for any Claude session working on this repo. Read first.

## What this is

Multi-surface platform for Central Washington real estate:
- **Yakima Web posts** + **realtor blogs** (license-gated) + **comments**
- **AI lead magnets**: furniture remover (port from `virtual-staging-app`), description writer
- **Marketplace**: Fiverr-shaped lead-gen for photographers, lenders, junk removal, 3D tours, etc.
- **Reddit-style forum**
- **Three control surfaces**: Django admin / Moderator console / Operator dashboard
- **AI moderation pipeline** with prompt-injection defenses on every UGC pipe

Target: 10K MAU steady state, future-proof for content + features without rewrites.

## Stack (locked — see ADRs)

| Layer | Choice |
|---|---|
| Architecture | **Split** per ADR-0005: Django REST API + Next.js 15 frontend + Caddy reverse proxy. **8 services**. Supersedes ADR-0001. |
| Backend | Django 5.x + DRF + drf-spectacular OpenAPI + SimpleJWT + Strawberry GraphQL (read-only) |
| Frontend | **Next.js 15 App Router** + React 19 RSC + Tailwind 3.4 + Framer Motion 11 + TanStack Query (per ADR-0006). Lives in `/frontend/`. |
| Auth | **JWT in httpOnly + SameSite=Strict cookies** (`yw_access` 15min, `yw_refresh` 7d) + CSRF double-submit (per ADR-0008). django-allauth signup. django-otp staff 2FA. django-axes throttle. |
| Reverse proxy | **Caddy 2.x** with rate-limit module (per ADR-0007) — `/api/*` + `/admin/*` → `api:8000`, else → `frontend:3000` |
| DB | Postgres 16 (FTS via tsvector; **pgvector schema-ready** per ADR-0009; activation deferred to v1.1) |
| Cache / queue / sessions | Redis 7 |
| Async | Celery + Beat + dedicated img-worker (image-heavy tasks routed via `apps/core/celery_routes.py`) |
| AI | Google Gemini — 2.5 Flash for moderation, 2.5 Pro for tools |
| License verify | ARELLO API (not DOL — no public DOL API) |
| Storage / CDN | Cloudflare R2 + CDN, signed URLs (5min TTL) |
| Email | Postmark via django-anymail |
| Hosting | Railway (Phase 1) — Fly.io is the alternate |
| Monitoring | Sentry + Better Stack |

ADRs: `0001-django-monolith.md` (superseded by 0005), `0002-arello-for-license-verification.md`, `0003-gemini-as-ai-provider.md`, `0004-lead-gen-only-marketplace-v1.md`, **`0005-split-architecture.md`**, **`0006-nextjs-app-router.md`**, **`0007-caddy-reverse-proxy.md`**, **`0008-jwt-httponly-auth.md`**, **`0009-pgvector-future-proof.md`**.

Documentation suite: `docs/{VISION-AND-SCOPE,SRS,SAD,ICD,MTP,RTM,RISK-REGISTER,THREAT-MODEL,SECURITY-PLAYBOOK,COPY-STYLE-GUIDE,ACCESS-MATRIX,RUNBOOK,STATE-OF-THE-PROJECT}.md`.

## Visual quality bar

Match `C:\Users\vladi\OneDrive\Desktop\Projects\vrov-new`. Source of truth for tokens + animation patterns: `docs/research/design-system-reference.md`.

- **Palette**: `black #080604 / deep #0D0904 / panel #141008 / warm #1A1208 / gold #BFA06A / gold-hi #DEC98A / gold-dim #5A4A28 / ivory #F5EFE0 / mist #CEC4A8 / dim #706450`
- **Headings**: `font-serif` (Cormorant Garamond)
- **Labels**: uppercase + `tracking-luxe` (0.22em)
- **Easing**: `cubic-bezier(0.16, 1, 0.3, 1)` (`ease-luxe` utility)
- **Animations**: `animate-fade-up` (with delay variants), `animate-slow-zoom` for hero bg
- **Scroll reveal**: Alpine `x-reveal` + `x-reveal-stagger` directives (Motion One + IntersectionObserver, honors `prefers-reduced-motion`)

## Project layout

```
yakimaWeb/
├── apps/                Django backend (REST API only post-Sprint-0c)
│   ├── core/            shared mixins + base API utilities (auth, permissions, errors, pagination)
│   ├── accounts/        User, RealtorProfile, VendorProfile, ARELLO client; api/{auth,me,realtor,public}
│   ├── content/         Post, Comment, NewsletterSubscription, SocialEmbed; api/{public,private}
│   ├── tools/           AI lead magnets; api/{public,private}
│   ├── forum/           ForumThread, Reply, Vote, Flair; api/{public,private,votes}
│   ├── marketplace/     Vendor, Service, Package, Bundle, Lead, Review; api/{public_*,private_*,leads}
│   ├── moderation/      ModeratableMixin + 3-layer pipeline; api/ (queue, decisions, flags, investigate)
│   ├── audit/           ActionLog + AccessLog (read-only via api/)
│   ├── operations/      Operator dashboard; api/ (cards, suspend, vendor status, takedown)
│   └── admin_tools/     IP allowlist + 2FA hooks + role decorators (no API surface)
├── config/              settings/{base,dev,prod}, urls, api_urls, celery, wsgi/asgi
├── frontend/            Next.js 15 App Router (per ADR-0006)
│   ├── app/             (public)/, (auth)/, (dashboard)/ route groups
│   ├── components/      layout/, reveal/, ui/, marketing/, content/, forum/, marketplace/, tools/, ops/
│   ├── lib/             api/, auth/, utils
│   ├── styles/          tailwind.config.ts (vrov-new tokens ported)
│   ├── tests/           e2e/ (Playwright), unit/ (Vitest)
│   ├── middleware.ts    JWT cookie gate + CSP nonce
│   └── Dockerfile       multi-stage Node 20-alpine standalone
├── caddy/               Caddy reverse proxy
│   ├── Caddyfile        routing + edge security headers + rate limit
│   └── Dockerfile       xcaddy build w/ rate-limit module
├── templates/           allauth (account/), email digests (emails/), and core/{healthz,robots} only — DEB-002 removed Phase-1 monolith
├── static/              LEGACY — Vite assets retained for allauth + emails (DEB-003 follow-up)
├── docs/                full enterprise doc suite (see Stack table)
│   ├── adr/             9 ADRs (0001 superseded by 0005)
│   └── research/        design audit, ARELLO notes, marketplace patterns
├── tests/e2e/           LEGACY top-level Playwright (frontend/tests/e2e/ is the new home)
└── .planning/phases/    per-phase detailed plan files
```

## Conventions (apply to every change)

| Topic | Convention |
|---|---|
| Commits | Conventional Commits (`feat(scope): ...`, `fix(scope): ...`, `test(scope): ...`, `chore(scope): ...`) |
| Branches | `phase-N/stream-X-name` per stream |
| Tests first | TDD via `superpowers:test-driven-development` for non-trivial logic |
| AI calls | ALWAYS async via Celery — synchronous Gemini in views is forbidden |
| UGC | Every UGC model inherits `ModeratableMixin` — no exceptions |
| Staff writes | Auto-logged via `apps/audit/signals.py` — don't bypass with `objects.update()` |
| Templates | LEGACY — admin + email only. New surfaces are Next.js components in `frontend/`. |
| JS | React 19 RSC by default (server components), `"use client"` only when Framer Motion / hooks / event handlers required. Tailwind utility classes; custom CSS only in `frontend/app/globals.css` `@layer utilities` w/ comment. |
| Secrets | All in `.env`, never committed; `django-environ` reads them; production via Railway/Fly secrets |
| Migrations | One per logical change, named descriptively |
| Code style | Caveman-tight. Minimal comments. No `# noqa` without reason. Run `ruff check && ruff format && djlint templates/` before commit |
| Karpathy | Surgical changes. No premature abstraction. Three repetitions before extracting. |

## Skills to invoke (per task type)

| Task | Skill |
|---|---|
| New phase / non-trivial change | `superpowers:brainstorming` → present design → write to `.planning/phases/phase-N-name/PLAN.md` → execute via `superpowers:executing-plans` |
| Code work | `caveman` (terse) — apply throughout |
| Marketing / website copy | `copy-editing` (run Seven Sweeps) |
| New visual components | `frontend-design` |
| Implementing tests | `superpowers:test-driven-development` |
| Pre-commit | `superpowers:verification-before-completion` (run the test, don't claim done) |
| Pre-merge | `superpowers:requesting-code-review` |
| End of phase | `security-review` for the phase's diff |
| Bug investigation | `superpowers:systematic-debugging` |
| Independent parallel work | `superpowers:dispatching-parallel-agents` |
| AI / Gemini integration | `karpathy-guidelines` (minimal, surgical) |
| Code review feedback | `superpowers:receiving-code-review` (verify, don't blindly apply) |

## Local dev

**Whole stack (8 services, recommended):**

```bash
cp .env.example .env        # set DJANGO_SECRET_KEY (50 random chars)
docker compose up -d        # caddy + frontend + api + db + redis + celery + beat + img-worker
docker compose --profile migrate run --rm migrate
docker compose exec api python manage.py createsuperuser
# Visit http://localhost (Caddy fronts everything)
```

**Backend only (for API/test work):**

```bash
cp .env.example .env
uv venv ; uv pip install -e . --group dev
docker compose up -d db redis
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py runserver  # http://localhost:8000
```

**Frontend only (against running backend):**

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev                 # http://localhost:3000
```

## Quality gates (every PR)

- `pytest` green
- `ruff check . && ruff format --check .`
- `djlint templates/`
- `python manage.py check --deploy` (no warnings beyond explicit waivers)
- For UI changes: Playwright critical paths green
- Coverage ≥ 80% on `apps/accounts`, `apps/moderation`, `apps/audit`

## Critical safety contracts (NEVER break)

1. **Pipeline never approves an attack.** `apps/moderation/services/pipeline.py` orchestrates 3 layers; `injection_guard.parse_classifier_response` fails closed. Adversarial fixtures in `apps/moderation/tests/fixtures/prompt_injection_attacks.json` — add 5+ per phase.
2. **License verification is auditable.** Every ARELLO call writes a `LicenseCheck` row with raw JSON. Admin blocks delete.
3. **Staff actions are logged.** `apps/audit/signals.py` auto-logs writes by `is_staff` users. Never bypass via raw SQL or `.update()`.
4. **Admin behind 2FA + IP allowlist.** `django-otp` enforced for `is_staff`; `AdminIPAllowlistMiddleware` blocks /admin/ from non-allowlisted IPs.
5. **Every UGC pipe inherits ModeratableMixin.** Post-save signal triggers Celery `moderate_content` task. No raw publish paths.

## Phase status (live)

- [x] **Phase 0** — Research & Reference docs
- [x] **Phase 1** — Foundation (auth, license verify, design system, AI moderation, audit, admin lockdown)
- [x] **Phases 2-8 scaffold** — models + DRF API surface (Phase-1 template views deleted in DEB-002 once Next.js reached parity)
- [x] **Sprint 0a** — Full enterprise doc suite (RFP, SRS, SAD, ICD, MTP, RTM, Risk, Threat Model, Security Playbook, Copy Guide, Access Matrix) + ADRs 0005-0009
- [x] **Sprint 0b/0c** — Architecture split: DRF backend + Next.js 15 frontend + Caddy + img-worker (8 services)
- [ ] **Sprint 1** — Real APIs (ARELLO/Gemini/Postmark/R2/Sentry) + seed data + brand assets
- [ ] **Sprint 2** — Production polish: CSP nonces, rate limits, OTP, spend cap, Lighthouse 95+, axe-core 0
- [ ] **Sprint 3** — Furniture remover real implementation
- [ ] **Sprint 4** — Vendor onboarding wizard + LeadMessage UI + notification center
- [ ] **Sprint 5** — Mod console v2 + content polish
- [ ] **Sprint 6** — 25-30 Playwright critical-path specs + final security review + k6 load test
- [ ] **Sprint 7** — Beta launch (private invite, monitoring, feedback iteration)
- [ ] **Sprint 8** — Public launch (attorney pass, press kit, soft + hard launch)

## Master plan + per-phase plans

- Master: `C:\Users\vladi\.claude\plans\create-a-local-real-tranquil-koala.md`
- Per-phase: `.planning/phases/phase-N-<slug>/PLAN.md` (template in master plan)

## Reference projects

- **vrov-new** (`C:\Users\vladi\OneDrive\Desktop\Projects\vrov-new`) — visual quality bar
- **virtual-staging-app** — port furniture remover Gemini code into `apps/tools/services/furniture_remover.py` for Phase 3
- **marketing-dashboard** — reference Gemini SDK patterns (already 2.5-flash compatible)

## Memory

Persistent project memory at `C:\Users\vladi\.claude\projects\C--Users-vladi-OneDrive-Desktop-Projects-yakimaWeb\memory\`. Updated after every significant decision.
