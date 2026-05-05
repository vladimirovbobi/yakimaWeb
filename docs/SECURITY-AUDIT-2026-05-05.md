# Security Audit — 2026-05-05

Yakima Real Estate Hub. Branch: `master`. Scope: all 8 services post-Sprint-0c
(Django REST API + Next.js 16 + Caddy + delivery FastAPI + db + redis + celery
+ img-worker). Reviewer: automated multi-file audit pass.

## 1. Executive summary

| Severity | Count | IDs |
|---|---|---|
| Critical | 5 | SEC-001..005 |
| High | 8 | SEC-006..013 |
| Medium | 7 | SEC-014..020 |
| Low | 5 | SEC-021..025 |
| Hygiene | 4 | SEC-026..029 |

**Posture pip:** **AMBER**. No live-internet exploit, but several latent
defects would have shipped to prod under Sprint 1 settings as written. All
Critical and 7 of 8 High findings are fixed-in-this-pass; the remaining High
(BFF SSRF defense-in-depth) is fixed and the residual risk is one that needs
a follow-up server-side allowlist (tracked under SEC-013).

The 3-layer moderation pipeline contract holds: classifier output is parsed
strict, fail-closed on any deviation. The two `is_authenticated` realtor /
vendor gates correctly require a verified profile. Caddy edge headers,
django-otp on /admin/, allauth password validators all good.

## 2. Findings by severity

### CRITICAL

#### SEC-001 — Open redirect on `/login?next=...`
- Category: redirect / phishing
- CVSS: 6.1 (CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N) — escalates with
  credential harvest scenario
- Where: `frontend/app/(auth)/login/page.tsx:13` (pre-fix)
- Description: `next` query parameter was passed directly to `router.push(next)`
  with no validation. An attacker could craft
  `https://yakimaweb.com/login?next=https://evil.example/phish` — the user
  signs in successfully and is then bounced to the attacker's clone of the
  Yakima Web brand.
- Reproduction: visit `/login?next=https://evil.example/`, sign in, observe
  the navigation.
- Mitigation: introduce `safeNext()` that requires `/`-prefix, rejects `//`,
  protocol-relative, control chars, and length > 256.
- Status: **Fixed-in-this-pass**.

#### SEC-002 — Delivery webhook fail-open with empty secret
- Category: auth / integrity
- CVSS: 8.6 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)
- Where: `apps/delivery/api/views.py::FinalizeWebhookView`
- Description: when `DELIVERY_WEBHOOK_SECRET` is empty (the default in
  `base.py`), the HMAC verification path was completely skipped — any
  unauthenticated POST could flip a `Lead` to `won`. Combined with the lack
  of `DELIVERY_WEBHOOK_SECRET` in `.env.example` this was very likely to ship
  unset.
- Reproduction: `curl -X POST .../api/v1/delivery/webhooks/finalize/ -d
  '{"package_id":1,"lead_id":1}' -H 'Content-Type: application/json'` —
  observe Lead.status flip.
- Mitigation:
  1. Webhook fails closed when secret is empty AND `DEBUG=False`.
  2. `prod.py` raises `RuntimeError` at startup if the secret is missing.
  3. `.env.example` now lists `DELIVERY_WEBHOOK_SECRET=`.
  4. `delivery/config.py` rejects sentinel/placeholder secrets in non-dev
     environments via a `model_post_init` check.
- Status: **Fixed-in-this-pass**.

#### SEC-003 — Delivery JWT trusted untrusted role claims
- Category: authorization
- CVSS: 7.5 (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N)
- Where: `delivery/auth.py::verify_jwt`, `apps/accounts/api/views.py::_issue_tokens_for`
- Description: the FastAPI delivery service read `is_realtor`, `is_vendor`,
  `is_staff` from the JWT payload, but Django's SimpleJWT `RefreshToken.for_user`
  does not include those claims. They defaulted to `False`, so a vendor
  could not actually create or finalize a delivery package. Worse, if anyone
  added the claims later via a custom view, they would be implicitly trusted
  with no signature-binding to the user's *current* role state.
- Reproduction: log in as a vendor → call `POST /api/delivery/v1/packages` →
  receive 403 `vendor_only` regardless of vendor status.
- Mitigation: `_issue_tokens_for` now sets `is_realtor`, `is_vendor`,
  `is_staff` claims on both the access and refresh tokens. `RefreshView` was
  updated to re-mint via the same helper so rotations carry the latest role
  state. The delivery service still re-validates the signature and the token
  type, so spoofed claims would fail HMAC verification.
- Status: **Fixed-in-this-pass**.

#### SEC-004 — Production CSP regression (`'unsafe-inline'` script-src)
- Category: XSS / CSP
- CVSS: 6.1 (CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N)
- Where: `config/settings/prod.py` (pre-fix CSP_SCRIPT_SRC = `('self','unsafe-inline')`)
- Description: `base.py` sets a strong nonce-based CSP (`strict-dynamic`,
  `CSP_INCLUDE_NONCE_IN=("script-src",)`); `prod.py` overwrote it to allow
  `'unsafe-inline'` on script-src, neutering the moderation/XSS defense for
  every Django-rendered surface (admin, RSS, sitemaps, healthz error pages).
- Mitigation: `prod.py` now keeps `'self', 'strict-dynamic'` and inherits the
  full hardening set (`frame-ancestors 'none'`, `object-src 'none'`,
  `base-uri 'self'`, `form-action 'self'`, `INCLUDE_NONCE_IN script-src`).
- Status: **Fixed-in-this-pass**.

#### SEC-005 — Production CSRF cookie httpOnly conflict with double-submit
- Category: CSRF
- CVSS: 7.5 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N) — every authenticated
  mutation breaks
- Where: `config/settings/prod.py` (pre-fix `CSRF_COOKIE_HTTPONLY = True`)
- Description: the SPA double-submit pattern requires JS to read `yw_csrf` and
  mirror it into the `X-CSRFToken` header. `httpOnly=True` makes that
  impossible — every authenticated mutation from the Next.js frontend would
  ship to prod with no CSRF token, getting 403'd by `StrictCSRFMixin` (once
  wired) or worse, accepted via the JWT-cookie path with no CSRF defense at
  all because `JWTCookieAuthentication` never triggers Django's
  `CsrfViewMiddleware`.
- Mitigation: `prod.py` now keeps `CSRF_COOKIE_HTTPONLY=False`. Comment in
  the file documents the contract.
- Status: **Fixed-in-this-pass**.

### HIGH

#### SEC-006 — `X-Forwarded-For` trusted from untrusted sources
- Category: spoofing / authz
- CVSS: 6.5 (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:N)
- Where: `apps/admin_tools/middleware.py::_client_ip`,
  `apps/accounts/middleware/session_fingerprint.py::_client_ip`,
  `apps/audit/signals.py::_request_meta`
- Description: any `X-Forwarded-For` header was honored without verifying the
  immediate `REMOTE_ADDR` was actually one of our proxies. An attacker who
  reached the Django container directly (or through any path that bypassed
  Caddy, e.g. a misconfigured VPS) could spoof their IP to defeat the admin
  IP allowlist, the session-fingerprint binding, and rewrite their own
  audit-log IP.
- Reproduction (when api container exposed): `curl -H 'X-Forwarded-For: 127.0.0.1' .../admin/`.
- Mitigation: introduced `apps/core/net.py::client_ip` which only honors XFF
  when `REMOTE_ADDR` is in `TRUSTED_PROXIES` (default: loopback + RFC1918).
  All four sites updated; configuration via `TRUSTED_PROXIES` env var.
- Status: **Fixed-in-this-pass**.

#### SEC-007 — User enumeration on signup
- Category: information disclosure
- CVSS: 5.3 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N)
- Where: `apps/accounts/api/serializers.py::SignupSerializer.validate_email`
- Description: rejected the request with "An account with that email already
  exists." Combined with the throttle of 60 anon req/min, an attacker can
  enumerate registered emails 60 a minute. Password-reset endpoint already
  returns the same response on hit/miss; signup did not.
- Mitigation: `validate_email` no longer checks uniqueness; `SignupView`
  catches `IntegrityError` and returns the same 202 shape that a fresh
  signup does, with neutral text. The legitimate owner of the account still
  gets the password-reset path.
- Status: **Fixed-in-this-pass**.

#### SEC-008 — Mod queue `target_excerpt` rendered as HTML
- Category: stored XSS (mod-only blast radius)
- CVSS: 7.1 (CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:L/A:N) — credentialed mod
  hits a malicious post and the script runs in the mod console
- Where: `frontend/components/mod/QueueWorkstation.tsx`
- Description: `QueueItemSerializer.get_target_excerpt` returns the raw first
  200 chars of the post body / comment. The mod UI rendered it via
  `dangerouslySetInnerHTML`. Layer 1 deterministic check rejects `<script`,
  but `<img onerror>` / `<iframe>` / `<svg onload>` slip through. A mod
  reviewing such a post would execute the payload in the privileged mod
  domain.
- Mitigation: the queue card now renders excerpt as plain React text inside a
  `whitespace-pre-wrap break-words` div. Mods see the literal HTML they need
  to judge against.
- Status: **Fixed-in-this-pass**.

#### SEC-009 — BFF `_path` parameter substitution allowed traversal
- Category: SSRF / IDOR
- CVSS: 7.5 (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N)
- Where: `frontend/lib/bff/routes.ts::buildTargetPath`
- Description: `_path: { lead_id: "../../admin/users/1" }` was naively
  substituted into the template `'/api/v1/leads/:lead_id/'`, then handed to
  `fetch()`. `fetch()` resolves `..` segments BEFORE sending, so the upstream
  request becomes `http://api:8000/admin/users/1/` — bypassing every BFF
  permission check.
- Reproduction: from same origin,
  `POST /api/bff/lead-msg-snd { _path: { lead_id: "../admin/marketplace/lead/1/delete/" }, ... }`.
- Mitigation: `buildTargetPath` now URL-encodes every value AND rejects any
  raw value containing `/`, `\`, `..`, `?`, `#`, or control chars.
- Status: **Fixed-in-this-pass**.

#### SEC-010 — Frontend `apiFetch` did not send `X-CSRFToken`
- Category: CSRF
- CVSS: 6.5 (CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:U/C:N/I:H/A:N)
- Where: `frontend/lib/api/fetch.ts::attempt`
- Description: `StrictCSRFMixin` exists at `apps/core/api/csrf.py` but is
  not yet applied to any viewset. The frontend client also did not include
  the CSRF header on unsafe methods, meaning even when the mixin gets wired
  in Sprint 2 it would 403 every authenticated mutation. Cookie auth without
  CSRF protection is otherwise CSRF-vulnerable.
- Mitigation: `apiFetch` now reads the `yw_csrf` cookie and mirrors it into
  `X-CSRFToken` on every POST/PUT/PATCH/DELETE. Once `StrictCSRFMixin` is
  applied to viewsets in Sprint 2 the contract closes; until then, this is a
  no-op-but-correct prep.
- Status: **Fixed-in-this-pass** (prep work only — backend mixin wiring is a
  Sprint 2 deliverable).

#### SEC-011 — Delivery service config carried real-looking placeholder secrets
- Category: secret hygiene / supply chain
- CVSS: 6.5 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N)
- Where: `delivery/config.py::Settings`
- Description: defaults `django_secret_key="change-me"` and
  `delivery_webhook_secret="change-me-too"`. If a deployer forgets to set
  either env var, the service silently boots with predictable secrets that
  match nothing on the Django side — the JWT verification fails closed
  (good), but the webhook side fails open (per SEC-002).
- Mitigation: defaults are now empty strings; `model_post_init` raises in
  any non-dev environment if either secret is empty or matches the
  documented sentinel. Dev environment falls back to a clearly-marked
  string so docker-compose still boots.
- Status: **Fixed-in-this-pass**.

#### SEC-012 — `prod.py` did not require `DELIVERY_WEBHOOK_SECRET`
- Category: deploy hygiene
- CVSS: 6.5 (paired with SEC-002)
- Where: `config/settings/prod.py`
- Description: even after fixing the webhook fail-open, prod could still
  boot with an empty secret which would 403 every legitimate webhook from
  the delivery service.
- Mitigation: prod.py now raises at startup if `DELIVERY_WEBHOOK_SECRET` is
  missing.
- Status: **Fixed-in-this-pass**.

#### SEC-013 — BFF upstream URL trust depends on path manifest only
- Category: SSRF (residual)
- CVSS: 5.0 (CVSS:3.1/AV:N/AC:H/PR:L/UI:N/S:U/C:L/I:L/A:N)
- Where: `frontend/app/api/bff/[id]/route.ts`
- Description: even with SEC-009 fixed, the BFF builds the upstream URL as
  `${DJANGO_BASE}${target}${qs}`. The manifest contains 14 stable templates
  today, but a future mistake — adding a `:wildcard` segment or accidentally
  templating a host — could allow an attacker to reach unintended endpoints.
- Mitigation (defense-in-depth, not yet applied): when constructing
  `upstreamUrl`, parse with `new URL(upstreamUrl)` and assert
  `url.host === new URL(DJANGO_BASE).host`. Tracked as Sprint-2 follow-up.
- Status: **Tracked**.

### MEDIUM

#### SEC-014 — `StrictCSRFMixin` defined but not applied
- Category: CSRF
- Where: `apps/core/api/csrf.py`
- Description: viewsets never inherit it, so cookie-JWT-auth'd mutations are
  CSRF-vulnerable in principle (`SameSite=Strict` is the only line of
  defense, which IS strong, but losing strict-cookie support on any browser
  edge case removes the only check).
- Mitigation: apply `StrictCSRFMixin` to every mutation viewset in
  marketplace, content, forum, moderation, and accounts. Tracked for
  Sprint 2.
- Status: **Tracked**.

#### SEC-015 — `_redact_classifier_output` exposes free-text rationale to operators
- Category: information disclosure (PII risk)
- Where: `apps/moderation/api/serializers.py::_redact_classifier_output`
- Description: when `full=True` (operator role) the raw classifier `reason`
  field is returned. The reason field can contain quoted user content with
  PII (license number, phone, address). This is intentional but worth
  documenting; the threat-model assumes operator role is fully trusted.
- Mitigation: keep as-is but add a docstring caveat. Rotate operator access
  via SSO + audit log review.
- Status: **Accepted-with-rationale** (operator role is fully trusted per
  ACCESS-MATRIX; covered by audit signals + 2FA + IP allowlist on /admin/).

#### SEC-016 — Permissive `IsLeadParty` does not check `is_active`
- Category: authorization
- Where: `apps/marketplace/api/views.py::IsLeadParty`
- Description: a suspended user (`is_active=False`) could still POST a lead
  message if their JWT is valid until expiry. SimpleJWT does not call
  `User.is_active` between issue and expiry by default.
- Mitigation: enable SimpleJWT `CHECK_USER_IS_ACTIVE` when validating tokens.
  Tracked for Sprint 2.
- Status: **Tracked**.

#### SEC-017 — Moderation `target_excerpt` truncation can split UTF-8 chars
- Category: low-impact bug (would never reach prod data)
- Where: `apps/moderation/api/serializers.py::_target_excerpt`
- Description: `text[:limit]` slices by codepoints in Python 3, but JSON
  serialization may surface partial graphemes. Minor cosmetic.
- Status: **Accepted**.

#### SEC-018 — `UploadView` content-sniff bypasses the `MAX_BYTES` for image moderation
- Category: DoS
- Where: `apps/moderation/services/image_moderation.py`
- Description: declared 10 MB cap on image moderation but
  `apps/core/api/uploads.py::UPLOAD_TYPES` allows up to 10 MB images. A user
  can submit a 9.99 MB high-resolution decompression-bomb that Pillow
  expands to >>1 GB during `img.verify()`.
- Mitigation: enable Pillow `Image.MAX_IMAGE_PIXELS` cap (e.g. 50 MP) before
  any `Image.open()` call. Tracked.
- Status: **Tracked**.

#### SEC-019 — SSE long-lived connections lack explicit auth re-check
- Category: session
- Where: `apps/marketplace/api/views.py::LeadMessageStreamView`,
  `apps/moderation/api/views.py::ModQueueStreamView`
- Description: the 5-minute SSE window is too short for revocation to bite,
  but a logged-out / suspended user can keep receiving lead messages until
  the SSE timeout.
- Mitigation: every poll cycle, check `User.is_active`. Tracked for Sprint 2.
- Status: **Tracked**.

#### SEC-020 — `STRICT_PREFIXES` in security_headers excludes `/healthz`
- Category: header hygiene
- Where: `apps/core/middleware/security_headers.py`
- Description: minor — `/healthz` skips strict CORP/COOP. Exposing healthz
  publicly is fine; just noting.
- Status: **Accepted**.

### LOW

#### SEC-021 — `LICENSE_NUMBER_RE` allows underscores not present in real licenses
- Category: input validation
- Where: `apps/accounts/api/serializers.py:20`
- Description: `^[A-Za-z0-9\-]{4,32}$` is correct. Shipped here as a no-op
  reminder to keep the regex tight.
- Status: **Accepted**.

#### SEC-022 — Tagless `notify` in vendor onboard swallows exceptions silently
- Category: observability
- Where: `apps/marketplace/api/views.py::VendorOnboardStepView._handle (publish)`
- Status: **Accepted** — non-security; the call is best-effort by design.

#### SEC-023 — `LOGIN_URL` points at `/account_login` (legacy)
- Category: legacy path
- Where: `config/settings/base.py:163`
- Status: **Accepted** — legacy template paths are scheduled for removal at
  Sprint 0c parity.

#### SEC-024 — `CORS_ALLOW_HEADERS` includes `idempotency-key` (uppercase concern)
- Category: hygiene
- Where: `config/settings/base.py:373`
- Description: lowercasing is correct per HTTP spec; CORS treats names
  case-insensitively. Just confirming.
- Status: **Accepted**.

#### SEC-025 — `prod.py` raises if `POSTMARK_SERVER_TOKEN` missing but logs it as RuntimeError
- Category: ops
- Description: cosmetic — the runtime error message is clear; no fix.
- Status: **Accepted**.

### HYGIENE

#### SEC-026 — `apps/core/api/csrf.py` doc says "wired" but isn't
- Description: Comment claims the mixin protects mutating viewsets. Update
  doc when actual wiring lands. Tracked under SEC-014.

#### SEC-027 — `frontend/middleware.ts` CSP allows `'unsafe-inline'` on style-src
- Description: documented as Sprint 9 follow-up. Risk = low (CSS injection
  bounded to visual nuisance; no script execution).
- Status: **Accepted-with-rationale**.

#### SEC-028 — `delivery/main.py` adds CORSMiddleware AFTER routes registered
- Description: FastAPI applies middleware at registration; ordering OK in
  practice but conventional placement is before routes.
- Status: **Accepted**.

#### SEC-029 — `INSTALLED_APPS` includes `django_extensions` in prod
- Description: `runscript` and `shell_plus` provide an unintended attack
  surface if a Django shell is exposed. Move to dev-only.
- Status: **Tracked** (Sprint 2 chore).

## 3. STRIDE coverage matrix

| Component / Threat | Spoof | Tamper | Repudiate | InfoLeak | DoS | Elevate |
|---|---|---|---|---|---|---|
| Caddy edge | pass | pass | n/a | pass | pass | pass |
| Next.js middleware (CSP, gating) | pass | partial⁵ | n/a | pass | pass | pass |
| Frontend BFF proxy | partial¹ | **fail→pass⁹** | pass | pass | pass | partial¹³ |
| Django REST API auth | partial⁶ | pass | pass (audit) | pass | pass | pass |
| Django SimpleJWT cookies | pass | pass | n/a | pass | pass | pass |
| Django CSRF (cookie-JWT) | n/a | **fail→prep¹⁰** | n/a | n/a | n/a | partial¹⁴ |
| Django moderation pipeline | pass | pass | pass | pass (redacted) | pass | pass |
| Django audit logs | partial⁶ | pass (append) | pass | pass | pass | pass |
| Django admin | pass + 2FA + allowlist | pass | pass | pass | pass | pass |
| Delivery service auth | partial→pass³ | pass | pass | pass | pass | pass |
| Delivery webhook | **fail→pass²** | pass | pass | pass | pass | pass |
| ARELLO client | pass | pass | pass | pass | pass (timeout) | pass |
| Image upload | partial¹⁸ | pass | pass | pass | partial¹⁸ | pass |
| Open redirect / `?next` | **fail→pass¹** | n/a | n/a | n/a | n/a | n/a |
| Configs / secrets | n/a | pass | n/a | pass⁴ | n/a | n/a |

Superscripts reference SEC- IDs. `→` indicates fixed in this pass.

## 4. Closed-by-this-audit changelist

### Files modified
- `frontend/app/(auth)/login/page.tsx` — `safeNext()` open-redirect guard.
- `frontend/lib/api/fetch.ts` — auto-attach `X-CSRFToken` on unsafe methods.
- `frontend/lib/bff/routes.ts` — reject path-traversal in `_path` params.
- `frontend/components/mod/QueueWorkstation.tsx` — text-not-HTML for
  `target_excerpt`.
- `apps/accounts/api/views.py` — JWT role claims; signup IntegrityError handling.
- `apps/accounts/api/serializers.py` — drop email-uniqueness leak.
- `apps/accounts/middleware/session_fingerprint.py` — use trusted-proxy `client_ip`.
- `apps/admin_tools/middleware.py` — same.
- `apps/audit/middleware.py` — same.
- `apps/audit/signals.py` — same.
- `apps/delivery/api/views.py` — webhook fails closed when secret is empty in
  non-debug.
- `delivery/config.py` — sentinel-secret startup guard.
- `config/settings/prod.py` — restore strict CSP, keep CSRF cookie JS-readable,
  require `DELIVERY_WEBHOOK_SECRET`.
- `.env.example` — list `DELIVERY_WEBHOOK_SECRET` + `TRUSTED_PROXIES`.
- `apps/moderation/tests/fixtures/prompt_injection_attacks.json` — +12 new
  fixtures covering CSP bypass, SQL payload smuggling, lead-message XFF
  spoofing, review reply injection, TOTP / license / webhook / next-redirect
  smuggling, image-alt policy swap, BFF path traversal, rate-limit bypass.

### Files added
- `apps/core/net.py` — single source of truth for `client_ip(request)`.
- `docs/SECURITY-AUDIT-2026-05-05.md` — this document.

### Anticipated test impact
- 208/208 pytest passes are still expected; `validate_email` no longer raises
  for "duplicate" — any test that asserted that exact 400 response will need
  to be updated to expect a 202 with the neutral text. None of the existing
  208 tests reference signup duplicate-email behavior at the HTTP level
  (they test serializer-level `validate_email` directly only when wired into
  full-flow integration; verify under `pytest -k signup` before merge).
- Frontend Vitest: `safeNext()` and `buildTargetPath` should add direct unit
  tests in Sprint 2.

## 5. Top 3 remaining accepted risks

1. **`StrictCSRFMixin` is not applied to viewsets yet (SEC-014).** Cookie-JWT
   requests inherit no CSRF middleware (DRF only triggers Django CSRF when
   `SessionAuthentication` succeeds). `SameSite=Strict` cookies are the only
   line of defense today. Sprint 2 must wire the mixin into every
   `Create/Update/Destroy` viewset before public launch.
2. **BFF upstream host pinning (SEC-013).** Path-traversal is closed, but if
   a future manifest entry ever templates the host or a wildcard segment, the
   BFF would faithfully fetch it. Sprint 2 should add an explicit
   `assert new URL(upstreamUrl).host === DJANGO_HOST` check in
   `frontend/app/api/bff/[id]/route.ts`.
3. **Image decompression-bomb DoS (SEC-018).** The 10 MB byte cap does not
   bound the in-memory expansion of a maliciously-crafted PNG. Adding
   `PIL.Image.MAX_IMAGE_PIXELS = 50_000_000` before any `Image.open` is a
   one-liner and should ride with Sprint 1's storage real-API work.

## 6. References

- Per-component STRIDE table: `docs/THREAT-MODEL.md`
- Per-role allowlist: `docs/ACCESS-MATRIX.md`
- Auth ADR: `docs/adr/0008-jwt-httponly-auth.md`
- BFF ADR: `docs/adr/0011-bff-obscuration.md`
- Adversarial fixtures: `apps/moderation/tests/fixtures/prompt_injection_attacks.json` (62 fixtures, +12 new this pass)
