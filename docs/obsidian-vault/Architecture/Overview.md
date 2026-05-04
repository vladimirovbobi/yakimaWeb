---
title: Architecture overview
last_updated: 2026-05-04
status: locked v1
---

# Architecture overview

Locked architectural decisions (changing any of these requires a new ADR that
supersedes the existing one).

## System shape

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Browser │ ──> │  Caddy  │ ──> │ Next.js │  ─┐
└─────────┘     │  edge   │     │ frontend│   │
                │ TLS+WAF │     └─────────┘   │
                │ rate-lim│                   │
                └─────────┘                   │
                     │                        │
                     ├───> Django REST API ◄──┘  (server components)
                     │     /api/v1/* and
                     │     /api/public/v1/*
                     │
                     └───> Delivery service (FastAPI) — Sprint 6
                           /api/delivery/*
```

**Containers (10 services post-Sprint 6):**

| Service | Image | Purpose |
|---|---|---|
| `caddy` | xcaddy + rate-limit | edge: TLS, WAF, security headers, per-IP rate limit |
| `frontend` | Next.js 15 standalone | React 19 RSC, route groups, BFF (Sprint 7) |
| `api` | Django 5.x DRF + Celery | core API, admin, ORM |
| `db` | Postgres 16 + pgvector schema | data, FTS, future embeddings |
| `redis` | Redis 7 | cache, sessions, Celery broker, rate buckets |
| `celery` | Django + Celery worker | async tasks (general queue) |
| `beat` | Celery beat | scheduler (license recheck, anomaly detector, digests) |
| `img-worker` | Pillow-heavy worker | dedicated `images` queue (furniture remover, image compressor, scans) |
| `delivery` | FastAPI + asyncpg | vendor → buyer asset delivery (Sprint 6) |
| `migrate` | one-shot | runs migrations, exits |

## Locked decisions (ADR backlinks)

- [[../Decisions/ADR-0001]] — Django monolith (superseded by ADR-0005)
- [[../Decisions/ADR-0002]] — ARELLO for license verification
- [[../Decisions/ADR-0003]] — Gemini as AI provider
- [[../Decisions/ADR-0004]] — Lead-gen-only marketplace v1
- [[../Decisions/ADR-0005]] — Split architecture (DRF + Next.js + Caddy)
- [[../Decisions/ADR-0006]] — Next.js App Router
- [[../Decisions/ADR-0007]] — Caddy reverse proxy
- [[../Decisions/ADR-0008]] — JWT in httpOnly + SameSite=Strict cookies
- [[../Decisions/ADR-0009]] — pgvector future-proof schema
- [[../Decisions/ADR-0010]] — Delivery service container (Sprint 6)
- [[../Decisions/ADR-0011]] — BFF / network-tab obscuration (Sprint 7)

## What we're not building

- Microservices beyond the container split. The 10 services are the cap.
- Native mobile apps. Web is mobile-responsive.
- Stripe / escrow / payments in v1. Lead-gen only per ADR-0004.
- MLS integration without a stable source contract.
- A separate analytics database. Postgres + Sentry are it for v1.

## Where to find things in code

- `apps/accounts/` — User, RealtorProfile, VendorProfile, ARELLO client
- `apps/content/` — polymorphic Post, Comment, NewsletterSubscription, SocialEmbed
- `apps/forum/` — ForumThread, ForumReply, Vote (generic FK)
- `apps/marketplace/` — Category tree, Service, Package, Bundle, BundleItem, Lead, LeadMessage, Review
- `apps/tools/` — Tool registry, ToolUsage; description writer, furniture remover, image compressor
- `apps/moderation/` — 3-layer pipeline, ModeratableMixin, injection guard
- `apps/audit/` — ActionLog, AccessLog, anomaly detector
- `apps/operations/` — operator dashboard
- `apps/admin_tools/` — IP allowlist, OTP enforcement, role decorators
- `apps/notifications/` — Notification model, signal hooks, email digest
- `apps/core/` — TimeStampedModel, validators, throttles, auth shared
- `frontend/app/(public)/` — public pages (no login required)
- `frontend/app/(auth)/` — login / signup / 2FA / password reset
- `frontend/app/(dashboard)/` — gated by middleware (yw_access cookie)
- `frontend/components/` — UI kit + feature components
- `frontend/lib/api/` — fetch wrappers + TanStack Query hooks
- `delivery/` — FastAPI service (Sprint 6)

Cross-links: [[../README]] · [[../Sprints/INDEX]] · [[../Security/INDEX]]
