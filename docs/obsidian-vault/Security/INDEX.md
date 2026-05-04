# Security

The threat model, security playbook, and per-sprint security audits.

## Authoritative docs

- `docs/THREAT-MODEL.md` — STRIDE-based threat model
- `docs/SECURITY-PLAYBOOK.md` — incident response runbooks
- `docs/SECURITY-PHASE1.md` — Phase 1 baseline security review
- `docs/SECURITY-FINAL.md` — Sprint 2 production polish (CSP, OTP, rate limits, headers)
- `docs/THREAT-MODEL.md` — adversarial fixtures + injection-guard matrix

## Per-sprint audits

| Sprint | Audit note | Severity findings | Resolved |
|---|---|---|---|
| 2 | [[sprint-2-audit]] | low | yes |
| 6 | [[sprint-6-audit]] | medium | yes |
| 7 | [[sprint-7-audit]] | low | yes |
| 9 | [[sprint-9-audit]] | — | final pass |

## The five non-negotiables

1. **The moderation pipeline never approves an attack.** Fail closed. Adversarial fixtures live in `apps/moderation/tests/fixtures/prompt_injection_attacks.json` and grow every sprint.
2. **Every license verification is auditable.** ARELLO calls write a `LicenseCheck` row with the raw response. No deletes.
3. **Every staff write logs to `ActionLog`.** Model-layer signal, not view-layer; admin actions get logged too.
4. **Admin behind 2FA + IP allowlist.** `django-otp` TOTP, `AdminIPAllowlistMiddleware`. SMS is forbidden (SIM-swap).
5. **Every UGC pipe inherits `ModeratableMixin`.** No exceptions. Post-save signal triggers Celery `moderate_content`.

## What we ship per surface

- HTTPS-only via Caddy, HSTS preload after first prod cert
- CSP enforced (no `unsafe-inline`), nonce per request
- COOP/COEP/X-Frame-Options/Referrer-Policy/Permissions-Policy
- DRF throttles: per-user, per-IP, per-vendor depending on endpoint
- Caddy rate limit: per-IP token bucket, stricter on /api/v1/auth/login
- JWT in httpOnly + SameSite=Strict cookies; CSRF double-submit on writes
- File upload: size + extension + content scan via img-worker
- Server-side validation on every input (DRF serializers); client validation is UX only

Cross-links: [[../Architecture/Overview]] · [[../Sprints/INDEX]]
