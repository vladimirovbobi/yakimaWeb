# ADR-0008: JWT Authentication via httpOnly Cookies with CSRF Double-Submit

- **Status:** Accepted
- **Date:** 2026-05-03
- **Supersedes:** —
- **Superseded by:** —
- **Deciders:** Yakima Real Estate Hub Engineering
- **Tags:** security, authentication, frontend, backend

## Context

ADR-0005 split the platform into a Django REST API and a Next.js 15 frontend. ADR-0006 chose Next.js with React Server Components, which means authenticated pages are rendered server-side after reading auth state from the request. This combination forces a specific shape on the auth token transport:

1. The token must be readable by Next.js server-rendered code (RSC + middleware) to gate routes before any HTML leaves the server.
2. The token must be invisible to JavaScript on the client to keep XSS impact bounded — this is the single highest-leverage hardening we can do for a UGC-heavy site (blog comments, forum, marketplace listings, all of which Phase 1's moderation pipeline mitigates but cannot eliminate).
3. The transport must work with Caddy's reverse proxy (ADR-0007) and `withCredentials` CORS without per-request gymnastics.
4. Refresh and rotation must be enforceable on the server so a stolen access token has a bounded blast radius.

The site has UGC at scale, prompt-injection adversaries (CLAUDE.md "critical safety contracts"), and a control surface that includes a Django admin behind 2FA + IP allowlist. Auth design has to be conservative.

## Decision

Authentication uses **SimpleJWT issued by Django**, stored in **two httpOnly + Secure + SameSite=Strict cookies**:

- `yw_access` — JWT access token, **15-minute lifetime**, sent on every request to the API.
- `yw_refresh` — JWT refresh token, **7-day lifetime**, scoped to `Path=/api/v1/auth/refresh/` so it is never sent on any other route.

CSRF protection uses the **double-submit cookie pattern**: Django sets a non-httpOnly `csrftoken` cookie that the frontend mirrors into an `X-CSRFToken` header on every unsafe (POST/PUT/PATCH/DELETE) request. With `SameSite=Strict` already eliminating cross-site cookie attachment, double-submit is defense-in-depth.

**No JWT or session token is ever exposed to JavaScript.** The frontend never reads `document.cookie` for auth. RSC reads `cookies()` server-side; client components send `credentials: 'include'` and let the browser do the rest.

This ADR is **subordinate to ADR-0005**.

## Rationale

**Alternatives evaluated.**

| Option | Verdict | Notes |
|---|---|---|
| **`Authorization: Bearer` + JWT in `localStorage`** | Rejected outright | Easiest to implement and the most common bad answer. Any XSS on any page exfiltrates the token. With UGC + comments + forum, XSS surface is large. Non-starter. |
| **`Authorization: Bearer` + JWT in JS memory only** | Rejected | Better than localStorage (no persistence), but every full page load and tab open requires re-login. Bad UX for a content site where users navigate between articles. Doesn't compose with RSC server-side auth reads. |
| **Django sessions + cookies (no JWT)** | Rejected | Excellent security but couples the frontend tightly to Django session middleware: every Next.js RSC render that needs auth has to round-trip to Django's session store. Doesn't scale for ISR'd authenticated pages. Mobile API in v2 would need a second auth path. |
| **JWT in `Authorization` header + refresh cookie** | Rejected | Some leakage protection on the refresh token but the access token still touches JS. Hybrid models tend to leak the worst of both worlds. |
| **JWT in httpOnly cookie + CSRF double-submit (chosen)** | Accepted | XSS-safe (no JS access). Works with Next.js `cookies()` for RSC auth. CSRF mitigated by SameSite=Strict and double-submit as defense-in-depth. Refresh rotation gives bounded blast radius. |

**Why two cookies instead of one.**

- **Blast radius.** If an access token leaks (e.g., via a server-side log misconfiguration), the 15-minute window bounds damage. The refresh token, with its 7-day life, is far more valuable to an attacker — keeping it scoped to a single path that only one endpoint reads makes accidental log capture nearly impossible.
- **Path scoping.** `Path=/api/v1/auth/refresh/` means the refresh cookie is *not attached* to any other request. A SSRF or proxy bug that re-routes traffic cannot accidentally hand it to another endpoint.

**Why SameSite=Strict (not Lax).**

- `Strict` prevents the cookie from being attached to top-level cross-site navigations. We don't need cross-site nav-with-cookie (no third-party embedding of authenticated pages, no OAuth callback that depends on cookie presence on first hit — allauth's OAuth flows complete server-side via state tokens).
- Trade-off: a user clicking a deep link from email to `https://yakimarealestatehub.com/account/...` will land logged-out and need to re-auth. Acceptable. The login redirect picks up the `next=...` query param and lands them where they intended.
- `Strict` essentially eliminates classic CSRF; double-submit is then defense-in-depth, not the primary control.

**Why double-submit on top of Strict.**

- Belt-and-suspenders: a future browser bug or a mis-set SameSite header on a single endpoint shouldn't open us up.
- Compatible with Django's CSRF middleware — we don't fight the framework.
- The `csrftoken` cookie *is* readable by JS by design; it's the access token that must never be.

**Token rotation.** Every successful refresh issues a new `(access, refresh)` pair and denylists the old refresh JTI in Redis. The access token has no denylist (its 15-minute lifetime is the bound). Logout denylists the active refresh JTI and clears both cookies. SimpleJWT's `BLACKLIST_AFTER_ROTATION` + `ROTATE_REFRESH_TOKENS` handle this with the `token_blacklist` app.

**Algorithm.** HS256 with a key derived from `DJANGO_SECRET_KEY` via HKDF. RS256 was considered but adds key-management overhead with no benefit when issuer == verifier (the API both signs and verifies). Rotation cadence: secret rotates per the SECURITY-PLAYBOOK.md schedule (planned: yearly + on suspected compromise).

## Consequences

### Positive
- XSS does not yield the access token. UGC moderation pipeline mitigations remain the first line, but a single missed escape doesn't hand attackers an account.
- RSC auth reads happen server-side at zero JS cost.
- Refresh-rotation + denylist gives bounded blast radius for a leaked token.
- SameSite=Strict eliminates classic CSRF; double-submit is defense-in-depth.
- Pattern is well-trodden; SimpleJWT + django-cors-headers is a proven combo.

### Negative
- Cookie-based auth requires `withCredentials` / `credentials: 'include'` everywhere on the frontend. One missed call in a fetch wrapper produces a confusing 401.
- CORS becomes stricter: `CORS_ALLOWED_ORIGINS` must list the exact frontend origin (no wildcards permitted with credentials).
- Cookie size: ~300-500 bytes per cookie; well under 4 KB limit but adds bytes to every request.
- SameSite=Strict means deep-linked email clicks land logged-out. Mitigation: `?next=` redirect after login.
- Logout requires both cookie clearing and refresh JTI denylisting; one without the other leaves either a stale cookie or a still-valid refresh token.

### Neutral
- The `csrftoken` cookie is intentionally non-httpOnly. Documented; reviewed in security audit.
- Token sizes: HS256 + standard claims ~400 bytes; modest but real.

## Implementation notes

- `pyproject.toml` adds: `djangorestframework-simplejwt[token_blacklist]`.
- `config/settings/base.py`:

  ```python
  SIMPLE_JWT = {
      "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
      "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
      "ROTATE_REFRESH_TOKENS": True,
      "BLACKLIST_AFTER_ROTATION": True,
      "ALGORITHM": "HS256",
      "SIGNING_KEY": derive_jwt_key(SECRET_KEY),
      "AUTH_COOKIE_ACCESS": "yw_access",
      "AUTH_COOKIE_REFRESH": "yw_refresh",
      "AUTH_COOKIE_SECURE": not DEBUG,
      "AUTH_COOKIE_HTTP_ONLY": True,
      "AUTH_COOKIE_SAMESITE": "Strict",
  }

  REST_FRAMEWORK = {
      "DEFAULT_AUTHENTICATION_CLASSES": (
          "apps.accounts.api.auth.JWTCookieAuthentication",
      ),
      ...
  }

  CORS_ALLOW_CREDENTIALS = True
  CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
  CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")
  ```

- `apps/accounts/api/auth.py`: `JWTCookieAuthentication(JWTAuthentication)` overrides `authenticate` to read `request.COOKIES.get("yw_access")` instead of the `Authorization` header.
- `apps/accounts/api/views.py`: `LoginView`, `RefreshView`, `LogoutView`. All set/clear cookies via `response.set_cookie(httponly=True, secure=not DEBUG, samesite="Strict", ...)`. `RefreshView` issues a new pair, denylists the old refresh.
- Frontend `lib/api/fetch.ts`:

  ```ts
  export async function api(path: string, init: RequestInit = {}) {
    const csrf = getCookie("csrftoken");
    return fetch(`${API_BASE}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init.headers ?? {}),
        ...(csrf ? { "X-CSRFToken": csrf } : {}),
        "Content-Type": "application/json",
      },
    });
  }
  ```

- Frontend `lib/auth/server.ts`:

  ```ts
  import { cookies } from "next/headers";
  export async function currentUser() {
    const access = (await cookies()).get("yw_access")?.value;
    if (!access) return null;
    return fetch(`${API_BASE}/api/v1/auth/me/`, {
      headers: { Cookie: `yw_access=${access}` },
      cache: "no-store",
    }).then(r => (r.ok ? r.json() : null));
  }
  ```

- Frontend `middleware.ts`: presence-and-shape check on `yw_access` (`req.cookies.get("yw_access")`); redirect to `/login?next=...` if missing on `(dashboard)/*` or other gated segments. Signature verification is **not** done in middleware — that's the API's job.
- Logout: frontend `POST /api/v1/auth/logout/` → API denylists refresh JTI + clears both cookies via `response.delete_cookie(...)`.

## Risks and mitigations

- **Risk:** A developer adds a write endpoint without CSRF protection. **Mitigation:** DRF default authentication class enforces CSRF for cookie-auth; PR review checklist; integration test that asserts a POST without `X-CSRFToken` returns 403.
- **Risk:** Cookie domain misconfiguration causes the cookie to leak to a sibling subdomain. **Mitigation:** explicit `Domain=yakimarealestatehub.com` (no leading dot) so cookies are bound to the exact host; staging on a separate apex.
- **Risk:** Refresh-rotation race (two parallel tabs both refresh, one wins, the other gets 401). **Mitigation:** SimpleJWT's denylist + `ROTATE_REFRESH_TOKENS=True`; frontend retries the failing request with the new access cookie that the winning tab just set.
- **Risk:** A logged-in user's refresh token is exfiltrated via a server-side log mishap. **Mitigation:** path-scoped refresh cookie, denylist on rotation, security audit covers logging surfaces.
- **Risk:** Email deep-links land users logged-out (SameSite=Strict). **Mitigation:** documented; `next=` redirect after login.

## Validation

The decision is validated when:
- A penetration test confirms `document.cookie` does not expose `yw_access` or `yw_refresh`.
- An XSS injection in a comment cannot retrieve the access token.
- A stolen access token expires in ≤15 minutes; a stolen refresh token rotates on next use and old JTI is denied.
- A POST without `X-CSRFToken` from the frontend returns 403.
- RSC pages on `(dashboard)/*` render with the authenticated user's data with no client round-trip.

We revisit if: a same-site bypass CVE in a major browser changes the threat model, or if mobile clients in v2 demand a header-based scheme (in which case we'll add a parallel scheme for those clients only — never replace this one for the web frontend).

## References

- Internal: `docs/adr/0005-split-architecture.md`, `docs/adr/0006-nextjs-app-router.md`, `docs/adr/0007-caddy-reverse-proxy.md`, `apps/accounts/api/auth.py`, `apps/accounts/api/views.py`, `frontend/middleware.ts`, `docs/SECURITY-PLAYBOOK.md`.
- External: SimpleJWT docs; OWASP "JWT for Java"/general JWT cheat sheet; OWASP "Cross-Site Request Forgery Prevention Cheat Sheet"; MDN cookie SameSite reference; PortSwigger blog on SameSite=Lax bypass research.
