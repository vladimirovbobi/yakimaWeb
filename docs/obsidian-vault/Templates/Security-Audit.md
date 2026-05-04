---
sprint: N
date:
auditor:
status: pass | conditional-pass | fail
---

# Security audit — Sprint N

## Surfaces touched

List every public route, API endpoint, model, or service modified.

## Threat model deltas

What new attack surface did this sprint introduce? What was retired?

## Checklist

- [ ] All UGC inputs flow through `ModeratableMixin`
- [ ] All staff-write paths log to `ActionLog`
- [ ] All `is_staff` reads log to `AccessLog`
- [ ] Every new file upload has size + type + content scan
- [ ] Every new third-party API call has spend cap + retry policy
- [ ] No new secrets committed; env-only
- [ ] CSP enforced (no `unsafe-inline` regression)
- [ ] All inputs validated on the server, not just the client
- [ ] Rate limit applied where appropriate
- [ ] Object-level permissions checked on detail/update/delete
- [ ] No sensitive data in URL parameters
- [ ] Error responses don't leak internals (Problem Details, not stack traces)
- [ ] OWASP top-10 sweep: SSRF / SQLi / XSS / CSRF / IDOR / SSRF / file-upload

## Findings

| Severity | Issue | Where | Remediation |
|---|---|---|---|

## Cross-links

- Sprint retro: [[../Sprints/sprint-N-name]]
- Threat model: `docs/THREAT-MODEL.md`
