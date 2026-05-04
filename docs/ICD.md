# Interface Control Document (ICD) — Yakima Real Estate Hub

## 1. Document Control

| Field | Value |
|---|---|
| Document | Interface Control Document |
| Project | Yakima Real Estate Hub |
| Version | 1.0 |
| Date | 2026-05-03 |
| Owner | Yakima Engineering |
| Status | Approved baseline |
| Related | SRS.md, SAD.md, ACCESS-MATRIX.md, MTP.md, RTM.md |

Changes to this document follow the versioning policy in section 12. Breaking-change candidates require an ADR.

---

## 2. Conventions

### 2.1 Base URLs

| Environment | URL |
|---|---|
| Local | `http://localhost/api/` (Caddy proxies to Django :8000) |
| Staging | `https://staging.yakimarealestatehub.com/api/` |
| Production | `https://yakimarealestatehub.com/api/` |

### 2.2 API Namespaces

| Namespace | Auth | Purpose |
|---|---|---|
| `/api/public/v1/` | Anonymous (read-only) | Posts, services, vendors, forum, realtor profiles, meta |
| `/api/v1/auth/` | Variable (signup anon; rest authenticated) | Login, refresh, logout, signup, 2FA, password reset |
| `/api/v1/` | JWT cookie required | Mutations, dashboards, AI tools, mod, ops, realtime |
| `/api/schema/` | Anonymous | drf-spectacular OpenAPI schema (JSON + YAML) |
| `/api/docs/` | Anonymous | Swagger UI for exploration |
| `/api/graphql/` | JWT optional | Strawberry GraphQL read-only endpoint |

### 2.3 Headers

| Header | Direction | Purpose |
|---|---|---|
| `X-Request-ID` | Both | UUIDv4 per request; echoed in response and logs. Server generates if absent. |
| `X-CSRFToken` | Client → Server | Required on every state-changing request when JWT cookie present. |
| `Cookie: yw_access` | Client → Server | 15-minute access JWT (httpOnly, SameSite=Strict, Secure) |
| `Cookie: yw_refresh` | Client → Server | 7-day refresh JWT (httpOnly, SameSite=Strict, Secure, Path=/api/v1/auth/refresh/) |
| `Cookie: yw_csrf` | Server → Client | Double-submit CSRF token (readable by JS, SameSite=Strict) |
| `Authorization: Bearer <jwt>` | Client → Server | Optional alternative to cookie auth (mobile/3rd-party clients) |
| `Idempotency-Key` | Client → Server | UUIDv4 on POST/PATCH that must be retry-safe (24h replay window) |
| `Content-Type: application/json` | Both | Default for all bodies unless multipart noted |
| `Accept-Language` | Client → Server | i18n hint (default `en-US`) |
| `X-RateLimit-Limit` | Server → Client | Total quota for window |
| `X-RateLimit-Remaining` | Server → Client | Requests remaining in window |
| `X-RateLimit-Reset` | Server → Client | Unix timestamp when window resets |
| `Retry-After` | Server → Client | Seconds to wait on 429/503 |
| `Deprecation` | Server → Client | RFC 8594 — `true` if endpoint deprecated |
| `Sunset` | Server → Client | RFC 8594 — HTTP-date when endpoint will be removed |
| `Cache-Control` | Server → Client | Per-endpoint policy (see each spec) |
| `ETag` | Server → Client | Strong validator on cacheable resources |
| `If-None-Match` | Client → Server | ETag conditional GET |

### 2.4 Versioning

URL-versioned (`/v1/`). Additive changes within v1 (new fields, new endpoints, new optional params) are non-breaking. Breaking changes get a v2 namespace; v1 enters deprecation with `Deprecation: true` and `Sunset: <HTTP-date>` headers for ≥6 months before removal.

### 2.5 Pagination

Cursor-based, opaque tokens. Query params:

| Param | Type | Default | Notes |
|---|---|---|---|
| `cursor` | string | empty | Opaque base64 token; treat as black box |
| `limit` | int | 20 | 1-100; clamped server-side |

Response envelope:

```json
{
  "results": [],
  "next": "eyJjcmVhdGVkX2F0IjogIjIwMjYtMDUtMDFUMTI6MDA6MDBaIiwgImlkIjogMTIzfQ==",
  "previous": null,
  "count_estimate": 1240
}
```

`count_estimate` is approximate (uses Postgres `pg_stat_user_tables.n_live_tup`) — never exact for large tables.

### 2.6 Filtering

Query params per endpoint. Common patterns:

| Param | Example | Applies to |
|---|---|---|
| `status` | `?status=published` | Posts, services, leads |
| `category` | `?category=photography` | Services, vendors |
| `min_price`, `max_price` | `?min_price=100&max_price=500` | Services, packages |
| `has_bundle` | `?has_bundle=true` | Services |
| `verified` | `?verified=true` | Realtor profiles |
| `q` | `?q=yakima+drone` | Full-text search (Postgres tsvector) |
| `ordering` | `?ordering=-created_at` | Whitelisted fields per endpoint |

### 2.7 Errors — RFC 7807 problem+json

Content-Type: `application/problem+json` on every error.

```json
{
  "type": "https://yakimarealestatehub.com/errors/validation",
  "title": "Validation failed",
  "status": 400,
  "detail": "One or more fields are invalid.",
  "instance": "/api/v1/posts/",
  "errors": [
    {"field": "title", "code": "max_length", "message": "Title must be 200 characters or fewer."}
  ],
  "request_id": "f3a7c2e1-9b4d-4c8a-a1e2-0d5e6f7a8b9c"
}
```

Standard error types:

| Type slug | HTTP | When |
|---|---|---|
| `validation` | 400 | Field-level validation failure |
| `authentication` | 401 | Missing/invalid/expired JWT |
| `csrf` | 403 | Missing/mismatched CSRF token |
| `permission` | 403 | Authenticated but lacks role |
| `not-found` | 404 | Resource missing or hidden by row-level perm |
| `conflict` | 409 | Optimistic lock or duplicate |
| `idempotency-mismatch` | 422 | Same key, different body |
| `rate-limited` | 429 | Throttle breached |
| `moderation-blocked` | 451 | Content failed AI moderation |
| `upstream-failure` | 502 | ARELLO/Gemini/Postmark unreachable |
| `service-unavailable` | 503 | Maintenance window or circuit breaker open |

### 2.8 Rate Limiting

DRF throttle classes + Redis backend. Per-IP for anonymous, per-user for authenticated, per-endpoint scoped.

Default tiers:

| Tier | Anon | Authenticated |
|---|---|---|
| Read | 60/min | 300/min |
| Mutate | 10/min | 60/min |
| Auth (login/signup) | 5/5min | n/a |
| AI tools | n/a | 10/hour realtor; 100/day org |
| Webhook ingress | 30/min per source | n/a |

Breach response: 429 with `Retry-After` + RFC 7807 body.

### 2.9 Idempotency

POST/PATCH operations marked idempotent in this doc accept `Idempotency-Key: <uuid>`. Server stores `(user_id, endpoint, key) → response_hash` for 24h in Redis. Replay with same key returns cached response with `X-Idempotent-Replay: true` header. Same key + different body returns 422 `idempotency-mismatch`.

Required idempotent endpoints:

- `POST /api/v1/posts/<slug>/comments/`
- `POST /api/v1/services/<slug>/inquiries/`
- `POST /api/v1/leads/<id>/messages/`
- `POST /api/v1/tools/description/`
- `POST /api/v1/tools/furniture-remover/`
- `POST /api/v1/realtor/verify/`
- `POST /api/v1/forum/items/<id>/vote/`

---

## 3. Authentication Endpoints (`/api/v1/auth/`)

### 3.1 POST `/signup/`

| Field | Value |
|---|---|
| Auth | Anonymous |
| Rate limit | 3/hour per IP |
| Idempotent | No |
| CSRF | Required (cookie pre-issued by GET `/api/v1/auth/csrf/`) |

Request:

```json
{
  "email": "user@example.com",
  "password": "correct horse battery staple",
  "password_confirm": "correct horse battery staple",
  "captcha_token": "01H..."
}
```

Response 201:

```json
{
  "id": 4128,
  "email": "user@example.com",
  "verification_email_sent": true
}
```

Sets `yw_access`, `yw_refresh`, `yw_csrf` cookies.

Errors: 400 `validation` (weak password, mismatched confirm, malformed email); 409 `conflict` (email exists); 429 `rate-limited`.

### 3.2 POST `/login/`

| Auth | Anonymous |
| Rate limit | 5/5min per IP + django-axes lock after 5 failures/15min |
| Idempotent | No |

Request:

```json
{
  "email": "user@example.com",
  "password": "correct horse battery staple",
  "remember_me": true
}
```

Response 200:

```json
{
  "id": 4128,
  "email": "user@example.com",
  "is_realtor": false,
  "is_vendor": false,
  "is_staff": false,
  "two_factor_required": false
}
```

Sets cookies; if `two_factor_required=true`, partial token issued — only `/2fa/totp/verify/` allowed until completion.

Errors: 400 `validation`; 401 `authentication`; 423 axes-locked.

### 3.3 POST `/logout/`

| Auth | Authenticated |
| Rate limit | 60/min |
| Idempotent | Yes (no key required) |

Empty body. Clears `yw_access`, `yw_refresh`, `yw_csrf` cookies; blacklists refresh JTI in Redis.

Response 204.

### 3.4 POST `/refresh/`

| Auth | `yw_refresh` cookie required |
| Rate limit | 30/min |
| Idempotent | Yes |

Empty body. Reads refresh from cookie only — body refresh tokens rejected to prevent JS theft. Rotates both tokens; old refresh JTI blacklisted.

Response 200:

```json
{
  "access_expires_at": "2026-05-03T13:15:00Z",
  "refresh_expires_at": "2026-05-10T13:00:00Z"
}
```

Errors: 401 `authentication` (expired/blacklisted/missing); 403 `csrf`.

### 3.5 POST `/verify-email/<key>/`

| Auth | Anonymous |
| Rate limit | 30/hour per IP |

Path `<key>` is the allauth confirmation key. Empty body.

Response 200: `{"verified": true}`.
Errors: 400 (key invalid/expired).

### 3.6 POST `/password-reset/`

| Auth | Anonymous |
| Rate limit | 3/hour per IP, 5/hour per email |

```json
{"email": "user@example.com"}
```

Response 202 always (avoids enumeration): `{"sent": true}`.

### 3.7 POST `/password-reset-confirm/<uid>/<token>/`

| Auth | Anonymous (token-gated) |
| Rate limit | 5/hour per IP |

```json
{"new_password": "...", "new_password_confirm": "..."}
```

Response 200 `{"reset": true}`. Errors: 400 token invalid/expired.

### 3.8 POST `/2fa/totp/setup/`

| Auth | Authenticated |
| Rate limit | 5/hour per user |

Empty body.

Response 200:

```json
{
  "provisioning_uri": "otpauth://totp/Yakima:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Yakima",
  "qr_png_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "device_id": 17
}
```

Device created in `unconfirmed=true` state. Must call `/verify/` within 10 minutes or device is purged.

### 3.9 POST `/2fa/totp/verify/`

| Auth | Authenticated (or partial post-login token) |
| Rate limit | 10/min per user |

```json
{"device_id": 17, "token": "823914"}
```

Response 200:

```json
{"verified": true, "backup_codes": ["a1b2-c3d4-e5f6", "..."]}
```

`backup_codes` only returned on first successful verify (device confirmation). Errors: 400 wrong token; 410 device expired.

---

## 4. Public Endpoints (`/api/public/v1/`)

All public endpoints support: `Cache-Control: public, max-age=300, stale-while-revalidate=86400`, ETag, conditional GET.

### 4.1 GET `/posts/`

| Auth | Anon |
| Rate limit | 60/min anon, 300/min auth |
| Filters | `category`, `author`, `tag`, `q`, `ordering=-published_at` (default), `cursor`, `limit` |

Response 200:

```json
{
  "results": [
    {
      "id": 521,
      "slug": "spring-market-yakima-2026",
      "title": "Spring market — Yakima 2026",
      "kind": "blog",
      "excerpt": "Inventory tightened in March...",
      "author": {"id": 88, "display_name": "Jane Realtor", "slug": "jane-realtor", "verified": true},
      "category": {"slug": "market-reports", "name": "Market reports"},
      "cover_image": {"url": "https://cdn.yakimarealestatehub.com/p/521/cover.webp", "width": 1600, "height": 900, "blurhash": "L6PZfSjE..."},
      "published_at": "2026-04-15T09:00:00Z",
      "reading_time_minutes": 5,
      "comment_count": 12
    }
  ],
  "next": "eyJwdWJsaXNoZWRfYXQiOiAiMjAyNi0wNC0xNVQwOTowMDowMFoifQ==",
  "previous": null,
  "count_estimate": 480
}
```

Errors: 400 `validation` (bad cursor); 503 `service-unavailable`.

### 4.2 GET `/posts/<slug>/`

| Auth | Anon | Cache | `public, max-age=300, swr=86400` |

Response 200:

```json
{
  "id": 521,
  "slug": "spring-market-yakima-2026",
  "title": "Spring market — Yakima 2026",
  "kind": "blog",
  "body_html": "<article>...</article>",
  "body_format": "html",
  "table_of_contents": [{"level": 2, "text": "Inventory", "anchor": "inventory"}],
  "author": {"id": 88, "display_name": "Jane Realtor", "slug": "jane-realtor", "verified": true, "license": {"state": "WA", "number": "12345"}},
  "category": {"slug": "market-reports", "name": "Market reports"},
  "tags": ["yakima", "market-report"],
  "cover_image": {"url": "...", "width": 1600, "height": 900, "blurhash": "..."},
  "published_at": "2026-04-15T09:00:00Z",
  "updated_at": "2026-04-16T08:00:00Z",
  "reading_time_minutes": 5,
  "comment_count": 12,
  "seo": {"meta_description": "...", "og_image": "...", "canonical": "https://yakimarealestatehub.com/blog/spring-market-yakima-2026"}
}
```

Errors: 404 `not-found` (slug missing or unpublished).

### 4.3 GET `/posts/<slug>/comments/`

| Auth | Anon | Filters | `parent` (for thread expand), `cursor`, `limit` (default 20, max 50) | Cache | `public, max-age=60, swr=300` |

Response 200:

```json
{
  "results": [
    {
      "id": 9012,
      "post_slug": "spring-market-yakima-2026",
      "parent_id": null,
      "author": {"display_name": "Anon Visitor", "slug": null, "is_realtor": false},
      "body_html": "<p>Great write-up.</p>",
      "created_at": "2026-04-15T11:30:00Z",
      "edited_at": null,
      "child_count": 2,
      "moderation_status": "approved"
    }
  ],
  "next": null,
  "previous": null,
  "count_estimate": 12
}
```

Comments with `moderation_status` other than `approved` are never returned.

### 4.4 GET `/services/`

| Auth | Anon | Filters | `category` (slug; expands subtree via treebeard), `min_price`, `max_price`, `has_bundle`, `vendor`, `q`, `ordering=-rating,price`, `cursor`, `limit` |

Response 200:

```json
{
  "results": [
    {
      "id": 312,
      "slug": "drone-aerial-photography-yakima",
      "title": "Drone aerial photography",
      "vendor": {"id": 47, "slug": "skyview-yakima", "display_name": "SkyView Yakima", "verified": true, "rating": 4.8, "reviews_count": 64},
      "category": {"slug": "photography/drone", "name": "Drone"},
      "starting_price_cents": 19900,
      "currency": "USD",
      "packages_count": 3,
      "has_bundle": true,
      "cover_image": {"url": "...", "blurhash": "..."},
      "summary": "Aerial photo + 4K video for listings."
    }
  ],
  "next": null,
  "previous": null,
  "count_estimate": 78
}
```

### 4.5 GET `/services/<slug>/`

Response 200:

```json
{
  "id": 312,
  "slug": "drone-aerial-photography-yakima",
  "title": "Drone aerial photography",
  "description_html": "<p>...</p>",
  "vendor": {"id": 47, "slug": "skyview-yakima", "display_name": "SkyView Yakima", "verified": true, "bio_html": "<p>...</p>", "service_areas": ["Yakima", "Selah"], "rating": 4.8, "reviews_count": 64},
  "category": {"slug": "photography/drone", "name": "Drone", "ancestors": [{"slug": "photography", "name": "Photography"}]},
  "packages": [
    {"id": 1100, "tier": "basic", "title": "Aerial photo basic", "price_cents": 19900, "delivery_days": 3, "revisions": 1, "features": ["10 stills", "Web-res"]},
    {"id": 1101, "tier": "standard", "title": "Aerial photo + video", "price_cents": 39900, "delivery_days": 5, "revisions": 2, "features": ["20 stills", "60-sec 4K video"]},
    {"id": 1102, "tier": "premium", "title": "Full listing media kit", "price_cents": 69900, "delivery_days": 7, "revisions": 3, "features": ["Stills", "4K video", "3D tour"]}
  ],
  "bundles": [{"id": 220, "slug": "monthly-listing-bundle", "title": "Monthly listing bundle", "price_cents": 99900, "cadence": "monthly"}],
  "gallery": [{"url": "...", "blurhash": "..."}],
  "faqs": [{"q": "Do you have FAA Part 107?", "a": "Yes."}],
  "reviews_summary": {"average": 4.8, "count": 64, "breakdown": {"5": 50, "4": 10, "3": 3, "2": 1, "1": 0}},
  "seo": {"meta_description": "...", "og_image": "..."}
}
```

### 4.6 GET `/vendors/`

| Filters | `category`, `verified`, `service_area`, `q`, `ordering=-rating`, `cursor`, `limit` |

Response 200 (truncated):

```json
{
  "results": [
    {
      "id": 47,
      "slug": "skyview-yakima",
      "display_name": "SkyView Yakima",
      "verified": true,
      "categories": ["photography/drone", "photography/twilight"],
      "service_areas": ["Yakima", "Selah", "Naches"],
      "rating": 4.8,
      "reviews_count": 64,
      "logo": {"url": "...", "blurhash": "..."},
      "starting_price_cents": 19900
    }
  ],
  "next": null,
  "previous": null,
  "count_estimate": 24
}
```

### 4.7 GET `/vendors/<slug>/`

Returns vendor profile + paginated services + reviews summary. Same shape as service detail's `vendor` block plus `services: [...]` and `reviews_recent: [...]`.

### 4.8 GET `/community/`

Lists forums (top-level boards).

```json
{
  "results": [
    {"slug": "buyers", "name": "Buyers", "description": "...", "thread_count": 412, "last_activity_at": "2026-05-02T18:14:00Z"}
  ],
  "next": null,
  "previous": null,
  "count_estimate": 8
}
```

### 4.9 GET `/community/<slug>/threads/`

| Filters | `ordering=-hot,new,top` (default `hot`), `time_range=week,month,all`, `cursor`, `limit` |

```json
{
  "results": [
    {
      "id": 7711,
      "slug": "first-time-buyer-down-payment-tips",
      "title": "First-time buyer — down payment tips",
      "author": {"display_name": "newhome2026", "slug": "newhome2026", "is_realtor": false},
      "forum_slug": "buyers",
      "score": 142,
      "vote_count": 168,
      "reply_count": 27,
      "tags": ["first-time", "financing"],
      "created_at": "2026-05-01T14:00:00Z",
      "last_activity_at": "2026-05-02T20:11:00Z",
      "is_locked": false,
      "is_pinned": false
    }
  ],
  "next": null,
  "previous": null,
  "count_estimate": 412
}
```

### 4.10 GET `/community/threads/<slug>/`

Returns thread + first-page replies. Replies further paginated via separate query.

```json
{
  "id": 7711,
  "slug": "first-time-buyer-down-payment-tips",
  "title": "First-time buyer — down payment tips",
  "body_html": "<p>...</p>",
  "author": {"display_name": "newhome2026", "slug": "newhome2026", "is_realtor": false},
  "forum_slug": "buyers",
  "score": 142,
  "vote_count": 168,
  "user_vote": null,
  "created_at": "2026-05-01T14:00:00Z",
  "is_locked": false,
  "replies": {
    "results": [
      {"id": 9001, "parent_id": null, "author": {"display_name": "jane-realtor", "is_realtor": true, "verified": true}, "body_html": "<p>...</p>", "score": 14, "user_vote": null, "created_at": "2026-05-01T15:00:00Z", "child_count": 3}
    ],
    "next": "...",
    "previous": null,
    "count_estimate": 27
  }
}
```

### 4.11 GET `/realtors/`

| Filters | `verified=true` (default), `service_area`, `specialty`, `q`, `cursor`, `limit` |

Returns paginated `RealtorProfile` summaries — only verified by default.

### 4.12 GET `/realtors/<slug>/`

Detail with bio, license info (state + number, not raw ARELLO payload), recent posts, service areas, contact form availability.

### 4.13 GET `/meta/`

| Cache | `public, max-age=600, swr=86400` |

```json
{
  "site": {"name": "Yakima Real Estate Hub", "tagline": "Central Washington real estate, in one place."},
  "navigation": [
    {"label": "Blog", "href": "/blog/", "children": []},
    {"label": "Marketplace", "href": "/marketplace/", "children": [{"label": "Photography", "href": "/marketplace/photography/"}]}
  ],
  "feature_flags": {"forum_enabled": true, "ai_tools_enabled": true, "marketplace_payments": false},
  "build": {"sha": "428248c", "deployed_at": "2026-05-03T06:00:00Z"}
}
```

Only public-safe flags — never internal toggles.

### 4.14 GET `/sitemap.xml`

Cached XML sitemap with `Content-Type: application/xml`. Indexes posts, services, vendors, forum threads. `Cache-Control: public, max-age=3600`.

### 4.15 GET `/robots.txt`

Static text. Disallows `/admin/`, `/api/v1/`, `/_next/`. Allows `/api/public/v1/sitemap.xml`.

### 4.16 GET `/healthz/`

Liveness probe. Empty body, 200 if process up. `Cache-Control: no-store`.

`GET /readyz/` — checks db, redis, celery broker; 200 healthy, 503 with body listing failed deps.

---

## 5. Authenticated Read Endpoints (`/api/v1/`)

### 5.1 GET `/me/`

| Auth | Authenticated | Cache | `private, no-store` |

```json
{
  "id": 4128,
  "email": "user@example.com",
  "display_name": "User",
  "is_staff": false,
  "is_realtor": false,
  "is_vendor": false,
  "two_factor_enabled": false,
  "email_verified": true,
  "created_at": "2026-04-10T10:00:00Z",
  "permissions": ["content.view_post", "content.add_comment"],
  "preferences": {"theme": "dark", "email_digest": "weekly"}
}
```

### 5.2 GET `/me/notifications/`

| Filters | `unread_only`, `cursor`, `limit` |

```json
{
  "results": [
    {
      "id": 33012,
      "kind": "comment_reply",
      "subject_kind": "comment",
      "subject_id": 9012,
      "title": "Jane replied to your comment",
      "url": "/blog/spring-market-yakima-2026/#comment-9012",
      "read_at": null,
      "created_at": "2026-05-03T08:00:00Z"
    }
  ],
  "next": null,
  "previous": null,
  "count_estimate": 4,
  "unread_count": 2
}
```

### 5.3 GET `/me/leads/`

Vendor sees inbound; buyer sees outbound. Filters: `status=open|in_progress|won|lost`, `cursor`, `limit`.

### 5.4 GET `/me/posts/`

Realtor's own posts (any status). Filters: `status=draft|in_review|published|removed`, `cursor`, `limit`.

### 5.5 GET `/me/tools/usage/`

Realtor's `ToolUsage` ledger.

```json
{
  "results": [{"id": 8810, "tool": "description_writer", "tokens_in": 412, "tokens_out": 280, "cost_cents": 1, "status": "succeeded", "created_at": "2026-05-02T10:00:00Z"}],
  "totals": {"month_to_date_cents": 240, "month_to_date_calls": 18, "tier_quota": 100}
}
```

---

## 6. Mutating Endpoints (`/api/v1/`)

### 6.1 POST `/posts/<slug>/comments/`

| Auth | Authenticated | Rate limit | 10/min user, 30/hour user | Idempotent | Yes (`Idempotency-Key` recommended) |

Request:

```json
{
  "body_markdown": "Useful breakdown — thanks.",
  "parent_id": null
}
```

Response 201:

```json
{
  "id": 9013,
  "post_slug": "spring-market-yakima-2026",
  "parent_id": null,
  "author": {"display_name": "User", "slug": "user-4128", "is_realtor": false},
  "body_html": "<p>Useful breakdown — thanks.</p>",
  "created_at": "2026-05-03T13:01:00Z",
  "moderation_status": "pending"
}
```

`moderation_status=pending` — comment is hidden from public list until Celery `moderate_content` task completes.

Errors: 400 `validation`; 401; 403 `csrf`; 404 post; 422 `idempotency-mismatch`; 429; 451 `moderation-blocked`.

### 6.2 POST `/community/<slug>/threads/`

| Rate limit | 5/hour user | Idempotent | Yes |

Request:

```json
{"title": "...", "body_markdown": "...", "tags": ["financing"]}
```

Response 201 `{thread object}` with `moderation_status: "pending"`.

### 6.3 POST `/community/threads/<slug>/replies/`

| Rate limit | 10/min user | Idempotent | Yes |

Request: `{"body_markdown": "...", "parent_id": 9001}`. Response 201.

### 6.4 POST `/forum/items/<id>/vote/`

| Rate limit | 60/min user | Idempotent | Yes (key required) |

Request:

```json
{"item_kind": "thread", "value": 1}
```

`item_kind` ∈ `thread|reply|comment`. `value` ∈ `-1, 0, 1` (0 clears). Same user re-voting same value is no-op. Different value updates. Always returns the new score:

```json
{"score": 143, "user_vote": 1}
```

### 6.5 POST `/services/<slug>/inquiries/`

| Auth | Authenticated | Rate limit | 5/hour user | Idempotent | Yes |

Request:

```json
{
  "package_id": 1100,
  "message": "Hi, looking for a drone shoot for a Selah listing on May 12.",
  "preferred_dates": ["2026-05-12", "2026-05-13"],
  "property_address": "1234 W Some St, Yakima, WA"
}
```

Response 201:

```json
{
  "lead_id": 56120,
  "vendor_id": 47,
  "service_slug": "drone-aerial-photography-yakima",
  "package_id": 1100,
  "status": "open",
  "created_at": "2026-05-03T13:02:00Z"
}
```

Triggers vendor notification email + SSE event.

### 6.6 POST `/vendors/onboard/<step>/`

Multi-step wizard with autosave. `<step>` ∈ `business|categories|services|gallery|publish`. Each step idempotent on `Idempotency-Key`. Final `publish` step transitions vendor profile to `pending_review` for moderation.

`PATCH /vendors/onboard/<step>/` — autosave (every 30s in UI).

### 6.7 POST `/leads/<id>/messages/`

| Auth | Lead participants only | Rate limit | 30/min user | Idempotent | Yes |

```json
{"body_markdown": "Confirmed for May 12, 9am.", "attachments": []}
```

Response 201 `{message_id, lead_id, body_html, sent_at, moderation_status}`.

### 6.8 POST `/leads/<id>/review/`

| Rate limit | 1 per lead | Idempotent | Yes |

Request:

```json
{"rating": 5, "title": "Outstanding work", "body_markdown": "...", "would_hire_again": true}
```

Response 201 — review enters `pending` moderation. 409 `conflict` if review already exists. Only allowed when lead `status=won`.

### 6.9 POST `/tools/description/`

| Auth | Realtor only | Rate limit | 10/hour user | Idempotent | Yes |

Request:

```json
{
  "property": {
    "address": "1234 W Some St, Yakima, WA",
    "beds": 3,
    "baths": 2,
    "square_feet": 1850,
    "lot_size": "0.25 acres",
    "year_built": 1998,
    "features": ["updated kitchen", "south-facing yard", "fenced"]
  },
  "tone": "professional-warm",
  "length": "standard"
}
```

Response 202:

```json
{
  "task_id": "8e1a7b2c-3d4f-5e6a-9b8c-1d2e3f4a5b6c",
  "status": "queued",
  "stream_url": "/api/v1/streams/tools/8e1a7b2c-3d4f-5e6a-9b8c-1d2e3f4a5b6c/",
  "result_url": "/api/v1/me/tools/usage/8810/"
}
```

Final result delivered via SSE or polling.

### 6.10 POST `/tools/furniture-remover/`

| Auth | Realtor only | Rate limit | 5/hour user | Idempotent | Yes |

Multipart: `image` (≤10MB, jpeg/png/webp), `mask?` (optional). Response 202 same shape as 6.9.

### 6.11 POST `/realtor/verify/`

| Auth | Authenticated, no realtor profile yet | Rate limit | 3/day user | Idempotent | Yes |

```json
{
  "license_state": "WA",
  "license_number": "12345",
  "first_name": "Jane",
  "last_name": "Doe",
  "consent": true
}
```

Response 202:

```json
{
  "license_check_id": 1411,
  "status": "queued",
  "stream_url": "/api/v1/streams/realtor/verify/1411/"
}
```

Final outcome `verified|unverified|review` writes `LicenseCheck` row with raw ARELLO JSON.

### 6.12 PATCH `/realtor/profile/`

| Auth | Verified realtor | Rate limit | 30/hour |

Partial-update fields: `bio_markdown`, `service_areas[]`, `specialties[]`, `headshot_id`, `social_links{}`. Triggers re-moderation only on `bio_markdown` change.

### 6.13 POST `/mod/items/<id>/decision/`

| Auth | Moderator | Rate limit | 200/hour user | Idempotent | Yes |

```json
{
  "action": "approve",
  "notes": "Borderline — context resolves it.",
  "template_id": null
}
```

`action` ∈ `approve|remove|escalate|require_edit`. Writes `ModerationDecision`, updates moderatable's status, signals subscribers via SSE.

Response 200 `{decision_id, action, applied_at}`.

### 6.14 POST `/ops/users/<id>/suspend/`

| Auth | Operator+ | Rate limit | 30/hour | Idempotent | Yes |

```json
{"reason": "repeated TOS violation", "duration_hours": 168}
```

Response 200 `{suspension_id, ends_at}`. Always logged via `ActionLog`.

### 6.15 POST `/ops/vendors/<id>/status/`

| Auth | Operator+ | Idempotent | Yes |

```json
{"status": "approved", "notes": "Verified business license."}
```

`status` ∈ `approved|rejected|paused`. Audit logged.

---

## 7. Realtime — Server-Sent Events

Transport: SSE. `Content-Type: text/event-stream`. Heartbeat `:keepalive` every 15s. Reconnect on `id:` checkpoint with `Last-Event-ID` header.

### 7.1 GET `/api/v1/streams/mod-queue/`

| Auth | Moderator | Backend | Redis pub/sub channel `mod_queue:new` |

Events:

```
event: item.flagged
id: 1714742460-1411
data: {"flag_id": 4101, "subject_kind": "comment", "subject_id": 9013, "reason": "spam", "score": 0.81, "received_at": "2026-05-03T13:01:00Z"}
```

### 7.2 GET `/api/v1/streams/leads/<id>/messages/`

| Auth | Lead participants only |

Events: `message.created`, `message.read`, `lead.status_changed`.

### 7.3 GET `/api/v1/streams/tools/<task_id>/`

| Auth | Task owner only |

Events: `task.queued`, `task.started`, `task.progress` (with `percent`), `task.succeeded` (with `result`), `task.failed` (with `error`).

```
event: task.succeeded
id: 8e1a7b2c-final
data: {"task_id": "8e1a7b2c-...", "result": {"description_html": "<p>Welcoming 3-bedroom...</p>", "tokens_in": 412, "tokens_out": 280, "cost_cents": 1}, "completed_at": "2026-05-03T13:03:11Z"}
```

### 7.4 GET `/api/v1/streams/realtor/verify/<license_check_id>/`

| Auth | License check owner |

Events: `verify.queued`, `verify.in_progress`, `verify.completed` (with `outcome`).

---

## 8. Webhooks (Incoming)

### 8.1 Postmark — bounces & spam complaints

Endpoint: `POST /api/v1/webhooks/postmark/`

Headers: `X-Postmark-Signature: <hex>` — HMAC-SHA256 of body with shared secret.

Verification: constant-time compare; fail closed on mismatch (returns 401 + audit log entry).

Body shape per Postmark docs (selected fields):

```json
{
  "RecordType": "Bounce",
  "MessageID": "...",
  "Email": "user@example.com",
  "Type": "HardBounce",
  "Description": "..."
}
```

Response 200 `{"received": true}` always (idempotent on `MessageID`); 401 on bad signature.

### 8.2 ARELLO — async result callback (if used)

Note: ARELLO primarily synchronous in v1. Callback-only path reserved for future async batch verification.

Endpoint: `POST /api/v1/webhooks/arello/`

Header: `X-Arello-Signature: <hex>` (HMAC-SHA256). Verification same model as Postmark.

Body: ARELLO opaque JSON; persisted verbatim into `LicenseCheck.raw_response`.

### 8.3 Cloudflare R2 — image processing notifications (internal)

Endpoint: `POST /api/v1/webhooks/img-worker/`

Auth: shared secret in header `X-Img-Worker-Token`. Used by the dedicated img-worker container to mark uploads ready/failed.

```json
{"upload_id": "abc123", "status": "ready", "variants": [{"size": "1600w", "url": "..."}]}
```

---

## 9. Schema Generation

drf-spectacular auto-publishes:

- `GET /api/schema/` — OpenAPI 3.1 JSON
- `GET /api/schema/?format=yaml` — YAML
- `GET /api/docs/` — Swagger UI
- `GET /api/redoc/` — ReDoc UI

Schema is the source of truth for codegen. Frontend uses `openapi-typescript` to generate `frontend/lib/api/types.gen.ts`. Mobile clients can generate Swift/Kotlin via `openapi-generator-cli`.

CI gate: `python manage.py spectacular --validate --fail-on-warn`.

---

## 10. Caching & ETag

| Resource | Cache-Control | ETag basis |
|---|---|---|
| Public post list | `public, max-age=300, swr=86400` | `max(updated_at)` of page |
| Public post detail | `public, max-age=300, swr=86400` | `updated_at` |
| Comments list | `public, max-age=60, swr=300` | `max(updated_at)` |
| Service list / detail | `public, max-age=300, swr=86400` | `updated_at` of service+packages |
| `/meta/` | `public, max-age=600, swr=86400` | build sha |
| `/me/` and `/api/v1/*` private | `private, no-store` | n/a |
| Sitemap | `public, max-age=3600` | digest of latest entry |

Conditional GET: clients send `If-None-Match`; server returns 304 with no body if unchanged.

---

## 11. Idempotency Implementation Notes

Server-side store: Redis key `idem:{user_or_ip}:{endpoint}:{key}` → `{body_hash, response_status, response_body, created_at}`. TTL 24h.

Algorithm:

1. Lookup key. If missing → execute, persist response, return.
2. If present and `body_hash` matches → return cached response with `X-Idempotent-Replay: true`.
3. If present and `body_hash` differs → 422 `idempotency-mismatch`.

Anonymous requests: keyed by IP + key. Authenticated: keyed by user id.

---

## 12. Versioning Policy

- Within `v1`: additive only (new endpoints, new optional fields, new optional query params, new response fields).
- Removing a field, narrowing a type, or changing semantics requires `v2`.
- `v1` deprecation path: announce via `Deprecation: true` and `Sunset: <HTTP-date>` headers and CHANGELOG; minimum 6-month grace period; banner in `/api/docs/`.
- Frontend pins to a major version in `NEXT_PUBLIC_API_VERSION`.

---

## 13. OpenAPI Excerpt Example

Auto-generated YAML for `GET /api/public/v1/posts/{slug}/`:

```yaml
openapi: 3.1.0
info:
  title: Yakima Real Estate Hub API
  version: 1.0.0
paths:
  /api/public/v1/posts/{slug}/:
    get:
      operationId: public_posts_retrieve
      summary: Retrieve a published post by slug
      tags: [Public Posts]
      parameters:
        - in: path
          name: slug
          required: true
          schema: { type: string, pattern: "^[-a-z0-9]+$", maxLength: 200 }
        - in: header
          name: If-None-Match
          required: false
          schema: { type: string }
      responses:
        "200":
          description: Post detail
          headers:
            ETag: { schema: { type: string } }
            Cache-Control: { schema: { type: string }, example: "public, max-age=300, stale-while-revalidate=86400" }
          content:
            application/json:
              schema: { $ref: "#/components/schemas/PostDetail" }
        "304":
          description: Not modified
        "404":
          description: Not found
          content:
            application/problem+json:
              schema: { $ref: "#/components/schemas/Problem" }
components:
  schemas:
    PostDetail:
      type: object
      required: [id, slug, title, body_html, kind, author, published_at]
      properties:
        id: { type: integer, format: int64 }
        slug: { type: string }
        title: { type: string, maxLength: 200 }
        kind: { type: string, enum: [yakimaweb, blog, landing] }
        body_html: { type: string }
        body_format: { type: string, enum: [html, markdown] }
        author: { $ref: "#/components/schemas/AuthorSummary" }
        category: { $ref: "#/components/schemas/CategorySummary" }
        published_at: { type: string, format: date-time }
        updated_at: { type: string, format: date-time }
        reading_time_minutes: { type: integer, minimum: 0 }
        comment_count: { type: integer, minimum: 0 }
        seo:
          type: object
          properties:
            meta_description: { type: string }
            og_image: { type: string, format: uri }
            canonical: { type: string, format: uri }
    Problem:
      type: object
      required: [type, title, status]
      properties:
        type: { type: string, format: uri }
        title: { type: string }
        status: { type: integer }
        detail: { type: string }
        instance: { type: string }
        errors:
          type: array
          items:
            type: object
            properties:
              field: { type: string }
              code: { type: string }
              message: { type: string }
        request_id: { type: string, format: uuid }
```

---

## 14. Cross-References

- SRS.md — functional & non-functional requirements (FR-1xx … NFR-8xx).
- SAD.md — system architecture, deployment topology.
- ACCESS-MATRIX.md — role × resource permission grid.
- MTP.md — verification of every endpoint against test cases.
- RTM.md — requirement → endpoint → test traceability.
