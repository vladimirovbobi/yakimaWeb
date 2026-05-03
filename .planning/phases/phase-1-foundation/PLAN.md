# Phase 1 — Foundation

> Substrate. Polished. Auth + license + design system + AI moderation + audit + admin lockdown.

## Goal
Production-grade foundation. Anyone signs up + email-verifies + logs in. Realtors verify WA license via ARELLO → upgrade to `realtor` role with badge. Every UGC pipe has moderation hooks. Admin behind 2FA. Homepage / About / Guidelines / Privacy / Terms / Auth pages match `vrov-new` polish bar. Deployed at public URL with HTTPS.

## Done = ALL of these
- [ ] Signup → email verify → login → password reset all work
- [ ] Realtor submits license → ARELLO (mocked or live) → verified badge
- [ ] `ModeratableMixin` exists; AI pipeline tested with adversarial prompt-injection fixtures
- [ ] `ActionLog` + `AccessLog` populated automatically
- [ ] Django admin requires TOTP; IP allowlist on destructive routes
- [ ] Homepage / About / Guidelines / Privacy / Terms / Login / Signup / Verify-Email / Password-Reset all polished, responsive, a11y AA
- [ ] Playwright e2e covers: signup→verify→login, realtor license verify, admin 2FA, moderation pipeline
- [ ] Deployed at public URL with HTTPS, CSP, HSTS

## Models (final shape — see master plan for full Python)
- `User` (email login, role flags)
- `RealtorProfile` (license_number, license_type, verification_status, headshot, bio, brokerage)
- `VendorProfile` (skeleton — business_name, status)
- `LicenseCheck` (audit row per ARELLO call)
- `ModeratableMixin` (abstract — moderation_status, score, moderated_at)
- `ModerationDecision` (Generic FK → any moderatable, layer, output, action, actor)
- `Flag` (Generic FK → any moderatable, reporter, reason)
- `ActionLog` (every staff write, before/after JSON)
- `AccessLog` (every staff route hit)

## Streams + tasks (30 atomic)

### Stream A — Scaffold (4 tasks)
- [ ] **A1** Bootstrap Django + uv + settings split (base/dev/prod) + django-environ
- [ ] **A2** docker-compose.yml: postgres + redis + healthchecks + .env.example
- [ ] **A3** Celery + Beat (config/celery.py + dummy task)
- [ ] **A4** pytest-django + pytest-cov + factory-boy + smoke test

### Stream B — Design system + base templates (5 tasks)
- [ ] **B1** Tailwind config (vrov-new tokens) + Cormorant Garamond + tracking utility
- [ ] **B2** Vite bundles Tailwind + Alpine + Motion One + HTMX → static/dist; Whitenoise serves
- [ ] **B3** templates/base.html (head, header, footer, scripts)
- [ ] **B4** _components/ partials (button, card, input, modal, hero, badge)
- [ ] **B5** _scroll_reveal.html + Alpine x-reveal directive (IntersectionObserver + Motion One, prefers-reduced-motion)

### Stream C — User + auth (5 tasks)
- [ ] **C1** Custom User model + managers
- [ ] **C2** django-allauth (email signup, email verify required, password reset)
- [ ] **C3** RealtorProfile + VendorProfile skeleton models
- [ ] **C4** Override allauth templates with design system
- [ ] **C5** /profile page (HTMX edit)

### Stream D — License verification (4 tasks)
- [ ] **D1** apps/accounts/services/arello.py — REST client (sandbox env)
- [ ] **D2** LicenseCheck model + verify_license_task + reverify_all beat (every 30 days)
- [ ] **D3** /realtor/verify page — form + HTMX polling for status
- [ ] **D4** Tests: mock ARELLO success/expired/revoked/down → state transitions + log entries

### Stream E — AI moderation core (4 tasks)
- [ ] **E1** ai_classifier.py — Gemini wrapper, strict JSON schema response
- [ ] **E2** injection_guard.py — wrap UGC in `<UNTRUSTED_USER_CONTENT>`, fail-closed to `queue` on bad output
- [ ] **E3** pipeline.py + deterministic.py + ModeratableMixin + post-save signal → Celery task
- [ ] **E4** 30+ adversarial fixtures + tests asserting pipeline never `allow`s on attack inputs

### Stream F — Audit + admin lockdown (3 tasks)
- [ ] **F1** ActionLog + AccessLog + signals + middleware
- [ ] **F2** django-otp (TOTP) + django-axes (throttle) + IP allowlist on destructive admin URLs
- [ ] **F3** Custom ModelAdmin per model (explicit list_display / search / readonly)

### Stream G — Public polished pages (4 tasks)
- [ ] **G1** Homepage — hero + value props + how-it-works + CTAs (`/copy-editing` skill for body copy)
- [ ] **G2** About — mission + story + contact
- [ ] **G3** Guidelines — render community standards from markdown source
- [ ] **G4** Privacy + Terms — placeholder copy w/ WA notes (replace pre-launch with attorney version)

### Stream H — Test + deploy (5 tasks)
- [ ] **H1** Playwright critical paths: signup, license verify, admin 2FA, moderation pipeline
- [ ] **H2** Multi-stage Dockerfile (Vite build → Python install → static collect)
- [ ] **H3** railway.json (or fly.toml) + /healthz endpoint
- [ ] **H4** Cloudflare in front: DNS, SSL, WAF, R2 bucket, image-resize
- [ ] **H5** Production smoke test + docs/RUNBOOK.md

## Skills per stream
| Stream | Skill |
|---|---|
| All code | `/caveman` |
| G1–G4 (text) | `/copy-editing` |
| B1–B5 (visual) | `/frontend-design` |
| Pre-merge | `/superpowers:requesting-code-review` |
| End of phase | `/security-review` |
| E (sensitive) | `/karpathy-guidelines` |
| Multi-task waves | `/dispatching-parallel-agents` |

## Execution flow per task
1. Pick next pending task
2. TDD where applicable (failing test first)
3. Implement
4. Run tests: `pytest apps/<app>/tests/`
5. Run lint: `ruff check . && ruff format . && djlint templates/`
6. Atomic commit (Conventional Commits)
7. Mark `[x]`
8. Next

## Verification (Phase 1 done)
- `pytest` green, ≥80% coverage on accounts/moderation/audit
- `npx playwright test` green
- `python manage.py check --deploy` clean
- Lighthouse `/` mobile ≥ 95 perf / 100 a11y / 100 best-practices / 100 SEO
- axe-core: zero violations on / /about /login /signup /realtor/verify
- Manual: signup→verify→login→submit-license→badge appears
- Manual: admin login → forced TOTP setup → admin reachable
- Manual: prompt-injection fixture → queued not allowed
- Production URL live with HTTPS
- `docs/RUNBOOK.md` exists

## Risks
- ARELLO sandbox not granted in time → mock client; flip to live key when granted
- Gemini false positives on real estate slang → log every decision; tune severity in Phase 6
- Visual drift from vrov-new bar → end-of-phase side-by-side screenshot review
- New prompt injection vectors → adversarial fixture set is living

## Dependencies
- Reads: `docs/research/design-system-reference.md`, `docs/research/arello-api-notes.md`, `docs/research/platform-guidelines-v1.md`, `docs/research/ai-moderation-prompt-injection.md`, `docs/adr/*`
- Writes: All apps, all templates, deploy config — substrate for Phase 2+
