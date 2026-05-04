---
sprint: 6
date: 2026-05-04
auditor: project-team
status: pass with deferred items
---

# Security audit — Sprint 6 (Delivery service)

## Surfaces touched

- New container: `delivery` (FastAPI, port 8001)
- New Django app: `apps/delivery/` (models + webhook receiver)
- New Caddy route: `/api/delivery/*` → delivery container
- New Postgres tables: `delivery_packages`, `delivery_files`, `delivery_access_log`

## Threat model deltas

- **NEW attack surface:** A new HTTP service accessible behind Caddy. A
  bug in the delivery service can leak files or accept malicious uploads.
- **NEW attack surface:** Webhook endpoint on Django side can be invoked
  by anyone unless HMAC-protected.
- **NEW attack surface:** Storage paths in R2 — if pattern is predictable,
  enumeration becomes a risk. Mitigated by uuid4-prefixed object keys.

## Checklist

- [x] All file uploads have size cap (per-class: 50MB image, 500MB archive,
      25MB document, 5MB workflow)
- [x] All file uploads have extension allow-list (10 extensions)
- [x] All file uploads have magic-byte content sniff (don't trust
      Content-Type)
- [x] JWT verification uses Django's SECRET_KEY + HS256 (matches SimpleJWT)
- [x] Buyer downloads require `Lead.buyer_id` match
- [x] Vendor uploads require `Lead.vendor_id` match
- [x] Webhook back to Django is HMAC-SHA256 signed when secret configured
- [x] Webhook is idempotent (re-firing flips status only if not already won)
- [x] Access log writes IP + UA on every read
- [x] CORS limited to localhost origins in dev
- [x] FastAPI docs/openapi disabled in prod (`docs_url=None`)
- [x] No new secrets committed; env-only (DELIVERY_WEBHOOK_SECRET)
- [x] Storage paths use uuid4 prefixes (not enumerable)

## Findings

| Severity | Issue | Where | Remediation |
|---|---|---|---|
| Medium | `scan_status="skipped"` until ClamAV dispatch is wired | `delivery/main.py:upload_file` | Ship in Sprint 10 polish; defer behind a feature flag |
| Low | Webhook signature verification only enforced when `DELIVERY_WEBHOOK_SECRET` set | `apps/delivery/api/views.py:FinalizeWebhookView` | Production deploy must set this in env; documented in `docs/SPRINT-1-VERIFICATION.md` |
| Low | Dev fallback to local FS storage when no R2 keys | `delivery/storage.py` | Acceptable for dev; production has the keys |
| Info | Eventual consistency between FastAPI finalize and Django Lead.WON | webhook latency | Buyers may briefly see "open" then "won"; acceptable |

## Cross-links

- Sprint retro: [[../Sprints/sprint-6-delivery]]
- ADR: `docs/adr/0010-delivery-service.md`
