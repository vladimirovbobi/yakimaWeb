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

## See also

- Root: `../CLAUDE.md`
- Docs: `../docs/RUNBOOK.md`, `../docs/SAD.md`, `../docs/adr/`
