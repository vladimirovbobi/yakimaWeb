# ADR-0010: Content/Order Delivery Service (FastAPI 9th container)

**Status:** Accepted
**Date:** 2026-05-04
**Deciders:** Project team

## Context

Vendors need to deliver assets to buyers through the platform: photos,
virtual-tour archives, websites (zip), n8n workflow exports (json),
automation packages, documents. The platform must:

1. Store the assets durably with audit trail.
2. Gate access so only the lead's buyer (or the vendor) can download.
3. Track who accessed what, when.
4. Support large file uploads (multi-megapixel images, multi-hundred-MB
   archives) without taking down the rest of the platform.

The Django + Celery stack could absorb this, but:

- Multi-part streaming uploads block gunicorn workers in undesirable ways.
- A delivery-volume spike shouldn't degrade the public site or the moderation
  pipeline.
- The audit/access patterns are tightly scoped — a small focused service is
  easier to reason about and to scale independently.

## Decision

Add a 9th container, `delivery`, running a FastAPI app on port 8001. It:

- Reads/writes the `delivery_packages`, `delivery_files`,
  `delivery_access_log` tables via SQLAlchemy + asyncpg.
- Stores blobs in Cloudflare R2 (separate bucket from main media).
- Authenticates with the same Django `SECRET_KEY` (HS256 JWT).
- On finalize, posts an HMAC-signed webhook to Django to flip `Lead.status`
  to `WON`.
- Validates uploads with magic-byte content sniff + per-class size caps.
- Runs behind Caddy at `/api/delivery/*`.

Schema source-of-truth stays in Django (`apps/delivery/`). Django runs
migrations; FastAPI just reads the live tables.

## Consequences

### Easier

- Delivery volume can scale independently of Django.
- Async uploads don't compete with gunicorn for workers.
- A delivery-service crash doesn't take down the public site.
- File validation is co-located with the upload path.

### Harder

- One more deploy artifact to manage (Dockerfile, dependencies, version
  alignment with Django on JWT format).
- Two services share a database; schema migrations must be backward-
  compatible during rolling deploys.
- Webhook back to Django introduces an eventual-consistency edge case: the
  package is finalized at the delivery service, but the Lead may briefly
  not show `WON` until the webhook lands.

### Locked-in

- The schema is now bi-tied (Django + SQLAlchemy). Field renames require
  migrating both; coordinate carefully.
- This service is part of the deploy topology forever now; we can absorb it
  back into Django but only by removing the delivery container and
  re-implementing the streaming upload path.

## Alternatives considered

- **Absorb into Django via Streaming.** Plausible but blocks gunicorn
  workers; would need ASGI-mode Django to handle streaming uploads cleanly.
  Rejected because the codebase is WSGI-Django (DRF default) and migrating
  is more disruptive than adding a focused service.
- **AWS Lambda + S3 direct upload.** Cheaper at low volume, more complex at
  high volume. Locked-in to AWS ecosystem; we're committed to R2/Cloudflare.
- **Use signed PUT URLs to upload directly to R2.** Eliminates the upload
  through our servers, but bypasses our magic-byte validation and means the
  client must implement multi-step coordination with the platform. Rejected
  for v1; can be layered in later as a "fast path" for vendors with very
  large uploads.

## Cross-references

- Sprint plan: `.planning/phases/sprint-6-delivery-service/PLAN.md`
- Sprint retro: `docs/obsidian-vault/Sprints/sprint-6-delivery.md`
- Implementation: `delivery/` and `apps/delivery/`
- Supersedes / superseded by: none
