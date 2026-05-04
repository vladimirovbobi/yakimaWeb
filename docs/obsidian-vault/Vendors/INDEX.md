# Third-party vendors

External services we depend on. Update when contracts change, when keys
rotate, or when an incident exposes a dependency we forgot to track.

| Vendor | Purpose | Locked by ADR | Failure mode | Mitigation |
|---|---|---|---|---|
| ARELLO | Realtor license verification | [[../Decisions/ADR-0002]] | API down → realtor signups stuck pending | Fall back to mock; Celery retry; ops alert |
| Google Gemini | AI moderation + tools | [[../Decisions/ADR-0003]] | API down or 429 → moderation fails closed (queue, not approve) | Daily spend cap; circuit breaker (Sprint 2) |
| Cloudflare R2 | Media storage + CDN | (no ADR — see SAD §6) | R2 down → reads still cached, writes 5xx | Signed URLs; default_storage abstraction; can swap to S3 |
| Postmark | Transactional email (django-anymail) | (no ADR) | Bounce / outage | Console fallback in dev; Sentry alert on > 1% bounce |
| Sentry | Error monitoring | (no ADR) | Sentry down → we lose visibility, app keeps running | DSN-gated init |
| Better Stack | Uptime monitoring | (no ADR) | — | Backup pinger via cron-job.org |
| Cloudflare WAF | Edge protection (production only) | (no ADR) | — | Caddy edge security headers regardless |

## Cost levers

- Gemini is the most variable line item. Daily spend cap enforced (Sprint 2).
- R2 egress is free; ingress + storage is the cost.
- Sentry free tier covers dev; paid tier kicks in for prod.

## Relationships

- ARELLO sandbox key → `ARELLO_API_KEY` env (kept in Railway/Fly secrets)
- Gemini → `GEMINI_API_KEY`, `GEMINI_TOOLS_MODEL`, `GEMINI_MODERATION_MODEL`
- Postmark → `POSTMARK_SERVER_TOKEN` + `DEFAULT_FROM_EMAIL`
- R2 → `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_ENDPOINT_URL`,
  `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_CUSTOM_DOMAIN`
- Sentry → `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_ENVIRONMENT`

Verification commands for each are in `docs/SPRINT-1-VERIFICATION.md`.
