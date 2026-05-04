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
| Framework | Django 5.x monolith with apps inside (no microservices) |
| Frontend | HTMX + Alpine.js + Motion One + Tailwind. React islands ONLY in `static/src/react/` for AI tools + marketplace search |
| DB | Postgres 16 (FTS via tsvector, JSONB for flex, pgvector ready) |
| Cache / queue / sessions | Redis 7 |
| Async | Celery + Beat — every AI call goes through Celery (no synchronous Gemini in views) |
| AI | Google Gemini — 2.5 Flash for moderation, 2.5 Pro for tools |
| Auth | django-allauth (email-only) + django-otp (TOTP for staff) + django-axes (throttle) |
| License verify | ARELLO API (not DOL — no public DOL API) |
| Storage / CDN | Cloudflare R2 + CDN, Caddy in front of compose, image-resize worker |
| Email | Postmark via django-anymail |
| Hosting | Railway (Phase 1) — Fly.io is the alternate |
| Monitoring | Sentry + Better Stack |

ADRs: `docs/adr/0001-django-monolith.md`, `0002-arello-for-license-verification.md`, `0003-gemini-as-ai-provider.md`, `0004-lead-gen-only-marketplace-v1.md`.

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
├── apps/
│   ├── core/         shared mixins, marketing pages, healthz
│   ├── accounts/     User, RealtorProfile, VendorProfile, ARELLO client, verify flow
│   ├── content/      [Phase 2] Post (polymorphic), Comment, lead-magnet pages
│   ├── tools/        [Phase 3] AI lead magnets (furniture remover, description writer)
│   ├── forum/        [Phase 4] ForumThread, ForumReply, Vote, ranking
│   ├── marketplace/  [Phase 5] Vendor, Service, Package, Bundle, Lead, Review, Category tree
│   ├── moderation/   ModeratableMixin + 3-layer Gemini pipeline + injection guard
│   ├── audit/        ActionLog + AccessLog + signals + middleware
│   ├── operations/   [Phase 6] Operator dashboard
│   └── admin_tools/  IP allowlist + 2FA hooks + role decorators
├── config/           settings/{base,dev,prod}, urls, celery, wsgi/asgi
├── templates/        base.html, _components/, account/, accounts/, core/
├── static/src/       Tailwind + Alpine + Motion + HTMX entry → built by Vite to static/dist/
├── docs/
│   ├── adr/          architectural decision records
│   ├── research/     design audit, ARELLO notes, marketplace patterns, guidelines, moderation
│   └── RUNBOOK.md    operations manual
├── tests/e2e/        Playwright critical-path tests
└── .planning/phases/ per-phase detailed plan files
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
| Templates | Tailwind utility classes only — custom CSS only in `static/src/css/tailwind.css` w/ comment |
| JS | Alpine for state, HTMX for server interactions, Motion One for animations, React only inside `static/src/react/` islands |
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

```bash
cp .env.example .env       # set DJANGO_SECRET_KEY (50 random chars)
uv venv ; uv pip install -e . --group dev
npm install ; npm run build
docker compose up -d db redis
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py createsuperuser
.venv/Scripts/python.exe manage.py runserver

# In other shells:
.venv/Scripts/python.exe -m celery -A config worker -l info
.venv/Scripts/python.exe -m celery -A config beat -l info
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
- [ ] **Phase 2** — Content System (Post + Comment + editor + lead-magnet pages)
- [ ] **Phase 3** — AI Lead Magnets (port furniture remover from virtual-staging-app)
- [ ] **Phase 4** — Forum (Reddit-style)
- [ ] **Phase 5** — Marketplace (Fiverr-shaped, lead-gen only)
- [ ] **Phase 6** — Control Surfaces (Mod console + Operator dashboard)
- [ ] **Phase 7** — Social integration (YouTube/Instagram embeds)
- [ ] **Phase 8** — Production polish (SEO + perf + a11y + final security review)

## Master plan + per-phase plans

- Master: `C:\Users\vladi\.claude\plans\create-a-local-real-tranquil-koala.md`
- Per-phase: `.planning/phases/phase-N-<slug>/PLAN.md` (template in master plan)

## Reference projects

- **vrov-new** (`C:\Users\vladi\OneDrive\Desktop\Projects\vrov-new`) — visual quality bar
- **virtual-staging-app** — port furniture remover Gemini code into `apps/tools/services/furniture_remover.py` for Phase 3
- **marketing-dashboard** — reference Gemini SDK patterns (already 2.5-flash compatible)

## Memory

Persistent project memory at `C:\Users\vladi\.claude\projects\C--Users-vladi-OneDrive-Desktop-Projects-yakimaWeb\memory\`. Updated after every significant decision.
