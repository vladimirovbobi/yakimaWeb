---
sprint: 6
title: Content/Order Delivery Service (9th container)
status: done
date: 2026-05-04
plan_file: .planning/phases/sprint-6-delivery-service/PLAN.md
---

# Sprint 6 — Delivery Service

## Goal

Vendor → buyer asset delivery via a standalone FastAPI service. Photos,
virtual-tour archives, websites (zip), n8n workflow exports (json),
documents — all delivered through the platform with audit trail and signed
URL access.

## What landed

### FastAPI service ([delivery/](../../../delivery/))

- `delivery/main.py` — six endpoints under `/api/delivery/v1/`:
  - `POST /packages` (vendor creates package)
  - `POST /packages/{id}/files` (vendor uploads file with magic-byte validation)
  - `POST /packages/{id}/finalize` (vendor finalizes; webhook → Django flips Lead to WON)
  - `GET  /packages/{id}/manifest` (buyer or vendor sees what's inside)
  - `GET  /packages/{id}/files/{file_id}` (buyer downloads via 5-min signed URL)
  - `GET  /packages/{id}/access-log` (vendor sees who accessed what)
- `delivery/auth.py` — JWT verification using Django's `SECRET_KEY` + HS256
  (matches SimpleJWT config). Accepts both `Authorization: Bearer` and
  `yw_access` cookie.
- `delivery/db.py` — SQLAlchemy async models mirroring Django's `apps/delivery/`
  schema. Postgres via `asyncpg`.
- `delivery/storage.py` — R2 S3-compatible client; falls back to local
  filesystem in dev when no R2 keys configured.
- `delivery/validation.py` — extension allowlist + per-class size cap +
  magic-byte content sniff. JPG/PNG/WebP/HEIC/TIFF/JPG/ZIP/7Z/PDF/DOCX/JSON.
- `delivery/Dockerfile` — Python 3.12-slim, uvicorn, healthcheck.
- `delivery/requirements.txt` — pinned versions.

### Django side ([apps/delivery/](../../../apps/delivery/))

- `models.py` — `DeliveryPackage`, `DeliveryFile`, `DeliveryAccessLog`. Schema
  source-of-truth; FastAPI uses these tables via SQLAlchemy.
- `migrations/0001_initial.py` — initial schema.
- `api/views.py`:
  - `FinalizeWebhookView` — HMAC-signed webhook receiver from delivery service;
    flips `Lead.status` to `WON`. Idempotent.
  - `MyDeliveriesView` — `/api/v1/me/deliveries/` for the buyer dashboard's
    "deliveries received" list.
- `api/urls.py` — both routes wired.
- `INSTALLED_APPS` updated; `config/api_urls.py` includes `apps.delivery.api.urls`
  under `/api/v1/delivery/`.
- `DELIVERY_WEBHOOK_SECRET` env wired in `config/settings/base.py`.

### Infrastructure

- `docker-compose.yml` — new `delivery` service entry. Caddy already routes
  `/api/delivery/*` to it (added in Sprint 2 Caddyfile rewrite). Volume
  `delivery_dev_uploads` for local FS fallback.

## Security model

- **Vendor uploads** authenticate via main-platform JWT, verified by Django's
  SECRET_KEY in this service.
- **Buyer downloads** require both JWT + lead-buyer match.
- **Webhook back to Django** uses HMAC-SHA256 with `DELIVERY_WEBHOOK_SECRET`.
  Idempotent — re-firing is a no-op.
- **File validation** is magic-byte-based, not Content-Type-trusted.
- **Per-class size limits**: 50MB images, 500MB archives, 25MB documents,
  5MB workflow exports.
- **Signed URLs** are 5-minute TTL; buyer must re-request after expiration.
- **Anti-virus scan** on archives is dispatched to img-worker (clamav already
  in container ecosystem) — currently `scan_status="skipped"` until the
  scanner integration lands; tracked as a Sprint 9 follow-up.
- **CORS** restricted to localhost:3000 + localhost.

## What's deferred

- Frontend UI: vendor "deliver assets" tab on `/vendor/leads/[id]` and buyer
  "view deliveries" tab on `/dashboard/leads/[id]`. The backend is complete;
  the Next.js side is a separate ~1-day task that should land alongside
  Sprint 4's lead-messaging UI.
- Real anti-virus scan dispatch. ClamAV is in the dependency tree but the
  scan-status flip lands in Sprint 9 hardening.
- Stripe-integrated payment-on-delivery flow. Locked deferred per ADR-0004.

## Verification

- ⚠ Delivery service boot: gated on Docker (cannot run in this session).
- ✓ Django side: migration file syntax verified by Django's loader (static).
- ✓ FastAPI types: PEP 484 + pydantic-settings; not run-checked.
- ⚠ End-to-end test: needs Docker; Playwright spec to be added in Sprint 9.

## Lessons

- **Schema-in-Django, reads-via-SQLAlchemy is a clean split.** Migrations stay
  unified; the FastAPI service just declares matching column names.
- **`postgresql+asyncpg://` URL prefix** must be different from Django's
  `postgres://` driver string — easy to copy-paste wrong.
- **`Authorization` and `Cookie` headers** are both legitimate carriers. A
  delivery service must accept both because vendors might upload via curl
  scripts (Bearer) and the dashboard uses cookies.

## Cross-links

- ADR-0010 (new): Delivery service container — write canonical doc to
  `docs/adr/0010-delivery-service.md` next.
- Security audit: [[../Security/sprint-6-audit]]
- Predecessor: [[sprint-5-mod-console]] (audit-and-tighten)
