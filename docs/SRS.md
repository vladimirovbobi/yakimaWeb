# Software Requirements Specification — Yakima Real Estate Hub

| Field | Value |
|---|---|
| Document | SRS (IEEE 830-style) |
| Version | 1.0 |
| Date | 2026-05-03 |
| Owner | Yakima Real Estate Hub Engineering |
| Status | Baseline for Phases 2–8 |

## Document Control

### Change Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-05-03 | Engineering | Initial baseline; supersedes ad-hoc requirements scattered across phase plans |

### References

- `docs/VISION-AND-SCOPE.md` — product scope and success criteria
- `docs/SAD.md` — architecture realizing this SRS
- `docs/ICD.md` — external interface details (referenced)
- `docs/adr/0001-django-monolith.md` — original framework decision
- `docs/adr/0002-arello-for-license-verification.md` — license verify integration
- `docs/adr/0003-gemini-as-ai-provider.md` — AI provider lock
- `docs/adr/0004-lead-gen-only-marketplace-v1.md` — marketplace payment exclusion
- `docs/adr/0005-split-monolith-django-api-nextjs-frontend.md` — transport split (assumed)
- `docs/adr/0006-jwt-cookie-auth.md` — auth model (assumed)
- `docs/adr/0007-graphql-readonly-discovery.md` — Strawberry GraphQL read-only layer (assumed)
- `docs/adr/0008-cloudflare-r2-media.md` — media storage (assumed)
- `docs/adr/0009-postmark-transactional-email.md` — email provider (assumed)
- `docs/research/ai-moderation-prompt-injection.md` — moderation pipeline reference
- `docs/research/arello-api-notes.md` — ARELLO REST contract
- `docs/research/design-system-reference.md` — design tokens
- `docs/research/platform-guidelines-v1.md` — community standards driving FR-6xx
- `docs/research/marketplace-patterns/{ebay,fiverr}-ux-teardown.md` — marketplace UX precedents
- IEEE Std 830-1998 Recommended Practice for Software Requirements Specifications
- ISO/IEC 25010:2011 Systems and software Quality Requirements and Evaluation

---

## 1. Introduction

### 1.1 Purpose

Specify the functional and non-functional requirements for Yakima Real Estate Hub v1 (public launch). Every requirement is testable, traceable to a user need (see `VISION-AND-SCOPE.md` §3), and bounded by the constraints in §1.3. This document is the contract between product (Operator), engineering, and downstream reviewers (security, accessibility, legal).

### 1.2 Scope

In-scope surfaces are enumerated in `VISION-AND-SCOPE.md` §4. Excluded surfaces (MLS, payments, multi-region, native mobile, multi-currency, DM) are listed in §5 of that document and are explicitly out of scope here.

### 1.3 Definitions, Acronyms, Abbreviations

| Term | Meaning |
|---|---|
| ARELLO | Association of Real Estate License Law Officials; license verification API |
| CSP | Content Security Policy |
| DRF | Django REST Framework |
| FCP | First Contentful Paint |
| FR | Functional Requirement |
| FTS | Full-Text Search |
| JWT | JSON Web Token |
| LCP | Largest Contentful Paint |
| ModeratableMixin | Abstract Django model mixin attaching the moderation pipeline to UGC |
| NFR | Non-Functional Requirement |
| RESPA | Real Estate Settlement Procedures Act |
| RSC | React Server Component |
| RTM | Requirements Traceability Matrix |
| TTFB | Time to First Byte |
| UGC | User-Generated Content |

### 1.4 Overview

§2 gives product perspective and high-level functions. §3 specifies functional requirements grouped by surface (FR-1xx … FR-8xx). §4 specifies non-functional requirements organized by ISO 25010 quality attributes (NFR-1xx … NFR-8xx). §5 references external interfaces. §6 contains the glossary and traceability summary.

---

## 2. Overall Description

### 2.1 Product Perspective

Yakima Real Estate Hub is a greenfield product. It is not a replacement for an existing system. It coexists with, but does not integrate with, public listing portals (Zillow, Redfin) and the local MLS. External dependencies — ARELLO, Gemini, Cloudflare R2, Postmark, Sentry, Better Stack — are documented in `SAD.md` §3 and `ICD.md`.

### 2.2 Product Functions (high-level)

1. Authenticate users (email + password, OAuth deferred), verify email, enforce 2FA for staff.
2. Verify WA real-estate licenses via ARELLO and gate authoring on verification.
3. Publish, list, search, and read editorial posts and realtor blogs.
4. Host comments, forum threads/replies/votes, and lead inquiries — all moderated.
5. Run AI lead-magnet tools (description writer, furniture remover) under rate and spend caps.
6. Surface a vendor marketplace with profiles, services, packages, bundles, leads, reviews.
7. Operate the platform via three control surfaces (Django admin / mod console / operator dashboard).
8. Surface SEO/social signals (sitemap, robots, JSON-LD, OG, RSS).

### 2.3 User Characteristics

Five role classes; see `VISION-AND-SCOPE.md` §3 for personas.

| Role | Auth required | Capabilities (summary) |
|---|---|---|
| Anonymous | no | Read public posts, forum threads, vendor profiles, AI tool landing pages |
| Authenticated user | yes | All of above + comment, forum post/vote, lead inquiry, run AI tool, profile edit |
| Verified realtor | yes + ARELLO check | All of above + publish blog post |
| Vendor | yes + identity check | All of above + create/edit services, packages, bundles, respond to leads |
| Moderator | yes + 2FA | Mod console: review queue, approve/reject, audit-trail visible |
| Operator | yes + 2FA | Operator dashboard + all moderator capabilities |
| Admin | yes + 2FA + IP allowlist | Django admin: break-glass schema-level access |

### 2.4 Constraints

See `VISION-AND-SCOPE.md` §7 (regulatory, technical, team, timeline, budget). Notable inheritances:

- 10K MAU baseline; 100K MAU schema-headroom
- Railway hosting; 12-factor portability required
- Single Postgres, single Redis (no clustering in v1)
- America/Los_Angeles time zone, USD, en-us locale only
- WCAG 2.1 AA accessibility floor

### 2.5 Assumptions and Dependencies

- ARELLO API contract remains stable through 2026 (per `docs/research/arello-api-notes.md`).
- Gemini 2.5 Flash and 2.5 Pro remain available; pricing within the $80/mo cap at projected volume.
- Postmark deliverability for transactional email remains ≥99%.
- Railway infrastructure remains within budget and SLA.
- Solo developer is the execution model through public launch.

---

## 3. Functional Requirements

Each FR carries: ID, title, description, priority (M = Must, S = Should, C = Could), source (persona served — A=Realtor, B=Vendor, C=Buyer/Seller, D=Operator; "All" if cross-cutting), acceptance criteria (testable), dependencies.

### FR-1xx — Authentication & Account Management

#### FR-101 — Email signup
- **Description.** Anonymous user can register with email + password. System sends verification email via Postmark with single-use, 24h-expiring token.
- **Priority.** M
- **Source.** All
- **Acceptance.** (a) `POST /api/auth/signup/` with valid email + password ≥12 chars returns 201 + cookies. (b) Verification email arrives <60s. (c) Token consumed once; reuse returns 410 Gone. (d) Unverified user cannot publish content (UGC create returns 403).
- **Depends on.** —

#### FR-102 — Email verification
- **Description.** User clicks the link in the verification email; account marked verified.
- **Priority.** M
- **Source.** All
- **Acceptance.** Link `GET /verify-email/<token>/` flips `User.email_verified=True`, redirects to `/account`. Expired token shows resend page.
- **Depends on.** FR-101

#### FR-103 — Login
- **Description.** Email + password login; issues SimpleJWT access (15min) + refresh (7d) in httpOnly+SameSite=Strict cookies (`yw_access`, `yw_refresh`).
- **Priority.** M
- **Source.** All
- **Acceptance.** Correct credentials → 200 + cookies; bad credentials → 401 with generic message; 6+ failed attempts in 10min → django-axes lockout.
- **Depends on.** FR-101

#### FR-104 — Logout
- **Description.** Clears access + refresh cookies; refresh token added to denylist.
- **Priority.** M
- **Source.** All
- **Acceptance.** `POST /api/auth/logout/` returns 204 with cookie-clearing headers; subsequent refresh attempts return 401.
- **Depends on.** FR-103

#### FR-105 — Token refresh
- **Description.** Silent refresh of access token via refresh cookie.
- **Priority.** M
- **Source.** All
- **Acceptance.** `POST /api/auth/refresh/` with valid refresh cookie returns new access cookie; rotated refresh; old refresh denylisted.
- **Depends on.** FR-103

#### FR-106 — Password reset
- **Description.** Request reset email; click link to set new password.
- **Priority.** M
- **Source.** All
- **Acceptance.** Reset email <60s; token single-use 1h; new password ≥12 chars; existing sessions invalidated.
- **Depends on.** FR-101

#### FR-107 — 2FA enrolment (staff required)
- **Description.** Staff users (mod, operator, admin) must enroll a TOTP device via django-otp before staff actions are accessible.
- **Priority.** M
- **Source.** D
- **Acceptance.** Login as staff without active TOTP device → forced enroll page; cannot reach `/admin/`, `/mod/`, `/ops/` until enrolled and verified.
- **Depends on.** FR-103

#### FR-108 — License verification (realtor onboarding)
- **Description.** User submits WA real-estate license number; system calls ARELLO; result persisted in `LicenseCheck` row with raw JSON; on success, user gains "verified realtor" capability.
- **Priority.** M
- **Source.** A
- **Acceptance.** Valid active license → `RealtorProfile.verified_at` set, `LicenseCheck.status="active"`, raw JSON stored. Invalid/expired license → user sees explicit reason (suspended/expired/not-found). Admin cannot delete `LicenseCheck` rows (audit immutability).
- **Depends on.** FR-101, ARELLO API
- **Reference.** `docs/research/arello-api-notes.md`, `docs/adr/0002`

#### FR-109 — Profile edit
- **Description.** Authenticated user can edit display name, bio, avatar, public contact preferences. Realtor profiles add license number (read-only post-verify), brokerage, service area.
- **Priority.** M
- **Source.** A, B, C
- **Acceptance.** `PATCH /api/me/` updates allowed fields; bio sanitized through bleach; avatar uploaded to R2 via signed URL; changes audit-logged when actor is staff.
- **Depends on.** FR-103

#### FR-110 — Vendor onboarding
- **Description.** Authenticated user requests vendor status; submits business name, category, service area, identity attestation; pending operator approval.
- **Priority.** M
- **Source.** B
- **Acceptance.** Application creates `VendorProfile(status='pending')`; operator approves in mod console → status becomes 'active', email notification sent.
- **Depends on.** FR-101, FR-505 (operator approval flow)

#### FR-111 — Role transitions
- **Description.** Granting moderator/operator/admin role is a staff-only action, audit-logged. Demotion clears related capabilities and any active sessions.
- **Priority.** M
- **Source.** D
- **Acceptance.** `User.is_moderator/is_operator/is_staff/is_superuser` flags writable only via Django admin or operator dashboard; every change writes `ActionLog` row; demoted user's TOTP device retained but role-gated views return 403.
- **Depends on.** FR-107, FR-7xx

#### FR-112 — Account deletion (data rights)
- **Description.** User can request account deletion. System soft-deletes user, hard-deletes UGC (or anonymizes per policy), ships deletion confirmation email.
- **Priority.** S
- **Source.** All
- **Acceptance.** `DELETE /api/me/` returns 202; within 24h, user record `is_active=False`, posts/comments anonymized to "[deleted user]", email sent. Audit row written.
- **Depends on.** FR-103

#### FR-113 — Data export (data rights)
- **Description.** User can request a JSON export of their data (profile, posts, comments, lead inquiries).
- **Priority.** S
- **Source.** All
- **Acceptance.** `GET /api/me/export/` returns JSON file streamed within 30s; signed download URL emailed if exceeds 5 MB.
- **Depends on.** FR-103

#### FR-114 — Rate-limited login
- **Description.** django-axes throttles to 6 failed attempts per 10 minutes per `(ip, email)` pair; lockout 1h.
- **Priority.** M
- **Source.** D (security)
- **Acceptance.** 7th failed attempt within 10min returns 423 Locked; lockout cleared at 1h.
- **Depends on.** FR-103

### FR-2xx — Content Authoring & Display

#### FR-201 — Create post (org author)
- **Description.** Org/admin user creates a post with title, slug, body (sanitized HTML), hero image, tags, scheduled publish time.
- **Priority.** M
- **Source.** D
- **Acceptance.** `POST /api/posts/` requires `is_staff`; body sanitized via bleach allowlist; hero image stored in R2; `Post.published_at` honored; post enters mod queue if `is_staff=False` (paranoid mode for delegated authors).
- **Depends on.** FR-103, FR-6xx

#### FR-202 — Create post (verified realtor blog)
- **Description.** Verified realtor authors a blog post; same model as FR-201 with `author_role='realtor'` and visible byline + license badge.
- **Priority.** M
- **Source.** A
- **Acceptance.** `POST /api/posts/` allowed iff `request.user.realtorprofile.verified_at is not None`; post enters mod queue (Layer 1 deterministic + Layer 2 Gemini); on approval, public.
- **Depends on.** FR-108, FR-6xx

#### FR-203 — List posts
- **Description.** Public list endpoint with pagination, tag filter, author filter, sort (newest, most-read).
- **Priority.** M
- **Source.** C
- **Acceptance.** `GET /api/posts/?page=1&tag=neighborhoods` returns 20/page; `Cache-Control: public, s-maxage=60` on anonymous responses; SSR-rendered as `/posts` in Next.js.
- **Depends on.** FR-201

#### FR-204 — Post detail
- **Description.** Public detail endpoint and SSR page; serves post, related posts, comments thread.
- **Priority.** M
- **Source.** C
- **Acceptance.** `GET /api/posts/<slug>/` returns 200 with body, OG image URL, JSON-LD blob; 404 if unpublished or moderation-rejected.
- **Depends on.** FR-201

#### FR-205 — Search posts (Postgres FTS)
- **Description.** Full-text search across post title + body using `tsvector` GIN index; weighted (title > body).
- **Priority.** M
- **Source.** C
- **Acceptance.** `GET /api/search/?q=irrigation` returns ranked matches in <250ms p95 at 10K-post corpus; supports phrase queries (`"hop yard"`); pagination.
- **Depends on.** FR-201

#### FR-206 — Comment under post
- **Description.** Authenticated user can comment under any published post. Comment passes through ModeratableMixin pipeline before display.
- **Priority.** M
- **Source.** C
- **Acceptance.** `POST /api/posts/<slug>/comments/` creates `Comment(status='pending')`; Layer 1 + Layer 2 run async; on approval, comment becomes visible; rejected comments hidden with reason visible to author only.
- **Depends on.** FR-103, FR-6xx

#### FR-207 — Edit own comment / post
- **Description.** Author can edit their own comment within 15min of posting; post-15min edits flagged in audit.
- **Priority.** S
- **Source.** All
- **Acceptance.** `PATCH /api/comments/<id>/` allowed for owner; edit re-enters mod queue if any flagged term changed; edit history retained.
- **Depends on.** FR-206

#### FR-208 — Delete own comment / post
- **Description.** Author can delete their own content; deletion is soft (status flag) for audit.
- **Priority.** M
- **Source.** All
- **Acceptance.** `DELETE /api/comments/<id>/` sets `Comment.status='deleted_by_author'`; row preserved 90 days then hard-deleted via Celery beat.
- **Depends on.** FR-206

#### FR-209 — Sanitize HTML body
- **Description.** All user-submitted HTML passes through bleach with allowlist (p, br, strong, em, ul, ol, li, a, blockquote, code, h2, h3, img with `src` to R2 only).
- **Priority.** M
- **Source.** D (security)
- **Acceptance.** `<script>`, `<iframe>` (except whitelisted YouTube/Instagram embeds via shortcode), `on*` attributes, `javascript:` URLs all stripped. Adversarial test fixtures verified.
- **Depends on.** FR-201, FR-206

#### FR-210 — Embed shortcodes
- **Description.** YouTube and Instagram embeds via shortcodes `[youtube ID]`, `[instagram URL]`. Renders sandboxed iframe with restricted sandbox flags.
- **Priority.** S
- **Source.** A, D
- **Acceptance.** Shortcode resolves only allowlisted hosts (`youtube.com`, `youtu.be`, `instagram.com`); iframe has `sandbox="allow-scripts allow-same-origin allow-presentation"`; CSP `frame-src` configured.
- **Depends on.** FR-209

#### FR-211 — Lead-magnet landing pages
- **Description.** Static-feel landing pages for AI tools (description writer, furniture remover) — public, SEO-optimized.
- **Priority.** M
- **Source.** All
- **Acceptance.** `/tools/description-writer` and `/tools/furniture-remover` SSR-rendered, JSON-LD `SoftwareApplication`, OG images, ≥95 Lighthouse mobile.
- **Depends on.** FR-5xx

#### FR-212 — Tag taxonomy
- **Description.** Curated tag list (neighborhoods, market analysis, buying tips, selling tips, vendor spotlight, etc.). Authors choose from existing tags; only Operator can create new tags.
- **Priority.** S
- **Source.** D
- **Acceptance.** `Tag.create` restricted to operator role; authors get autocomplete via `GET /api/tags/`.
- **Depends on.** FR-201

### FR-3xx — Forum (Reddit-style)

#### FR-301 — Create forum thread
- **Description.** Authenticated user creates thread with title, flair (selected from a controlled list), body (sanitized markdown).
- **Priority.** M
- **Source.** A, C
- **Acceptance.** `POST /api/forum/threads/` enters mod queue; flair limited to `MarketAnalysis | NeighborhoodGuide | TacticalQ | VendorRec | News | Casual`; markdown rendered server-side via markdown-it with allowlist.
- **Depends on.** FR-103, FR-6xx

#### FR-302 — Reply to thread
- **Description.** Authenticated user replies to thread; reply may itself have replies (nested ≤3 levels).
- **Priority.** M
- **Source.** All
- **Acceptance.** `POST /api/forum/threads/<id>/replies/`; nested via `parent_reply_id`; depth >3 rejected; mod pipeline applies.
- **Depends on.** FR-301

#### FR-303 — Vote on thread/reply
- **Description.** Authenticated user can upvote/downvote a thread or reply. One vote per (user, target). Switching changes score by ±2.
- **Priority.** M
- **Source.** All
- **Acceptance.** `POST /api/forum/vote/` with `{target_type, target_id, value: 1|-1|0}` updates `Vote` row; `score_cache` denormalized via Postgres trigger or Celery debounce; rate-limited to 60 votes/minute/user.
- **Depends on.** FR-103

#### FR-304 — Sort modes
- **Description.** Forum index supports sort modes: Hot (Reddit-style time-decayed score), New (created_at desc), Top (window: 24h, 7d, 30d, all-time).
- **Priority.** M
- **Source.** All
- **Acceptance.** `GET /api/forum/threads/?sort=hot` returns scores using `log10(max(|score|,1)) + (created_ts - epoch) / 45000`; `?sort=top&window=7d` filters and orders by score; cached 60s.
- **Depends on.** FR-303

#### FR-305 — Flair filter
- **Description.** Forum index can be filtered by flair.
- **Priority.** S
- **Source.** All
- **Acceptance.** `GET /api/forum/threads/?flair=NeighborhoodGuide`; multi-select via repeated query params.
- **Depends on.** FR-301

#### FR-306 — Score sync (denormalize)
- **Description.** Thread/reply score recomputed periodically to correct drift; debounced Celery task runs every 5 minutes.
- **Priority.** S
- **Source.** D
- **Acceptance.** Beat task `forum.recompute_scores` reconciles `score_cache` with `Vote` aggregates; logs drift > 5 votes.
- **Depends on.** FR-303

#### FR-307 — Public forum read
- **Description.** Anonymous users can read forum threads/replies; cannot post or vote.
- **Priority.** M
- **Source.** C
- **Acceptance.** `GET /forum`, `/forum/<slug>` SSR for anonymous; vote/reply UI shown but routes to login.
- **Depends on.** FR-301, FR-302

#### FR-308 — Thread search
- **Description.** Same Postgres FTS as posts, scoped to forum threads.
- **Priority.** S
- **Source.** All
- **Acceptance.** `GET /api/forum/search/?q=...`; <300ms p95 at 10K-thread corpus.
- **Depends on.** FR-205

### FR-4xx — Marketplace (lead-gen, no payments)

#### FR-401 — Vendor profile
- **Description.** Approved vendor has a public profile: business name, logo, hero image, description (sanitized), service area (zip codes / radius), category, social links.
- **Priority.** M
- **Source.** B
- **Acceptance.** `GET /api/vendors/<slug>/` returns profile + active services; SSR page at `/marketplace/<slug>`.
- **Depends on.** FR-110

#### FR-402 — Service create/edit
- **Description.** Vendor creates services under their profile. Service has title, description, base price (display only), turnaround time, gallery (≤8 images via R2), category.
- **Priority.** M
- **Source.** B
- **Acceptance.** `POST /api/services/` requires `vendor.status='active'`; gallery images uploaded via signed URL flow; service enters mod queue.
- **Depends on.** FR-110, FR-6xx

#### FR-403 — Package tiers
- **Description.** Each service may define up to 3 tiered packages (Starter / Pro / Premium) with deliverables and price.
- **Priority.** S
- **Source.** B
- **Acceptance.** `Package` rows tied to service; UI surfaces them as Fiverr-style three-column table.
- **Depends on.** FR-402

#### FR-404 — Bundle (cross-service)
- **Description.** Vendor can group services or packages from their own profile into a Bundle (e.g., Photo + Drone + 3D for $895). Bundle has its own slug and lead inquiry endpoint.
- **Priority.** S
- **Source.** B
- **Acceptance.** `Bundle` references `BundleItem` rows linking services/packages from the same vendor; cross-vendor bundles disallowed in v1.
- **Depends on.** FR-403

#### FR-405 — Lead inquiry
- **Description.** Authenticated user submits a lead inquiry for a service, package, or bundle. Includes message (sanitized), contact preferences, optional listing-address context. Vendor receives notification email + in-app inbox entry.
- **Priority.** M
- **Source.** A, C
- **Acceptance.** `POST /api/leads/` creates `Lead(status='new')`; mod pipeline scans message; vendor email via Postmark <60s; vendor sees lead in `/marketplace/inbox`.
- **Depends on.** FR-103, FR-6xx

#### FR-406 — Lead messages (threaded)
- **Description.** After lead created, vendor and user can exchange messages on the lead thread (still moderated).
- **Priority.** M
- **Source.** A, B, C
- **Acceptance.** `POST /api/leads/<id>/messages/` creates `LeadMessage(status='pending')`; visible only to lead participants + mods; pipeline runs; rate-limited (10 messages/lead/hour/user).
- **Depends on.** FR-405

#### FR-407 — Review
- **Description.** After a lead reaches `status='completed'` (vendor marks complete; user confirms), user can write a review (1–5 stars + text).
- **Priority.** M
- **Source.** A, B, C
- **Acceptance.** `POST /api/reviews/` allowed only for lead participants; one review per (user, vendor) per lead; mod pipeline scans text; published reviews aggregate into `Vendor.rating_avg` and `rating_count`.
- **Depends on.** FR-405, FR-6xx

#### FR-408 — Category tree
- **Description.** Marketplace categories (Photography, 3D Tours, Staging, Junk Removal, Lenders, Web/Marketing, AI Agents, Automation). Up to 2 levels deep. Operator-managed.
- **Priority.** M
- **Source.** D
- **Acceptance.** `Category` model with `parent_id`; admin-only create/update; vendor profiles and services pick from leaf categories.
- **Depends on.** FR-401, FR-402

#### FR-409 — Marketplace search/discover
- **Description.** Faceted search over services: text query (FTS), category, service-area proximity (zip code), price range, rating.
- **Priority.** M
- **Source.** A, C
- **Acceptance.** `GET /api/marketplace/search/?q=photo&zip=98901&max_price=500`; <400ms p95 at 1K-service corpus; React island for facets, SSR for first page.
- **Depends on.** FR-402, FR-205

#### FR-410 — Vendor inbox
- **Description.** Authenticated vendor sees a list of leads, sortable by status (new/active/closed) and recency.
- **Priority.** M
- **Source.** B
- **Acceptance.** `/marketplace/inbox` SSR + TanStack Query refresh; unread leads counter in header.
- **Depends on.** FR-405

#### FR-411 — Vendor profile moderation
- **Description.** Vendor profile and service edits enter mod queue when content fields change.
- **Priority.** M
- **Source.** D
- **Acceptance.** Edits to `Vendor.description`, `Service.description`, `Service.gallery` trigger pipeline; profile remains visible during review (last-approved version cached).
- **Depends on.** FR-401, FR-402, FR-6xx

#### FR-412 — Lead-only marketplace constraint
- **Description.** No payment flow shipped in v1. Lead transitions are status-only (`new → active → completed | abandoned`).
- **Priority.** M
- **Source.** D, ADR-0004
- **Acceptance.** No Stripe/PayPal/escrow code in v1 codebase. No `Payment` table. Reviewer confirms via grep on `apps/marketplace/`.
- **Depends on.** ADR-0004

### FR-5xx — AI Tools (Lead Magnets)

#### FR-501 — Description Writer landing
- **Description.** Public page describes the tool, shows examples, has CTA to run.
- **Priority.** M
- **Source.** All
- **Acceptance.** `/tools/description-writer` SSR; ≥95 Lighthouse mobile; OG/JSON-LD complete.
- **Depends on.** —

#### FR-502 — Description Writer run
- **Description.** Authenticated user submits structured property fields (beds, baths, sqft, neighborhood, features, listing-side: buy/sell). System submits to Gemini 2.5 Pro via Celery, returns 3 description variants.
- **Priority.** M
- **Source.** A, C
- **Acceptance.** `POST /api/tools/description-writer/` with valid fields → 202 + job ID; Celery task runs Gemini call with prompt-injection-aware system prompt; result polled via `GET /api/tools/jobs/<id>/`; 3 variants returned within 20s p95; result stored in `ToolUsage` ledger row with input hash.
- **Depends on.** FR-103, FR-6xx (system prompts hardened)

#### FR-503 — Furniture Remover landing
- **Description.** Public page describes the tool with before/after gallery.
- **Priority.** M
- **Source.** All
- **Acceptance.** `/tools/furniture-remover` SSR; gallery uses R2-hosted images; ≥95 Lighthouse mobile.
- **Depends on.** —

#### FR-504 — Furniture Remover run
- **Description.** Authenticated user uploads a room photo; system runs Gemini multimodal pipeline (port from `virtual-staging-app`); returns "empty room" image.
- **Priority.** M
- **Source.** A, C
- **Acceptance.** `POST /api/tools/furniture-remover/` with image (≤10 MB, jpeg/png/webp) → 202; img-worker queue handles Pillow + Gemini multimodal call; result stored in R2; signed URL returned to user; latency <90s p95; failures retried 2× with exponential backoff.
- **Depends on.** FR-103, R2 signed-URL flow, img-worker queue

#### FR-505 — Per-user rate limit (AI tools)
- **Description.** Free tier: 5 description-writer runs/day, 2 furniture-remover runs/day. Verified-realtor tier: 25/day, 10/day. Enforced server-side via Redis token bucket.
- **Priority.** M
- **Source.** D (cost control)
- **Acceptance.** 6th description-writer run by free user → 429 Too Many Requests with `Retry-After`; counters reset at America/Los_Angeles midnight.
- **Depends on.** FR-502, FR-504

#### FR-506 — Tool usage ledger
- **Description.** Every AI tool run writes a `ToolUsage` row: user, tool, input hash, model, prompt token count, completion token count, cost (cents), status, error (if any).
- **Priority.** M
- **Source.** D
- **Acceptance.** `ToolUsage` table append-only; operator dashboard surfaces cost/day; admin cannot delete rows.
- **Depends on.** FR-502, FR-504

#### FR-507 — Global AI spend cap
- **Description.** Daily aggregate Gemini cost across all users hard-capped (default $5/day, configurable). On cap reach, tools return 503 with friendly message until next-day reset.
- **Priority.** M
- **Source.** D
- **Acceptance.** Celery beat task aggregates `ToolUsage.cost` daily; if `current_day_total >= cap`, tool endpoints return 503; ops sees alert in Sentry.
- **Depends on.** FR-506

#### FR-508 — Prompt-injection hardening (tools)
- **Description.** All AI-tool prompts pass through `injection_guard` to detect attempted system-prompt overrides in user input; flagged inputs rejected before Gemini call.
- **Priority.** M
- **Source.** D
- **Acceptance.** Adversarial fixture suite (`apps/moderation/tests/fixtures/prompt_injection_attacks.json`) — every fixture rejected; 0 false negatives.
- **Depends on.** FR-6xx

#### FR-509 — Anonymous demo (preview only)
- **Description.** Anonymous users can run description writer once per session (cookie-bound), receive 1 truncated variant, prompted to sign up for full output.
- **Priority.** S
- **Source.** All (acquisition)
- **Acceptance.** Anonymous run gates after 1; cookie-bound counter; full 3 variants gated to authenticated.
- **Depends on.** FR-502

### FR-6xx — Moderation Pipeline

#### FR-601 — ModeratableMixin
- **Description.** Abstract Django model mixin providing `status`, `moderated_at`, `moderation_decision_id`, `flag_count` fields and post-save signal that enqueues moderation Celery task. Every UGC model inherits.
- **Priority.** M
- **Source.** D, safety contract #5
- **Acceptance.** Models: `Post`, `Comment`, `ForumThread`, `ForumReply`, `Service`, `Bundle`, `Lead`, `LeadMessage`, `Review`, `VendorProfile`, `RealtorProfile.bio`. Reviewer greps for "class .*\\(.*ModeratableMixin" and counts ≥10 models.
- **Depends on.** —

#### FR-602 — Layer 1 — Deterministic checks
- **Description.** Synchronous pre-checks: protected-class lexicon (Fair Housing), prohibited-pattern regex (phone numbers/emails embedded in non-vendor content per policy), URL safelist, content length. Outcome: `auto_reject | continue | auto_approve_low_risk`.
- **Priority.** M
- **Source.** D
- **Acceptance.** Layer 1 runs in-process <50ms; `apps/moderation/services/layer1_deterministic.py`; regression suite includes 30+ fair-housing fixtures.
- **Depends on.** FR-601, `docs/research/platform-guidelines-v1.md`

#### FR-603 — Layer 2 — Gemini classifier with injection_guard
- **Description.** Gemini 2.5 Flash classifies content into rubric: `safe | borderline | violating`. Output parsed by `injection_guard.parse_classifier_response`, which fails closed (treats parse error as `borderline → human queue`).
- **Priority.** M
- **Source.** D, safety contract #1
- **Acceptance.** `apps/moderation/services/pipeline.py` calls Gemini via Celery, uses pinned model + system prompt with injection-defense preamble (see `docs/research/ai-moderation-prompt-injection.md`); parse failure → human queue, NEVER auto-approve; adversarial fixtures (`apps/moderation/tests/fixtures/prompt_injection_attacks.json`) all blocked.
- **Depends on.** FR-602, FR-3xx (Celery)

#### FR-604 — Layer 3 — Human queue
- **Description.** Items marked `borderline` or flagged by users land in mod console queue. Moderator approves/rejects with reason.
- **Priority.** M
- **Source.** D
- **Acceptance.** `Flag` and `ModerationDecision` rows; mod console shows queue ordered by `(severity, created_at)`; decision writes audit row; auto-rejected attacks logged but not surfaced for approval.
- **Depends on.** FR-603, FR-7xx

#### FR-605 — User flag
- **Description.** Authenticated user can flag content (post, comment, thread, reply, vendor service, review). Flagging adds to `Flag` table; ≥3 flags on one item escalates regardless of pipeline state.
- **Priority.** M
- **Source.** All
- **Acceptance.** `POST /api/flags/` with `{target_type, target_id, reason}`; rate-limited 30 flags/day/user; `flag_count` denormalized; ≥3 flags → re-enqueue Layer 2 + park in human queue.
- **Depends on.** FR-601

#### FR-606 — Audit trail (moderation)
- **Description.** Every pipeline run, every moderator action, every auto-decision writes a `ModerationDecision` row with input hash, layer, outcome, reason, model version (if Layer 2). Append-only.
- **Priority.** M
- **Source.** D
- **Acceptance.** `ModerationDecision` has no DELETE allowed for non-superusers; mod console exposes filterable history; inputs not stored verbatim (only hash) to limit PII duplication.
- **Depends on.** FR-602–FR-604

#### FR-607 — Adversarial fixtures
- **Description.** A growing JSON fixture set of prompt-injection / fair-housing-violation / spam attempts. CI gates that every fixture is correctly handled (attack rejected, benign approved).
- **Priority.** M
- **Source.** D, safety contract #1
- **Acceptance.** ≥5 new fixtures added per phase. CI fails if any attack auto-approved. Regression results posted to PR.
- **Depends on.** FR-603

#### FR-608 — Pipeline never approves attacks
- **Description.** Hard invariant: `injection_guard` parse error → human queue (not auto-approve). Layer 2 returning unexpected schema → human queue. Network timeout to Gemini → human queue.
- **Priority.** M
- **Source.** D, safety contract #1
- **Acceptance.** Test `test_pipeline_fails_closed_on_parse_error` and `test_pipeline_fails_closed_on_timeout` green; mutation testing confirms no path approves on error.
- **Depends on.** FR-603, FR-604

#### FR-609 — Moderation latency target
- **Description.** Pipeline median latency from content submit to status decision <30s for non-queue path; queue items decided <4h median by humans.
- **Priority.** S
- **Source.** D, success criteria
- **Acceptance.** Sentry metric `moderation.pipeline.duration` p50 <30s; mod-queue resolution metric on operator dashboard p50 <4h.
- **Depends on.** FR-602–FR-604

#### FR-610 — Notify author of decision
- **Description.** On reject, author receives email + in-app notification with reason. On approve (after queue), no notification (silent).
- **Priority.** S
- **Source.** A, B, C
- **Acceptance.** `ModerationDecision.outcome='reject'` triggers Postmark email via Celery; in-app notification table updated.
- **Depends on.** FR-604

### FR-7xx — Control Surfaces

#### FR-701 — Django admin (break-glass)
- **Description.** Standard Django admin protected by 2FA + IP allowlist. Used for emergency data fixes only.
- **Priority.** M
- **Source.** D
- **Acceptance.** `/admin/` requires `is_staff`, active TOTP device, source IP in `ADMIN_IP_ALLOWLIST` env var. Non-allowlisted IPs return 404. Every admin save writes ActionLog.
- **Depends on.** FR-107, safety contract #4

#### FR-702 — Mod console
- **Description.** Web UI at `/mod` listing the moderation queue with filters (severity, type, age, flag count). Approve/reject buttons require typed reason.
- **Priority.** M
- **Source.** D
- **Acceptance.** Mod role required; queue paginated; bulk-action limited to 25 items at once; every action audit-logged.
- **Depends on.** FR-604

#### FR-703 — Operator dashboard
- **Description.** Web UI at `/ops` showing platform health: MAU, mod-queue depth & age, Gemini spend by day, vendor onboarding pipeline, top flagged users, pipeline false-positive estimate.
- **Priority.** M
- **Source.** D, success criteria
- **Acceptance.** Operator role required; charts via lightweight client lib (Recharts); data computed in Celery beat tasks and cached in Redis (refresh every 5min); accepts time-window filters.
- **Depends on.** FR-606, FR-506

#### FR-704 — Admin IP allowlist middleware
- **Description.** `AdminIPAllowlistMiddleware` blocks `/admin/*` from non-allowlisted IPs.
- **Priority.** M
- **Source.** D, safety contract #4
- **Acceptance.** Existing middleware (`apps/admin_tools/`); allowlist read from env; block returns 404 (not 403, to avoid endpoint disclosure).
- **Depends on.** FR-701

#### FR-705 — Role decorators / permission classes
- **Description.** DRF permission classes `IsRealtor`, `IsVendor`, `IsModerator`, `IsOperator`, `IsAdmin`. View-level enforcement.
- **Priority.** M
- **Source.** D
- **Acceptance.** All endpoints in §FR-1xx–FR-5xx use one of the permission classes; default-deny applied at viewset base class.
- **Depends on.** FR-103

#### FR-706 — Action audit log (staff writes)
- **Description.** Every write (create/update/delete) by `is_staff=True` user writes an `ActionLog` row via Django signals (`apps/audit/signals.py`).
- **Priority.** M
- **Source.** D, safety contract #3
- **Acceptance.** Hooked on `post_save` and `post_delete` for relevant models; row includes actor, IP, target model, target id, before/after diff (truncated to 4KB).
- **Depends on.** —

#### FR-707 — Access audit log
- **Description.** Mod/operator/admin GETs to sensitive views (mod console, operator dashboard, admin) write `AccessLog` rows.
- **Priority.** S
- **Source.** D
- **Acceptance.** Middleware applied to relevant URL prefixes; no PII logged beyond user id and path.
- **Depends on.** —

#### FR-708 — Append-only audit guarantee
- **Description.** No DELETE permission on `ActionLog`, `AccessLog`, `LicenseCheck`, `ModerationDecision` for any role including superuser via app-layer enforcement (DB constraint or model `Meta.permissions`).
- **Priority.** M
- **Source.** D, safety contract #3
- **Acceptance.** Models override `delete()` to raise `PermissionError`; CI test confirms.
- **Depends on.** FR-706, FR-707

### FR-8xx — SEO / Social / Public Surface Hygiene

#### FR-801 — Sitemap.xml
- **Description.** Auto-generated XML sitemap for posts, forum threads, vendor profiles, services, tool landing pages. Updated on publish.
- **Priority.** M
- **Source.** C (acquisition)
- **Acceptance.** `/sitemap.xml` returns valid sitemap protocol; <50K URLs per file with index file at scale.
- **Depends on.** FR-2xx, FR-3xx, FR-4xx

#### FR-802 — robots.txt
- **Description.** Allows public crawling; disallows `/admin`, `/mod`, `/ops`, `/api/auth`, `/account`, `/marketplace/inbox`.
- **Priority.** M
- **Source.** D
- **Acceptance.** `/robots.txt` static asset; CI test confirms presence of disallow lines.
- **Depends on.** —

#### FR-803 — JSON-LD structured data
- **Description.** Every post/thread/vendor/service emits appropriate schema.org JSON-LD: `Article`, `BlogPosting`, `DiscussionForumPosting`, `LocalBusiness`, `Service`, `BreadcrumbList`.
- **Priority.** M
- **Source.** C (acquisition)
- **Acceptance.** Lighthouse SEO ≥95; Google Rich Results Test passes for sample of each type.
- **Depends on.** FR-2xx, FR-3xx, FR-4xx

#### FR-804 — Open Graph / Twitter Card meta
- **Description.** Every public route renders OG title, description, image, and `twitter:card`.
- **Priority.** M
- **Source.** C
- **Acceptance.** OG image generated server-side per post (template + R2 upload) at publish time.
- **Depends on.** FR-2xx

#### FR-805 — RSS feeds
- **Description.** Per-tag and global RSS feeds for posts; Atom 1.0.
- **Priority.** S
- **Source.** A, C
- **Acceptance.** `/feed/`, `/feed/<tag>/`; valid against W3C feed validator.
- **Depends on.** FR-201

#### FR-806 — Canonical URLs
- **Description.** Every public page has `<link rel="canonical">`. Pagination uses `rel=prev/next` correctly.
- **Priority.** M
- **Source.** C
- **Acceptance.** Lighthouse SEO confirms.
- **Depends on.** —

#### FR-807 — Hreflang (en-us only)
- **Description.** Single locale at v1; hreflang `en-us` declared.
- **Priority.** S
- **Source.** —
- **Acceptance.** Set globally in Next.js root layout.
- **Depends on.** —

---

## 4. Non-Functional Requirements

Quality attributes per ISO/IEC 25010:2011. Measurable thresholds throughout.

### NFR-1xx — Performance Efficiency

#### NFR-101 — LCP (Largest Contentful Paint)
- **Threshold.** Mobile p75 < 2.5s on Slow 4G profile across top-20 routes.
- **Verification.** Real-user monitoring via Sentry Performance + synthetic Lighthouse-CI on PR.

#### NFR-102 — TTFB
- **Threshold.** API p95 < 200ms for cached routes, < 500ms uncached at 1K concurrent. SSR pages p95 < 350ms TTFB.
- **Verification.** k6 load test in CI; Sentry Performance.

#### NFR-103 — JS bundle size (initial)
- **Threshold.** Initial JS bundle (per route) < 100KB gzipped excluding fonts.
- **Verification.** `next build` analyze in CI; `bundlewatch` gate.

#### NFR-104 — Concurrent users
- **Threshold.** 1,000 concurrent users sustained 5 min, p95 5xx rate <0.1%, p95 latency <1s end-to-end.
- **Verification.** k6 staged load test.

#### NFR-105 — Database query budget
- **Threshold.** Any single API endpoint executes ≤ 12 DB queries (N+1 prevention via `select_related`/`prefetch_related`).
- **Verification.** `django-silk` in dev; `nplusone` middleware fails CI on N+1 detection.

#### NFR-106 — Caching strategy
- **Threshold.** Public list and detail responses use `Cache-Control: public, s-maxage=60` and Caddy edge cache; cache hit ratio ≥80% on anonymous traffic.
- **Verification.** Caddy access logs analyzed weekly.

#### NFR-107 — Image delivery
- **Threshold.** All images served via R2 + Cloudflare CDN; auto-WebP/AVIF where supported; LCP image preloaded.
- **Verification.** Lighthouse mobile ≥95.

### NFR-2xx — Security

#### NFR-201 — OWASP Top 10 (2021) hardening
- **Threshold.** 0 High/Critical findings from external pen-test pre-launch.
- **Verification.** External pen-test, Sprint 7. Internal `security-review` skill run end of every phase.

#### NFR-202 — JWT in httpOnly+SameSite=Strict cookies
- **Threshold.** Access (`yw_access`, 15min) and refresh (`yw_refresh`, 7d) cookies are httpOnly, SameSite=Strict, Secure (in production), Path=/.
- **Verification.** Test `test_auth_cookies_are_hardened`; security-review checklist.

#### NFR-203 — CSRF protection
- **Threshold.** Double-submit cookie pattern for all state-changing requests. SameSite=Strict provides primary defense; CSRF token provides defense-in-depth.
- **Verification.** Adversarial CSRF fixture; cross-origin POST returns 403.

#### NFR-204 — Content Security Policy with nonces
- **Threshold.** CSP enforced (not report-only): `default-src 'self'; script-src 'self' 'nonce-<per-request>'; style-src 'self' 'nonce-<per-request>'; img-src 'self' data: <r2-domain>; frame-src https://www.youtube.com https://www.instagram.com; object-src 'none'; base-uri 'self'; form-action 'self'`. No `unsafe-inline`, no `unsafe-eval`.
- **Verification.** CSP-evaluator passes; Lighthouse "Best Practices" 100.

#### NFR-205 — HTTP security headers
- **Threshold.** `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
- **Verification.** Mozilla Observatory ≥A.

#### NFR-206 — Rate limiting
- **Threshold.** Per-IP and per-user rate limits at Caddy + Django level: 60 req/min anon, 300 req/min auth; auth endpoints 6/10min via django-axes; AI tools per-tier (FR-505).
- **Verification.** k6 burst test confirms 429s; Sentry alerts on 429 spike.

#### NFR-207 — Encryption at rest
- **Threshold.** Postgres at-rest encryption (Railway-provided), R2 at-rest encryption (Cloudflare default), env secrets via Railway secrets manager.
- **Verification.** Vendor attestation; security-review confirms.

#### NFR-208 — Encryption in transit
- **Threshold.** TLS 1.2+ at all boundaries (Caddy auto-managed Let's Encrypt; minimum cipher suites per Mozilla "intermediate"); HSTS preload.
- **Verification.** SSL Labs grade A or A+.

#### NFR-209 — Signed media URLs
- **Threshold.** All R2 uploads (uploads in particular) and any private downloads use time-limited signed URLs (≤15min).
- **Verification.** Test confirms URL expiry.

#### NFR-210 — Secrets handling
- **Threshold.** No secrets in repo; `.env.example` placeholders only; `django-environ` reads from env; Railway/Fly secrets in production. Pre-commit hook scans for high-entropy strings.
- **Verification.** `gitleaks` in CI; security-review.

#### NFR-211 — Dependency vulnerabilities
- **Threshold.** 0 known High/Critical CVEs in production dependencies. `pip-audit` and `npm audit` gate CI.
- **Verification.** CI job; weekly Dependabot.

#### NFR-212 — Prompt-injection adversarial coverage
- **Threshold.** ≥5 new fixtures added per phase; pipeline rejects 100% of attacks; 0 false-negative regressions.
- **Verification.** CI fixture suite (`apps/moderation/tests/fixtures/`).

#### NFR-213 — Account enumeration resistance
- **Threshold.** Login, signup, password-reset endpoints return identical timing and identical error message regardless of email existence.
- **Verification.** Timing-side-channel test in CI; manual security review.

### NFR-3xx — Reliability / Availability

#### NFR-301 — Uptime SLO
- **Threshold.** 99.5% uptime rolling 30-day (≈ 3.6h/month allowed downtime).
- **Verification.** Better Stack heartbeat to `/healthz`.

#### NFR-302 — Error budget
- **Threshold.** ≤ 0.5% of requests return 5xx in any 24h window. Burn-rate alert at 50% budget consumed.
- **Verification.** Sentry; Better Stack alerts.

#### NFR-303 — RTO (Recovery Time Objective)
- **Threshold.** Service restoration after major incident ≤ 4 hours.
- **Verification.** Documented runbook (`docs/RUNBOOK.md`) with timed restore drill quarterly.

#### NFR-304 — RPO (Recovery Point Objective)
- **Threshold.** ≤ 24 hours data loss tolerance. Postgres daily snapshots retained 7 days; on-demand backup before any migration.
- **Verification.** Restore drill quarterly.

#### NFR-305 — Health check
- **Threshold.** `/healthz` returns 200 with `{"db": "ok", "redis": "ok"}` checks within 200ms.
- **Verification.** Better Stack heartbeat every 60s.

#### NFR-306 — Graceful Celery failure
- **Threshold.** Celery task retries up to 3× with exponential backoff (10s, 60s, 360s); permanent failure writes Sentry event and surfaces in operator dashboard.
- **Verification.** Failure-injection test.

#### NFR-307 — External dependency degradation
- **Threshold.** When ARELLO is unreachable, license verify returns "temporarily unavailable, retry in 15min" rather than 5xx; user not blocked from non-realtor actions. Same for Gemini, Postmark, R2.
- **Verification.** Adverse-condition tests with mocked timeouts.

### NFR-4xx — Maintainability

#### NFR-401 — Test coverage
- **Threshold.** ≥80% line coverage on `apps/accounts`, `apps/moderation`, `apps/audit`. ≥60% project-wide.
- **Verification.** `pytest --cov` gate in CI.

#### NFR-402 — Linting / type-checking
- **Threshold.** `ruff check . && ruff format --check .` clean. `mypy apps/` clean (strict on `apps/accounts`, `apps/moderation`, `apps/audit`).
- **Verification.** CI pre-merge.

#### NFR-403 — Templates lint
- **Threshold.** `djlint templates/` clean.
- **Verification.** CI pre-merge.

#### NFR-404 — ADR per major decision
- **Threshold.** Any decision changing stack, transport, security boundary, or contract gets an ADR.
- **Verification.** PR review checklist; ADR count tracked.

#### NFR-405 — OpenAPI auto-generated
- **Threshold.** drf-spectacular generates `/api/schema/` reflecting all endpoints; CI fails if endpoint added without doc.
- **Verification.** OpenAPI diff job.

#### NFR-406 — Conventional Commits
- **Threshold.** Every commit follows Conventional Commits (`feat(scope): ...`, `fix(scope): ...`, etc.).
- **Verification.** commitlint pre-receive (server) + commitizen pre-commit hook.

#### NFR-407 — Onboarding time
- **Threshold.** A new contributor reaches a green local test run within 30 minutes following `CLAUDE.md` "Local dev" section.
- **Verification.** Quarterly drill.

### NFR-5xx — Usability / Accessibility

#### NFR-501 — Lighthouse mobile performance
- **Threshold.** ≥95 on top-20 routes (homepage, posts list, post detail, forum index, thread detail, marketplace search, vendor profile, tool landing, etc.).
- **Verification.** Lighthouse-CI on PR; nightly run on production.

#### NFR-502 — axe-core violations
- **Threshold.** 0 axe-core violations on any public route. Manual NVDA + VoiceOver pass for forms.
- **Verification.** axe Playwright integration in CI.

#### NFR-503 — Mobile-first breakpoint
- **Threshold.** Layouts work at 375×667 (iPhone SE) without horizontal scroll. Touch targets ≥44×44 CSS pixels.
- **Verification.** Playwright viewport tests.

#### NFR-504 — Keyboard navigation
- **Threshold.** Every interactive element reachable and operable via keyboard alone. Visible focus indicator with ≥3:1 contrast against background.
- **Verification.** Manual keyboard pass; axe integration.

#### NFR-505 — Screen reader
- **Threshold.** Forms have explicit labels, errors are `aria-live=polite`, dynamic content updates are announced.
- **Verification.** NVDA pass on signup, lead inquiry, and AI tool flows.

#### NFR-506 — Color contrast
- **Threshold.** Body text ≥4.5:1 against background; large text and UI components ≥3:1. Validated for the gold-on-dark palette.
- **Verification.** Design system tokens checked in `docs/research/design-system-reference.md`; axe color-contrast rule.

#### NFR-507 — Reduced motion
- **Threshold.** All Motion One / Framer Motion animations honor `prefers-reduced-motion: reduce`.
- **Verification.** Manual test with OS toggle; unit test of motion provider.

#### NFR-508 — Form usability
- **Threshold.** Inline validation; submit disabled while pending; clear error attribution; never lose user input on error.
- **Verification.** Playwright e2e.

### NFR-6xx — Compatibility

#### NFR-601 — Browser support
- **Threshold.** Last 2 major versions of Chrome, Firefox, Safari, Edge. iOS Safari 16+, Android Chrome 110+.
- **Verification.** BrowserStack smoke run before launch; caniuse policy in `package.json` `browserslist`.

#### NFR-602 — Progressive enhancement
- **Threshold.** Core read paths (posts, forum threads, vendor profiles) usable without JavaScript (SSR HTML serves complete content).
- **Verification.** `curl` + parse test; Lighthouse "JS disabled" run.

#### NFR-603 — No paywall via JavaScript
- **Threshold.** No content gated only by client-side JS check; auth gating enforced server-side.
- **Verification.** Bypass test with cookies cleared and JS disabled.

### NFR-7xx — Scalability

#### NFR-701 — 10K MAU baseline
- **Threshold.** Reference architecture (`SAD.md` §6) sustains 10K MAU on Railway standard tiers without degradation.
- **Verification.** k6 load test simulating 10K MAU traffic profile.

#### NFR-702 — 100K MAU schema-readiness
- **Threshold.** Postgres schema, indexes, and partitioning strategy support 100K MAU without table-rewrite migrations. Append-only logs partitioned monthly.
- **Verification.** Schema review; explicit `CREATE INDEX` plan documented.

#### NFR-703 — pgvector future-proofing
- **Threshold.** pgvector extension installed and `embedding vector(768)` columns reserved on `Post`, `ForumThread`, `Service` (NULL until Phase 9+).
- **Verification.** Migration applied; column exists.

#### NFR-704 — Worker horizontal scale
- **Threshold.** Celery workers can be scaled by replica count without code change. Img-worker queue independent from default queue (heavy-Pillow isolation).
- **Verification.** Two workers × general queue + one worker × img queue all green.

#### NFR-705 — Stateless web tier
- **Threshold.** Frontend (Next.js) and api (Django) processes hold no per-instance state beyond connection pools. Sessions/cache in Redis. Rolling restart causes 0 user-visible errors.
- **Verification.** Restart drill in staging.

### NFR-8xx — Compliance

#### NFR-801 — Fair Housing Act compliance
- **Threshold.** Layer 1 deterministic check covers protected classes (race, color, religion, national origin, sex, disability, familial status); Layer 2 includes Fair Housing rubric in prompt; takedown SOP documented.
- **Verification.** 30+ Fair Housing fixtures pass; legal review of prompt + lexicon.

#### NFR-802 — RESPA Section 8 compliance
- **Threshold.** No referral fees or kickbacks between platform and vendors/lenders/realtors. No `Payment` table. No revenue-share UI.
- **Verification.** Schema review confirms; ADR-0004 in repo.

#### NFR-803 — ADA Section 508 / WCAG 2.1 AA
- **Threshold.** Public routes meet WCAG 2.1 AA. Internal admin/mod/ops surfaces strive for AA but accept documented exceptions.
- **Verification.** axe-core CI; manual VPAT-style check pre-launch.

#### NFR-804 — GDPR-shaped data rights (defensive)
- **Threshold.** User-initiated data export (FR-113) and account deletion (FR-112) implemented. Privacy policy lists data collected. No tracking pixels beyond first-party Sentry & Better Stack.
- **Verification.** End-to-end test of export + delete; legal review of privacy policy.

#### NFR-805 — CAN-SPAM
- **Threshold.** Marketing email opt-in only; transactional email exempt. Every marketing email contains physical address + 1-click unsubscribe; honored within 10 days.
- **Verification.** Postmark suppression list audit.

#### NFR-806 — WA Consumer Protection Act
- **Threshold.** Truth-in-advertising on AI-tool landing pages (no implied human-written when AI-generated; no implied license without verification).
- **Verification.** Legal review of marketing copy.

#### NFR-807 — Audit immutability
- **Threshold.** `ActionLog`, `AccessLog`, `LicenseCheck`, `ModerationDecision` rows are append-only; no in-app delete; DB-level constraint or trigger preferred.
- **Verification.** Test attempts delete; raises `PermissionError`.

#### NFR-808 — Data minimization
- **Threshold.** No collection of SSN, DOB, government ID images. Vendor identity verification via attestation; license verification via ARELLO is the only government-ID interaction.
- **Verification.** Schema review.

---

## 5. External Interfaces

Interface details live in `docs/ICD.md`. Summary:

- **ARELLO** — REST; license-by-number lookup; rate-limited; raw response stored in `LicenseCheck.raw_payload`. (`docs/research/arello-api-notes.md`)
- **Gemini API** — Google Generative AI SDK; 2.5 Flash for moderation, 2.5 Pro for tools. (`docs/adr/0003`)
- **Cloudflare R2** — S3-compatible; signed PUT for uploads, signed GET for private downloads. (ADR-0008)
- **Postmark** — django-anymail backend; transactional only. (ADR-0009)
- **Sentry** — DSN per env; performance + errors.
- **Better Stack** — heartbeat to `/healthz`; uptime monitoring + log drain.
- **Public REST API** — DRF + drf-spectacular OpenAPI; primary frontend consumer.
- **Public read-only GraphQL** — Strawberry; discovery and partner integrations. (ADR-0007)

---

## 6. Appendices

### 6.1 Glossary

See §1.3.

### 6.2 Requirements Traceability

A full Requirements Traceability Matrix (RTM) lives in `docs/RTM.md`. Each FR/NFR maps to (a) implementing code path, (b) test(s), (c) phase plan in `.planning/phases/`. Summary counts:

| Group | Count |
|---|---|
| FR-1xx Auth & Accounts | 14 |
| FR-2xx Content | 12 |
| FR-3xx Forum | 8 |
| FR-4xx Marketplace | 12 |
| FR-5xx AI Tools | 9 |
| FR-6xx Moderation | 10 |
| FR-7xx Control Surfaces | 8 |
| FR-8xx SEO/Social | 7 |
| **FR Total** | **80** |
| NFR-1xx Performance | 7 |
| NFR-2xx Security | 13 |
| NFR-3xx Reliability | 7 |
| NFR-4xx Maintainability | 7 |
| NFR-5xx Usability | 8 |
| NFR-6xx Compatibility | 3 |
| NFR-7xx Scalability | 5 |
| NFR-8xx Compliance | 8 |
| **NFR Total** | **58** |

### 6.3 Priority distribution

- Must (M): 102 requirements
- Should (S): 28 requirements
- Could (C): 0 requirements (deliberate — anything "could" is deferred to v2 backlog)

### 6.4 Versioning policy

Material additions or removals require a minor version bump (1.0 → 1.1) and an entry in §Change Log. Breaking architectural changes (e.g., a new ADR superseding ADR-0001) require a major version bump (1.x → 2.0).
