# Phase 1 Security Review

> Manual review of authentication, license verification, AI moderation, audit, and admin lockdown. Date: 2026-05-03.

## Scope reviewed
- `apps/accounts/` (User, RealtorProfile, ARELLO client, verify flow)
- `apps/moderation/` (3-layer pipeline, prompt-injection guard)
- `apps/audit/` (ActionLog + AccessLog signals + middleware)
- `apps/admin_tools/` (IP allowlist + 2FA + role decorators)
- `config/settings/` (base + dev + prod)
- `templates/account/` (allauth overrides) + `templates/accounts/`

## Verdicts

### Critical (block release)
**None.**

### High (fix before public launch, not blockers for staging)

1. **CSP `unsafe-inline` for scripts + styles** — `config/settings/prod.py` line 30 has `CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")`. Phase 8 should tighten by switching to nonce-based CSP after Vite build outputs nonces.
2. **No CSRF refresh in HTMX polling endpoints** — `templates/accounts/_status_partial.html` uses `hx-get` polling which Django CSRF allows for GET, but if the partial moves to POST in Phase 5+ this needs `hx-headers='{"X-CSRFToken": "..."}'`. Currently OK since GET-only.
3. **`ALLOWED_HOSTS` defaults to localhost** in `base.py`. Production env vars must override or production deploy fails closed. Already documented in `docs/RUNBOOK.md`.

### Medium

4. **ARELLO client has 10s timeout but no circuit breaker** — `apps/accounts/services/arello.py` line 76 sets `timeout=10`. If ARELLO is sustained down, every signup hits a 10s wait. Phase 6 should add a Redis-backed circuit breaker.
5. **`apps/moderation/services/ai_classifier.py` has no per-call cost tracking** — Gemini spend cap (`GEMINI_DAILY_SPEND_CAP_USD`) is set in env but not enforced in code yet. Phase 3 will add `apps/tools/models.py::ToolUsage` which extends to Layer 2 too.
6. **Session cookie name `yw_sessionid` is custom but doesn't differentiate per-surface** — per the original design the moderator console + operator dashboard should each have their own scope. Not yet split. Acceptable in Phase 1 (no surfaces exist yet); Phase 6 must add `SESSION_COOKIE_NAME` overrides per surface.

### Low

7. **`bleach` is a dependency but not yet imported anywhere** — pre-emptive for Phase 2 (Post body sanitization). Drop or document.
8. **`apps/audit/signals.py::AUDITED_MODELS` is a hardcoded set** — when Phase 2+ adds Post / Comment / Vendor / Lead / Review, this set MUST be updated. Add a CI check that asserts every model in apps/{content,marketplace,forum} is in `AUDITED_MODELS`.
9. **Admin IP allowlist applies to `/admin/` only** — middleware `PROTECTED_PREFIXES` only protects Django admin. When Phase 6 adds `/mod/` and `/operator/`, add them.
10. **No `Content-Security-Policy` `report-uri`** — Phase 8 should wire to a logging endpoint or Sentry.

## Things checked + cleared

- ✅ **Password storage** — using Django default Argon2 → PBKDF2 chain
- ✅ **CSRF** — middleware enabled; HTMX includes token via `main.js` `htmx:configRequest` hook
- ✅ **SQL injection** — only ORM, no raw SQL anywhere
- ✅ **XSS** — Django templates auto-escape; no `|safe` on user content (only on `body_html` on `_card.html` which is reserved for trusted org content)
- ✅ **Mass assignment** — all ModelForm `Meta.fields` are explicit allowlists (no `__all__`)
- ✅ **Secrets in env** — no hardcoded keys, `.env.example` has zero real values, `.gitignore` excludes `.env`
- ✅ **Open redirects** — allauth's `LOGIN_REDIRECT_URL` is hardcoded; no user-supplied `next=` accepted without validation
- ✅ **Login throttling** — `django-axes` 5 failures / 1h cooloff
- ✅ **Email verification** — `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` (no unverified accounts can log in)
- ✅ **Generic FK target validation** — `ModerationDecision.target_type` uses `SET_NULL` on delete, which is correct (we want the audit row to outlive the target)
- ✅ **Audit append-only** — `LicenseCheckAdmin`, `ModerationDecisionAdmin`, `ActionLogAdmin`, `AccessLogAdmin` all override `has_delete_permission` to return False
- ✅ **Prompt injection** — pipeline parser fails closed; 32 adversarial fixtures; pre-flag pattern coverage at 100% (32/32) after pattern tightening

## Test coverage of security-critical paths

- ✅ `apps/accounts/tests/test_arello.py` — 6 tests cover ACTIVE / NOT_FOUND / EXPIRED / SUSPENDED / 429 / 503
- ✅ `apps/accounts/tests/test_models.py::TestRealtorProfileSignal` — verified→is_realtor / revoked→strips role
- ✅ `apps/accounts/tests/test_verification_flow.py` — end-to-end with signal cascade
- ✅ `apps/moderation/tests/test_injection_guard.py` — 14 unit tests on parser fail-closed + adversarial fixture coverage
- ✅ `apps/moderation/tests/test_pipeline.py` — adversarial contract test (no attack ever returns approve)
- ✅ `apps/admin_tools/tests/test_ip_allowlist.py` — exact / CIDR / IPv6 / invalid / empty allowlist
- ⏳ `apps/audit/tests/test_audit.py` — staff-write logging test exists; expand in Phase 6

## Recommended actions before Phase 2

| # | Action | Owner | Severity |
|---|---|---|---|
| 1 | Tighten CSP nonces in Phase 8 | Backend | High |
| 2 | Document `ALLOWED_HOSTS` env requirement in RUNBOOK | Done | Info |
| 3 | Add CI check that `AUDITED_MODELS` covers every app/models.py model with UGC | Phase 2 | Medium |
| 4 | Wire ARELLO circuit breaker | Phase 6 | Medium |
| 5 | Add Gemini per-call cost ledger | Phase 3 | Medium |

## Checks run

```bash
python manage.py check --deploy   # prod settings: 0 issues
pytest apps/                      # 61/61 passing
ruff check .                      # not yet run; Phase 1 closeout
```

## Sign-off

Phase 1 codebase is **safe to proceed to Phase 2**. The 10 findings above are tracked
for follow-up in their respective phases. No blockers.
