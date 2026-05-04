# Sprint 2 — Production Polish (Security + Performance)

> Predecessor: `sprint-1-brand-foundation` (Sprint 1 deliverables landed in master plan; see `docs/SPRINT-1-VERIFICATION.md` for the gate it must clear before this sprint starts).
> Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Take the seeded, welcoming-homepage stack from Sprint 1 to production-grade: enforced CSP nonces, per-endpoint rate limits, 2FA for staff, AI spend hard cap, Lighthouse ≥ 95, axe-core zero violations, mobile audit clean across 375/414/768/1024.

## Tasks

1. **CSP nonces enforced.** Migrate the existing CSP from report-only to enforced. Server-render a per-request nonce in Next.js middleware; thread it through to inline scripts (the JSON-LD blocks in root layout + page-specific JSON-LD). Remove any `unsafe-inline` from `script-src`. Verify with browser console — zero violations on every public page.
2. **Rate limits, two layers.**
   - Caddy edge: per-IP token bucket via `caddy-rate-limit` plugin. Allow 30 req/s/IP burst, 10 req/s sustained. Stricter on `/api/v1/auth/login` (5/min/IP) and `/api/v1/tools/*` (10/min/IP).
   - DRF throttle classes: `apps/core/throttles.py` — per-user throttle for tool endpoints, per-vendor throttle for lead-message creation, per-IP throttle for unauth read endpoints. Wire into DRF `DEFAULT_THROTTLE_CLASSES`.
3. **Staff 2FA enforced.** `django-otp` with TOTP. Middleware: any `is_staff` request to `/admin/` or `/mod/` or `/ops/` without verified TOTP redirects to `/2fa/setup`. Already-existing 2FA setup page at `frontend/app/(auth)/2fa/setup/page.tsx` — wire backend enforcement.
4. **AI spend hard cap.** `apps/tools/services/spend_cap.py` already has `check_budget()`. Add a daily limit per user + a global daily limit (env var `GEMINI_DAILY_BUDGET_USD`). Tool endpoints call `check_budget()` pre-flight; on budget exceeded, return `429 SpendCapExceeded` with retry-after seconds.
5. **Lighthouse 95+.**
   - Image: migrate hero/og placeholders to next/image where local; remote URLs (Pexels) stay as `<img>` with width/height for CLS.
   - JS: dynamic-import below-the-fold components (`CuratedFeed` slices) where useful; avoid Framer Motion on bots (use `prefers-reduced-motion` media query as proxy).
   - Fonts: subset Cormorant Garamond + Raleway; add `unicode-range` if size matters; `font-display: swap` already on.
   - Caching: ensure Caddy serves static assets with `Cache-Control: public, max-age=31536000, immutable`.
6. **axe-core zero.** Run axe on every public page. Fix any color-contrast violations (gold on warm panels is the usual offender). Add aria-labels where missing.
7. **Mobile audit.** 375 / 414 / 768 / 1024 screen widths. Per-page sweep:
   - No horizontal scroll
   - Touch targets ≥ 44×44
   - Sticky header doesn't cover anchor links (already partially fixed via `scroll-padding-top`)
   - Hero copy doesn't truncate awkwardly
   - Card grid collapses cleanly to 1-col on 375px
8. **Security headers.** Caddy adds: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=(), camera=(), microphone=()`, HSTS with `preload` (after first prod cert).

## Verification

```bash
docker compose up -d
# Lighthouse on key pages
docker compose exec frontend npx lighthouse http://localhost/ --view --quiet --chrome-flags="--headless" --only-categories=performance,accessibility,best-practices,seo
docker compose exec frontend npx lighthouse http://localhost/blog/ --quiet --chrome-flags="--headless"
docker compose exec frontend npx lighthouse http://localhost/services/ --quiet --chrome-flags="--headless"
# axe-core
docker compose exec frontend npx @axe-core/cli http://localhost/
# CSP enforcement
curl -sI http://localhost/ | grep -i "content-security-policy"
# Rate limit
seq 1 100 | xargs -P 20 -I{} curl -s -o /dev/null -w "%{http_code}\n" http://localhost/api/public/v1/posts/ | sort | uniq -c
```

Expected: Lighthouse ≥ 95 on all four categories, all four pages. axe-core zero serious/critical. CSP header enforced (no Report-Only). Rate limit returns ~10% 429s under 100-burst test.

## Sign-off

- [ ] All 4 Lighthouse categories ≥ 95 on `/`, `/blog`, `/community`, `/services`
- [ ] axe-core zero serious/critical on all public pages
- [ ] CSP enforced (Report-Only header removed)
- [ ] DRF throttle + Caddy rate-limit returning 429s under burst
- [ ] Staff 2FA setup blocks `/admin/`, `/mod/`, `/ops/` without verified TOTP
- [ ] AI spend cap returns `429 SpendCapExceeded` when daily budget hit
- [ ] Mobile audit clean across 4 breakpoints on 6+ pages
- [ ] All security headers present
- [ ] pytest + ruff + djlint + frontend lint green
- [ ] Sprint 2 commit pushed; `docs/STATE-OF-THE-PROJECT.md` updated
