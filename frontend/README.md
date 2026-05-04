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

## See also

- Root: `../CLAUDE.md`
- Docs: `../docs/RUNBOOK.md`, `../docs/SAD.md`, `../docs/adr/`
