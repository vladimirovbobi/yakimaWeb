# Sprint 6 — Content/Order Delivery Service (NEW 9th container)

> Predecessor: Sprint 5. Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

New standalone service that handles vendor → buyer asset delivery: photos, virtual-tour archives, websites (zip), n8n workflow exports (json), automation packages, documents. Storage on Cloudflare R2; per-lead delivery package metadata in Postgres; signed-URL access (5-min TTL) gated by lead status.

## Architecture

- **Service:** FastAPI app (separate from Django). Lightweight, no ORM dependency. Reads/writes Postgres via SQLAlchemy.
- **Container:** new entry `delivery` in `docker-compose.yml`. Caddy routes `/api/delivery/*` → `delivery:8001`.
- **DB:** New tables — `delivery_packages`, `delivery_files`, `delivery_access_log`. Migrations live in Django (single source of truth) but FastAPI reads through SQLAlchemy.
- **Storage:** Cloudflare R2 bucket `yakimaweb-deliveries/` (separate from main `yakimaweb-prod/`).
- **Auth:** Service-to-service token issued by Django on lead creation. Buyer JWT also accepted on read endpoints. Vendor JWT accepted on write endpoints.

## Endpoints (v1)

- `POST /api/delivery/v1/packages` — vendor uploads multi-file delivery (multipart, up to 1GB total). Returns package_id.
- `GET /api/delivery/v1/packages/{id}/manifest` — buyer sees what's inside (filenames, sizes, types). Requires lead-id + buyer-token match.
- `GET /api/delivery/v1/packages/{id}/files/{filename}` — signed-URL redirect to R2 with 5-min TTL. Logs to delivery_access_log.
- `POST /api/delivery/v1/packages/{id}/finalize` — vendor marks delivery complete; webhook to Django flips Lead.status to `won` (if not already).
- `GET /api/delivery/v1/packages/{id}/access-log` — vendor-only, returns who accessed and when.

## File-type rules

- **Images** (.jpg, .png, .webp): up to 50MB each, max 200 files per package.
- **Archives** (.zip, .7z): up to 500MB each, max 5 per package. Anti-virus scan via `clamav` worker (already in docker-compose img-worker).
- **JSON** (n8n workflow exports): up to 5MB each. Schema-validated against n8n export format on upload.
- **Documents** (.pdf, .docx): up to 25MB each. PDF stripped of JS via PyMuPDF.
- **Websites** (.zip with index.html at root): treated as archive + extracted to read-only static-served bucket on finalize. Buyer gets `https://deliveries.yakimaweb.com/{package_id}/` permalink.
- **Other**: explicitly disallowed in v1. Document the allow-list.

## Tasks

1. Bootstrap `delivery/` directory: `delivery/main.py` (FastAPI), `delivery/db.py` (SQLAlchemy), `delivery/r2.py` (storage client), `delivery/auth.py` (JWT verify), `delivery/Dockerfile`.
2. Migrations: Django adds `apps/delivery/` (model-only app, no views) with `DeliveryPackage`, `DeliveryFile`, `DeliveryAccessLog` models.
3. Add `delivery` service to `docker-compose.yml`; Caddy `/api/delivery/*` route.
4. Vendor UI: new tab in `/vendor/leads/[id]` for "Deliver assets" — drag-drop multi-file upload, per-file progress, finalize button.
5. Buyer UI: new tab in `/dashboard/leads/[id]` for "View deliveries" — list of finalized packages, per-file download links.
6. Tests: pytest for FastAPI endpoints, Playwright E2E for full vendor-upload-→-buyer-download flow.

## Verification

- Vendor uploads 50 photos + 1 PDF + 1 n8n.json → package created, all files visible in manifest
- Buyer downloads a photo → signed URL works, expires after 5min, second click works (re-signs)
- Anti-virus scan: upload an EICAR test file → rejected
- Access log captures every download with IP + UA
- Lead.status flips to "won" on finalize

## Sign-off

- [ ] FastAPI delivery service running on port 8001 in docker-compose
- [ ] All 5 endpoints functional with auth
- [ ] File-type rules enforced (sizes, counts, content scanning)
- [ ] Vendor + buyer UIs wired
- [ ] R2 bucket configured with signed URLs
- [ ] pytest + Playwright green
- [ ] Sprint 6 commit pushed; ADR-0010 logged for the new service
