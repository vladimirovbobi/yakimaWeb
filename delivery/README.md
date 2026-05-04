# Delivery Service

Standalone FastAPI service for vendor → buyer asset delivery. Sprint 6 of the
master plan.

## What it does

Vendors deliver assets (photos, virtual-tour archives, websites, n8n workflow
exports, automation packages, documents) to buyers through this service. Each
delivery is scoped to a `Lead` row in the main Django database. Files live in
Cloudflare R2 under `deliveries/` prefix; access goes through 5-minute signed
URLs.

This service is intentionally separate from Django because:

1. The upload pipeline is heavy enough to warrant its own process
   (multipart streaming, anti-virus scan dispatch, archive validation).
2. Failure modes don't take down the rest of the platform.
3. We can scale this container independently if delivery volume spikes.

## Endpoints (v1)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/delivery/v1/packages` | vendor JWT | Create a package row, returns `package_id` and a short-lived upload token |
| `POST` | `/api/delivery/v1/packages/{id}/files` | upload-token | Stream a file into R2; appends a `DeliveryFile` row |
| `POST` | `/api/delivery/v1/packages/{id}/finalize` | vendor JWT | Mark delivery complete; webhook to Django flips Lead status to `won` |
| `GET`  | `/api/delivery/v1/packages/{id}/manifest` | buyer JWT | What's in this package — filenames, sizes, types |
| `GET`  | `/api/delivery/v1/packages/{id}/files/{filename}` | buyer JWT | Signed-URL redirect (5min TTL) |
| `GET`  | `/api/delivery/v1/packages/{id}/access-log` | vendor JWT | Who accessed what, when (paginated) |

## File-type rules

Server-validated on upload:

| Class | Extensions | Per-file limit | Per-package count |
|---|---|---|---|
| Images | .jpg, .jpeg, .png, .webp, .heic, .tiff | 50 MB | 200 |
| Archives | .zip, .7z | 500 MB | 5 |
| Documents | .pdf, .docx | 25 MB | 50 |
| Workflow exports | .json (n8n schema-validated) | 5 MB | 20 |
| Websites | .zip with `index.html` at root | 500 MB | 1 |

Anything else → 400.

PDFs are stripped of embedded JS via PyMuPDF. Archives are scanned by ClamAV
on the img-worker container before they're marked accessible.

## Authentication model

- **Vendor uploads** authenticate with their main-platform JWT (`yw_access`
  cookie passed through, validated against the same SECRET_KEY).
- **Buyer downloads** authenticate with the buyer's JWT, additionally
  validated against the `Lead.buyer_id` of the package's owning lead.
- **Service-to-service** webhook (Django ← delivery) uses an HMAC-signed
  shared secret in `DELIVERY_WEBHOOK_SECRET` env.

## Storage

- R2 bucket `yakimaweb-deliveries/` (separate from main `yakimaweb-prod/`).
- Object key format: `packages/{package_id}/{file_uuid}-{filename}`.
- Signed URLs: 5 minute TTL, signed by the delivery service (R2 keys never
  leave this container).

## Database

The `apps/delivery/` Django app owns the schema — Django runs migrations,
this service reads/writes via SQLAlchemy against the same tables. Single
source of truth lives in Django models.

Tables:

- `delivery_packages` — one row per delivery from a vendor to a buyer
- `delivery_files` — files attached to a package
- `delivery_access_log` — every read access logged with IP + UA

## Local development

```bash
docker compose up -d delivery
curl http://localhost:8001/healthz
```

In dev mode the service uses Django's local filesystem storage instead of R2
when `AWS_S3_ENDPOINT_URL` is unset.

## Cross-references

- ADR-0010: Delivery service container
- Sprint plan: `.planning/phases/sprint-6-delivery-service/PLAN.md`
- Obsidian retro: `docs/obsidian-vault/Sprints/sprint-6-delivery.md`
