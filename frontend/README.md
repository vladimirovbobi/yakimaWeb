# Yakima Real Estate Hub - Frontend

Next.js 15 App Router frontend for Yakima Real Estate Hub.

## Quick start

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

App at `http://localhost:3000`. Django API at `http://localhost:8000`.

## Stack

- Next.js 15 (App Router, RSC, standalone output)
- React 19 RC
- Tailwind 3 + Cormorant Garamond serif + Raleway sans
- Framer Motion for animation
- TanStack Query for client-side data
- Playwright + Vitest for tests
- JWT auth via httpOnly cookies (`yw_access`, `yw_refresh`) - issued by Django

## Conventions

- Server-first: RSC by default; `"use client"` only where needed
- Strict TypeScript, no `any`
- Tailwind tokens locked to `styles/tailwind.config.ts` - match vrov-new visual bar
- Mobile-first; `sm:` is the smallest breakpoint

## E2E tests (Playwright)

```bash
npm install
npx playwright install --with-deps chromium webkit

# Start backend on :8000
docker compose up -d api db redis

# Start frontend on :3000 (auto-started by Playwright if not already running)
npm run dev &

# Seed test data
docker compose exec api python manage.py seed_all

# Run all specs (chromium-desktop + webkit-mobile + chromium-mobile)
npm run test:e2e

# Run only the desktop project
npm run test:e2e -- --project=chromium-desktop

# Run only the mobile projects
npm run test:e2e -- --project=webkit-mobile --project=chromium-mobile
```

### Env vars

- `PLAYWRIGHT_BASE_URL` - override the frontend URL (default `http://localhost:3000`).
- `E2E_BACKEND_URL` - backend URL for healthz polling in `global-setup.ts` (default `http://localhost:8000`).
- `E2E_REQUIRE_BACKEND=1` - fail global setup if backend is unreachable (default: warn-only).
- `E2E_USE_REAL_AUTH=1` - exercise the real Django login/signup endpoints (otherwise they're mocked). Requires `seed_all` to have created the test users.
- `E2E_TEST_USER_EMAIL` / `E2E_TEST_USER_PASSWORD` - override the realtor test user (default `demo-realtor@yakimaweb.local` / `TestPass123!`).
- `E2E_VENDOR_EMAIL` / `E2E_VENDOR_PASSWORD` - vendor test user.
- `E2E_OPERATOR_EMAIL` / `E2E_OPERATOR_PASSWORD` - operator/staff test user.

### Optional dev deps

- `@axe-core/playwright` - required by `accessibility.spec.ts`. If absent, the a11y suite skips itself rather than failing. Install with `npm install --save-dev @axe-core/playwright`.

## Brand assets

All brand placeholder art lives under `frontend/public/`. Generate with:

```bash
make assets    # from repo root
```

Asset paths:

| Asset | Path | Source |
|---|---|---|
| Wordmark logo | `public/logo.svg` | hand-authored SVG |
| Mark only | `public/logo-mark.svg` | hand-authored SVG |
| Favicon SVG | `public/favicon.svg` | hand-authored SVG |
| Favicon ICO (multi-size) | `public/favicon.ico` | `scripts/generate_favicons.py` |
| Apple touch icon | `public/apple-touch-icon.png` | `scripts/generate_favicons.py` |
| PWA icons | `public/icon-192.png`, `public/icon-512.png` | `scripts/generate_favicons.py` |
| Hero placeholders | `public/img/hero/hero-{home,blog,services,community,tools}.jpg` | `scripts/generate_hero_placeholders.py` |
| Post placeholders (10) | `public/img/posts/post-{1..10}.jpg` | `scripts/generate_post_placeholders.py` |
| Service placeholders (12) | `public/img/services/service-{1..12}.jpg` | `scripts/generate_service_placeholders.py` |
| Avatar placeholders (8) | `public/img/avatars/avatar-{1..8}.jpg` | `scripts/generate_avatar_placeholders.py` |
| Vendor logo placeholders (8) | `public/img/vendors/vendor-logo-{1..8}.jpg` | `scripts/generate_vendor_logo_placeholders.py` |
| Forum thread placeholders (6) | `public/img/threads/thread-{1..6}.jpg` | `scripts/generate_thread_placeholders.py` |
| Furniture remover demo | `public/img/samples/furniture-remover/{before,after}-{1,2,3}.jpg` | `scripts/generate_furniture_remover_samples.py` |
| Empty-state illustrations | `public/img/empty/empty-{leads,posts,services,notifications,search}.svg` | hand-authored SVG |
| OG image samples | `public/og-samples/og-{blog,marketplace,forum}.png` | `manage.py regen_og_images --demo` |

CSS color tokens are exposed as both Tailwind classes (`bg-gold`, `text-ivory`)
and CSS variables in `app/globals.css` (`--yw-gold`, `--yw-ivory`, etc.) for
use in custom CSS and embedded iframes.

### Placeholder fallback (deterministic)

The platform never shows a hollow card. `lib/placeholders.ts` exposes
`postPlaceholder`, `servicePlaceholder`, `avatarPlaceholder`,
`vendorLogoPlaceholder`, and `threadPlaceholder` — each takes a seed
(usually a slug or id) and returns the same JPEG path on every reload.
The hash is stable across server and client renders, so refresh always
shows the same placeholder for the same item.

Wired into:

- `components/content/PostCard.tsx`, `Comment.tsx` — post hero + author avatar
- `components/marketplace/ServiceCard.tsx` — service hero
- `components/marketplace/VendorChip.tsx` — vendor logo
- `components/forum/ThreadCard.tsx` — thread thumbnail
- `app/(public)/blog/[slug]/page.tsx` — detail hero + author avatar
- `app/(public)/services/[slug]/page.tsx` — gallery fallback
- `app/(public)/services/vendors/[slug]/page.tsx` — vendor logo
- `app/(public)/community/threads/[slug]/page.tsx` — author avatars (incl. replies)
- `components/marketing/CuratedFeed.tsx` — homepage feed cards
- All section heroes (`/blog`, `/services`, `/community`, `/tools`, `/`)

To swap real photos in: drop the new file into the matching
`public/img/<dir>/`, then update the API to return a real URL on the
relevant model field. The fallback never fires once the API returns
a non-null `hero_image_url` (or `logo_url` / `avatar_url`).

Every demo image carries a tiny `[demo]` corner pip — easy to spot in
production so swaps are obvious.

### Replace before launch

Every generated asset is marked with `[demo]` or a `DEMO` watermark. Swap with
real art before going live:

- [ ] Wordmark logo (final designer cut)
- [ ] Hero photos (real Yakima Valley imagery — vineyards, riverfronts, downtown)
- [ ] Post hero photos (real photography per post)
- [ ] Service hero photos (vendor-supplied)
- [ ] Vendor avatars + logos (vendor-supplied)
- [ ] Forum thread thumbnails (or remove if not part of v1 visual scope)
- [ ] Founder / team photos for `/about`
- [ ] Real photographer-supplied before/after pairs for the furniture-remover demo
- [ ] Final OG image template review (typography, font files)

Brand source of truth: `../docs/research/design-system-reference.md`.
Voice + tone: `../docs/COPY-STYLE-GUIDE.md`.

## See also

- Root: `../CLAUDE.md`
- Docs: `../docs/RUNBOOK.md`, `../docs/SAD.md`, `../docs/adr/`
