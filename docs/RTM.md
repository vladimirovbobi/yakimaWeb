# Requirements Traceability Matrix (RTM) — Yakima Real Estate Hub

## 1. Document Control

| Field | Value |
|---|---|
| Document | Requirements Traceability Matrix |
| Project | Yakima Real Estate Hub |
| Version | 1.0 |
| Date | 2026-05-03 |
| Owner | Yakima Engineering |
| Status | Approved baseline |
| Related | SRS.md, SAD.md, ICD.md, MTP.md, ACCESS-MATRIX.md |

---

## 2. Summary

| Metric | Count |
|---|---|
| Total requirements | 102 |
| Functional (FR-1xx … FR-8xx) | 70 |
| Non-functional (NFR-1xx … NFR-8xx) | 32 |
| Status: Planned | 102 (100%) |
| Status: In progress | 0 (0%) |
| Status: Verified | 0 (0%) |
| Status: Deferred | 0 (0%) |

This baseline captures every SRS requirement at the start of Sprint 1. As features ship and tests pass, the Status column advances `Planned → In progress → Verified`. Items that move out of scope move to `Deferred` with a link to the ADR or scope-change record.

Legend:

- **Priority**: M = Must (launch blocker), S = Should (launch desirable), C = Could (post-launch nice), W = Won't (out of scope this version).
- **Source**: SRS section, stakeholder, ADR, or other origin.
- **SAD Component**: app/module owning the implementation.
- **ICD Endpoint(s)**: API contracts that exercise the requirement; "n/a" for cross-cutting or non-API requirements.
- **Test Case(s)**: scenario IDs from MTP.md (E2E-NN), unit/integration suite paths, perf/security tools.
- **Status**: Planned | In progress | Verified | Deferred.

---

## 3. Functional Requirements

### 3.1 FR-1xx — Authentication & Account

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-101 | Email-based signup with password confirmation and verification email | M | SRS §3.1 | apps/accounts | POST /api/v1/auth/signup/, POST /api/v1/auth/verify-email/<key>/ | E2E-02; tests/test_api/test_auth_signup.py | Planned |
| FR-102 | Login with rate limiting and django-axes lockout | M | SRS §3.1 | apps/accounts, apps/admin_tools | POST /api/v1/auth/login/ | E2E-02; tests/test_api/test_auth_login.py; load login storm | Planned |
| FR-103 | JWT issued in httpOnly+SameSite=Strict cookies | M | SRS §3.1 | apps/accounts | POST /api/v1/auth/login/, POST /api/v1/auth/refresh/ | E2E-29; tests/test_api/test_jwt_cookies.py | Planned |
| FR-104 | Silent refresh of access token via refresh cookie rotation | M | SRS §3.1 | apps/accounts | POST /api/v1/auth/refresh/ | E2E-29; tests/test_api/test_jwt_refresh.py | Planned |
| FR-105 | Logout invalidates refresh JTI in Redis blacklist | M | SRS §3.1 | apps/accounts | POST /api/v1/auth/logout/ | tests/test_api/test_auth_logout.py | Planned |
| FR-106 | Password reset via email link with token expiry | M | SRS §3.1 | apps/accounts | POST /api/v1/auth/password-reset/, POST /api/v1/auth/password-reset-confirm/ | tests/test_api/test_password_reset.py | Planned |
| FR-107 | Optional TOTP 2FA setup and verification for any user | S | SRS §3.1 | apps/accounts | POST /api/v1/auth/2fa/totp/setup/, POST /api/v1/auth/2fa/totp/verify/ | tests/test_api/test_2fa.py | Planned |
| FR-108 | Mandatory TOTP 2FA for is_staff users | M | SRS §3.1 | apps/admin_tools | n/a (django-otp middleware) | E2E-19; tests/test_admin/test_2fa_required.py | Planned |
| FR-109 | Realtor license verification via ARELLO with full audit trail | M | SRS §3.2 / ADR-0002 | apps/accounts | POST /api/v1/realtor/verify/, GET /api/v1/streams/realtor/verify/<id>/ | E2E-03; tests/test_api/test_realtor_verify.py; tests/test_arello_client.py | Planned |
| FR-110 | LicenseCheck row written for every ARELLO call with raw JSON; admin blocks delete | M | SRS §3.2 | apps/accounts, apps/audit | n/a | tests/test_models/test_license_check.py; tests/test_admin/test_license_check_immutable.py | Planned |
| FR-111 | Realtor profile editable post-verification with re-moderation on bio change | M | SRS §3.2 | apps/accounts, apps/moderation | PATCH /api/v1/realtor/profile/ | tests/test_api/test_realtor_profile.py | Planned |
| FR-112 | Vendor profile model and onboarding wizard (5-step) | M | SRS §3.3 | apps/marketplace | POST /api/v1/vendors/onboard/<step>/, PATCH /api/v1/vendors/onboard/<step>/ | E2E-09; tests/test_api/test_vendor_onboarding.py | Planned |
| FR-113 | Per-user notifications feed with read/unread state | S | SRS §3.4 | apps/core | GET /api/v1/me/notifications/ | tests/test_api/test_notifications.py | Planned |
| FR-114 | User preferences (theme, digest cadence) persisted | C | SRS §3.4 | apps/accounts | GET /api/v1/me/, PATCH /api/v1/me/ | tests/test_api/test_me_preferences.py | Planned |
| FR-115 | Account deletion with 30-day grace period and audit | S | SRS §3.5 | apps/accounts, apps/audit | POST /api/v1/me/delete/ (Phase 8) | tests/test_api/test_account_delete.py | Planned |

### 3.2 FR-2xx — Content System

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-201 | Polymorphic Post model (yakimaweb / blog / landing) | M | SRS §4.1 | apps/content | GET /api/public/v1/posts/, GET /api/public/v1/posts/<slug>/ | tests/test_models/test_post.py; tests/test_api/test_posts_public.py | Planned |
| FR-202 | Realtor authoring of blog posts with markdown editor | M | SRS §4.1 | apps/content, frontend/(realtor)/blog/new/ | POST /api/v1/posts/ (Phase 2) | E2E-04; tests/test_api/test_posts_create.py | Planned |
| FR-203 | Threaded comments with nested replies and parent_id | M | SRS §4.2 | apps/content | GET /api/public/v1/posts/<slug>/comments/, POST /api/v1/posts/<slug>/comments/ | E2E-05, E2E-06; tests/test_api/test_comments.py | Planned |
| FR-204 | Comment moderation runs asynchronously via Celery | M | SRS §4.2 / ADR-0003 | apps/moderation | n/a (signal-driven) | tests/test_signals/test_comment_moderate.py | Planned |
| FR-205 | Lead-magnet landing pages render via the Post `landing` kind | S | SRS §4.3 | apps/content | GET /api/public/v1/posts/<slug>/ | tests/test_api/test_landing_pages.py | Planned |
| FR-206 | Full-text search over posts using Postgres tsvector | S | SRS §4.4 | apps/content | GET /api/public/v1/posts/?q= | E2E-26; tests/test_api/test_post_search.py | Planned |
| FR-207 | Post categories and tags (m2m) | S | SRS §4.5 | apps/content | GET /api/public/v1/posts/?category=, ?tag= | tests/test_api/test_post_filters.py | Planned |
| FR-208 | SEO metadata (canonical, og_image, meta_description) on every public post | M | SRS §4.6 | apps/content, frontend/(public)/blog/[slug]/ | GET /api/public/v1/posts/<slug>/ | tests/test_api/test_post_seo.py; E2E-04 (HTML assertion) | Planned |
| FR-209 | Reading time computed and exposed in API | C | SRS §4.7 | apps/content | GET /api/public/v1/posts/<slug>/ | tests/test_models/test_reading_time.py | Planned |

### 3.3 FR-3xx — Forum

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-301 | ForumThread + ForumReply models with soft-deletion | M | SRS §5.1 | apps/forum | GET /api/public/v1/community/<slug>/threads/, POST /api/v1/community/<slug>/threads/ | tests/test_models/test_forum.py | Planned |
| FR-302 | Generic Vote model usable by thread, reply, comment | M | SRS §5.2 | apps/forum | POST /api/v1/forum/items/<id>/vote/ | E2E-08; tests/test_api/test_vote.py | Planned |
| FR-303 | Hot ranking based on score + age (Reddit-style) | M | SRS §5.3 | apps/forum | GET /api/public/v1/community/<slug>/threads/?ordering=hot | tests/test_models/test_ranking.py | Planned |
| FR-304 | Tag system on threads | S | SRS §5.4 | apps/forum | GET /api/public/v1/community/<slug>/threads/?tag= | tests/test_api/test_thread_tags.py | Planned |
| FR-305 | Anonymous browse, authenticated post/vote | M | SRS §5.5 | apps/forum, apps/admin_tools | n/a (permission classes) | E2E-08, E2E-27; tests/test_permissions/test_forum_perms.py | Planned |
| FR-306 | Locked / pinned thread states for moderators | S | SRS §5.6 | apps/forum, apps/moderation | POST /api/v1/mod/items/<id>/decision/ | tests/test_api/test_thread_locked.py | Planned |
| FR-307 | Thread reply pagination with cursor | M | SRS §5.7 | apps/forum | GET /api/public/v1/community/threads/<slug>/?cursor= | tests/test_api/test_thread_replies.py | Planned |

### 3.4 FR-4xx — Marketplace

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-401 | Category tree using treebeard with arbitrary depth | M | SRS §6.1 | apps/marketplace | GET /api/public/v1/services/?category= | tests/test_models/test_category_tree.py | Planned |
| FR-402 | Service model under Category with Basic/Standard/Premium packages | M | SRS §6.2 / ADR-0004 | apps/marketplace | GET /api/public/v1/services/<slug>/ | tests/test_models/test_service_packages.py | Planned |
| FR-403 | Bundle (recurring) with BundleItem → Service | S | SRS §6.3 | apps/marketplace | GET /api/public/v1/services/<slug>/ (`bundles[]`) | tests/test_models/test_bundle.py | Planned |
| FR-404 | Vendor public profile page | M | SRS §6.4 | apps/marketplace | GET /api/public/v1/vendors/<slug>/ | E2E-09; tests/test_api/test_vendor_public.py | Planned |
| FR-405 | Service search with full-text and filters | M | SRS §6.5 | apps/marketplace | GET /api/public/v1/services/?q=&category=&min_price=&max_price=&has_bundle= | E2E-25; tests/test_api/test_service_search.py | Planned |
| FR-406 | Lead model with status state machine (open→in_progress→won/lost) | M | SRS §6.6 | apps/marketplace | POST /api/v1/services/<slug>/inquiries/ | E2E-10; tests/test_models/test_lead_state.py | Planned |
| FR-407 | LeadMessage thread between buyer and vendor | M | SRS §6.6 | apps/marketplace | POST /api/v1/leads/<id>/messages/, GET /api/v1/streams/leads/<id>/messages/ | E2E-10; tests/test_api/test_lead_messages.py | Planned |
| FR-408 | Verified-only Review (1:1 with won Lead) | M | SRS §6.7 | apps/marketplace | POST /api/v1/leads/<id>/review/ | E2E-10; tests/test_api/test_review.py | Planned |
| FR-409 | Vendor onboarding wizard with autosave + publish gate | M | SRS §6.8 | apps/marketplace | POST/PATCH /api/v1/vendors/onboard/<step>/ | E2E-09; tests/test_api/test_vendor_onboarding.py | Planned |
| FR-410 | Lead-gen only — no payments processed in v1 | M | ADR-0004 | apps/marketplace | n/a (architectural) | tests/test_models/test_no_payment_field.py | Planned |
| FR-411 | Service gallery images served via Cloudflare R2 + img-worker | M | SRS §6.9 | apps/marketplace, img-worker container | n/a (CDN URL) | tests/test_storage/test_r2_upload.py | Planned |
| FR-412 | Lead inquiry rate limit per buyer | S | SRS §6.10 | apps/marketplace | POST /api/v1/services/<slug>/inquiries/ | tests/test_api/test_inquiry_throttle.py | Planned |
| FR-413 | Vendor mailbox digest of new leads | S | SRS §6.11 | apps/marketplace, apps/core | n/a (Celery beat) | tests/test_celery/test_lead_digest.py | Planned |
| FR-414 | Marketplace category browsing public, no auth | M | SRS §6.12 | apps/marketplace | GET /api/public/v1/services/, /api/public/v1/vendors/ | E2E-01, E2E-25 | Planned |
| FR-415 | Vendor status state managed by operators (approved/rejected/paused) | M | SRS §6.13 | apps/operations | POST /api/v1/ops/vendors/<id>/status/ | tests/test_api/test_ops_vendor_status.py | Planned |

### 3.5 FR-5xx — AI Tools

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-501 | Description writer using Gemini 2.5 Pro for property listings | M | SRS §7.1 / ADR-0003 | apps/tools | POST /api/v1/tools/description/, GET /api/v1/streams/tools/<task_id>/ | E2E-11; tests/test_api/test_tool_description.py | Planned |
| FR-502 | Furniture remover ported from virtual-staging-app | M | SRS §7.2 | apps/tools | POST /api/v1/tools/furniture-remover/, GET /api/v1/streams/tools/<task_id>/ | E2E-13; tests/test_api/test_tool_furniture.py | Planned |
| FR-503 | All AI calls run async via Celery; views never call Gemini synchronously | M | SRS §7.3 | apps/tools | n/a (architectural) | tests/test_celery/test_tools_async.py; lint rule | Planned |
| FR-504 | ToolUsage ledger row per call with tokens, cost, status | M | SRS §7.4 | apps/tools, apps/audit | GET /api/v1/me/tools/usage/ | tests/test_models/test_tool_usage.py | Planned |
| FR-505 | Per-realtor and per-org rate limits on AI tools | M | SRS §7.5 | apps/tools | POST /api/v1/tools/* | E2E-14; tests/test_api/test_tool_rate_limit.py | Planned |
| FR-506 | Tool inputs scrubbed for PII and pre-moderation | M | SRS §7.6 | apps/moderation, apps/tools | n/a (pre-pipeline) | E2E-12; tests/test_moderation/test_tool_input_pii.py | Planned |
| FR-507 | Tool outputs post-moderated before persistence | M | SRS §7.7 | apps/moderation, apps/tools | n/a (post-pipeline) | tests/test_moderation/test_tool_output.py | Planned |
| FR-508 | Tool task progress streamed via SSE | S | SRS §7.8 | apps/tools | GET /api/v1/streams/tools/<task_id>/ | E2E-11, E2E-13; tests/test_api/test_tool_sse.py | Planned |

### 3.6 FR-6xx — Moderation

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-601 | Three-layer Gemini-Flash pipeline (filter → classify → policy) | M | SRS §8.1 / ADR-0003 | apps/moderation | n/a | tests/test_moderation/test_pipeline.py | Planned |
| FR-602 | injection_guard.parse_classifier_response fails closed on malformed JSON | M | SRS §8.2 | apps/moderation | n/a | tests/test_moderation/test_injection_guard.py | Planned |
| FR-603 | ModeratableMixin attached to every UGC model | M | SRS §8.3 | apps/moderation | n/a | tests/test_moderation/test_mixin_coverage.py | Planned |
| FR-604 | Adversarial fixture suite ≥ 5 new entries per phase | M | SRS §8.4 | apps/moderation | n/a | tests/test_moderation/test_adversarial.py | Planned |
| FR-605 | Pipeline never returns approve on attack fixtures (regression test) | M | SRS §8.5 | apps/moderation | n/a | tests/test_moderation/test_no_approve_attacks.py | Planned |
| FR-606 | Flag model (generic FK) for user-submitted reports | M | SRS §8.6 | apps/moderation | POST /api/v1/flags/ (Phase 4) | tests/test_api/test_flag.py | Planned |
| FR-607 | ModerationDecision log with action templates | M | SRS §8.7 | apps/moderation | POST /api/v1/mod/items/<id>/decision/ | E2E-15; tests/test_api/test_mod_decision.py | Planned |
| FR-608 | Moderator queue with SSE updates | M | SRS §8.8 | apps/moderation | GET /api/v1/streams/mod-queue/ | E2E-15, E2E-16; tests/test_api/test_mod_queue_sse.py | Planned |
| FR-609 | Escalation path Mod → Operator | M | SRS §8.9 | apps/moderation, apps/operations | POST /api/v1/mod/items/<id>/decision/ (action=escalate) | E2E-16; tests/test_api/test_mod_escalate.py | Planned |
| FR-610 | 451 `moderation-blocked` returned to users on hard reject | M | SRS §8.10 | apps/moderation | POST endpoints | E2E-07, E2E-12; tests/test_api/test_moderation_block.py | Planned |

### 3.7 FR-7xx — Control surfaces (Mod console + Operator + Admin)

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-701 | Moderator console page with keyboard shortcuts | M | SRS §9.1 | frontend/(mod)/, apps/moderation | GET /api/v1/streams/mod-queue/, POST /api/v1/mod/items/<id>/decision/ | E2E-15; tests/test_frontend/mod-console.test.tsx | Planned |
| FR-702 | Operator dashboard with throughput + accuracy metrics | M | SRS §9.2 | frontend/(ops)/, apps/operations | GET /api/v1/ops/stats/ (Phase 6) | E2E-18; tests/test_api/test_ops_stats.py | Planned |
| FR-703 | Operator can suspend users with reason + duration | M | SRS §9.3 | apps/operations | POST /api/v1/ops/users/<id>/suspend/ | E2E-17; tests/test_api/test_ops_suspend.py | Planned |
| FR-704 | All operator actions write ActionLog rows | M | SRS §9.4 | apps/audit, apps/operations | n/a (signals) | tests/test_signals/test_action_log_ops.py | Planned |
| FR-705 | Django admin behind 2FA + IP allowlist | M | SRS §9.5 | apps/admin_tools | n/a (middleware) | E2E-19; tests/test_admin/test_ip_allowlist.py | Planned |
| FR-706 | Staff writes (is_staff=True) auto-logged to ActionLog | M | SRS §9.6 | apps/audit | n/a (post_save signal) | E2E-20; tests/test_signals/test_staff_writes.py | Planned |
| FR-707 | AccessLog middleware records every request to /admin/ + /api/v1/ops/ | M | SRS §9.7 | apps/audit | n/a (middleware) | tests/test_audit/test_access_log.py | Planned |
| FR-708 | Audit append-only — no DELETE / UPDATE on ActionLog from app code | M | SRS §9.8 | apps/audit | n/a | tests/test_audit/test_append_only.py | Planned |
| FR-709 | Per-moderator stats (throughput, agree-rate with operator) | S | SRS §9.9 | apps/operations | GET /api/v1/ops/stats/?by=moderator | E2E-18; tests/test_api/test_ops_mod_stats.py | Planned |
| FR-710 | Suspended user UX — informative page, not silent 403 | S | SRS §9.10 | apps/accounts, frontend/(public)/suspended/ | n/a | E2E-17; tests/test_frontend/suspended.test.tsx | Planned |

### 3.8 FR-8xx — SEO & Social Integration

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| FR-801 | Sitemap.xml indexes posts, services, vendors, threads | M | SRS §10.1 | apps/core | GET /api/public/v1/sitemap.xml | tests/test_api/test_sitemap.py | Planned |
| FR-802 | robots.txt allows public, blocks /admin/ and /api/v1/ | M | SRS §10.2 | apps/core | GET /api/public/v1/robots.txt | tests/test_api/test_robots.py | Planned |
| FR-803 | Per-page canonical tags + OpenGraph + Twitter cards | M | SRS §10.3 | frontend/lib/seo/ | n/a | tests/test_frontend/seo.test.tsx; E2E-04 | Planned |
| FR-804 | YouTube/Instagram embeds with privacy-respecting iframe | S | SRS §10.4 (Phase 7) | apps/content | n/a | tests/test_frontend/embeds.test.tsx | Planned |
| FR-805 | JSON-LD structured data for posts and services | S | SRS §10.5 | frontend/lib/seo/ | n/a | tests/test_frontend/json_ld.test.tsx | Planned |

---

## 4. Non-Functional Requirements

### 4.1 NFR-1xx — Performance

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-101 | Lighthouse Performance ≥ 95 mobile / ≥ 98 desktop on 5 key pages | M | SRS §11.1 | frontend/, apps/core | GET /api/public/v1/* | E2E-21; Lighthouse CI | Planned |
| NFR-102 | LCP ≤ 2.0s mobile, INP ≤ 200ms, CLS ≤ 0.05 | M | SRS §11.2 | frontend/ | n/a | Lighthouse CI; web-vitals RUM | Planned |
| NFR-103 | API p95 latency ≤ 500ms under 350 RPS sustained | M | SRS §11.3 | All apps | All public + private | k6 baseline scenario | Planned |
| NFR-104 | First-load JS ≤ 180KB gzipped | M | SRS §11.4 | frontend/ | n/a | Lighthouse CI; bundle analyzer report in CI | Planned |
| NFR-105 | Public list endpoints cached SWR, served < 50ms cached | M | SRS §11.5 | apps/core (cache layer) | GET /api/public/v1/posts/, /services/, /vendors/ | tests/test_cache/test_public_list_cache.py; k6 | Planned |

### 4.2 NFR-2xx — Security

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-201 | TLS 1.2+ enforced via Caddy; HSTS 1y preload | M | SRS §12.1 | infra/Caddyfile | n/a | tests/test_infra/test_tls.py; ZAP | Planned |
| NFR-202 | CSP, X-Frame-Options, Referrer-Policy, COEP/COOP set | M | SRS §12.2 | apps/core, infra/Caddyfile | n/a (response headers) | tests/test_security/test_headers.py; ZAP | Planned |
| NFR-203 | CSRF double-submit cookie enforced on every mutation | M | SRS §12.3 | apps/core | All POST/PATCH/DELETE | E2E-30; tests/test_security/test_csrf.py | Planned |
| NFR-204 | JWT cookies httpOnly + SameSite=Strict + Secure | M | SRS §12.4 | apps/accounts | POST /api/v1/auth/* | tests/test_api/test_jwt_cookies.py | Planned |
| NFR-205 | Admin behind IP allowlist + 2FA | M | SRS §12.5 | apps/admin_tools | n/a | E2E-19; tests/test_admin/test_ip_allowlist.py | Planned |
| NFR-206 | Pre-merge: no high/critical bandit, npm audit, Trivy findings | M | SRS §12.6 | CI | n/a | bandit, npm audit, Trivy gates in CI | Planned |
| NFR-207 | OWASP ZAP weekly baseline + monthly authenticated scan | M | SRS §12.7 | staging | n/a | ZAP report in CI artifacts | Planned |
| NFR-208 | Manual pen test prior to launch | M | SRS §12.8 | external | n/a | Sprint 6 / pre-launch report | Planned |
| NFR-209 | Secrets only in env / Railway secrets, never committed | M | SRS §12.9 | repo | n/a | gitleaks pre-commit + CI scan | Planned |
| NFR-210 | Webhook signatures HMAC verified, fail closed | M | SRS §12.10 | apps/core | POST /api/v1/webhooks/* | tests/test_webhooks/test_signature.py | Planned |

### 4.3 NFR-3xx — Reliability

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-301 | Uptime ≥ 99.5% measured over rolling 30 days | M | SRS §13.1 | infra | GET /healthz/, /readyz/ | Better Stack monitor | Planned |
| NFR-302 | Daily Postgres logical backup + weekly restore drill | M | SRS §13.2 | infra | n/a | tests/test_ops/test_restore_drill.py; RUNBOOK | Planned |
| NFR-303 | Sentry captures unhandled errors with PII scrubbing | M | SRS §13.3 | apps/core | n/a | tests/test_observability/test_sentry_scrub.py | Planned |
| NFR-304 | Celery task failures visible + retried with exponential backoff | M | SRS §13.4 | config/celery.py | n/a | tests/test_celery/test_retry.py | Planned |

### 4.4 NFR-4xx — Maintainability

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-401 | Coverage gates met per app per MTP §6 | M | SRS §14.1 | All | n/a | pytest-cov + vitest coverage gates | Planned |
| NFR-402 | Lint clean (ruff, djlint, eslint, tsc --noEmit) | M | SRS §14.2 | All | n/a | CI lint job | Planned |
| NFR-403 | OpenAPI schema validated each build (`spectacular --validate --fail-on-warn`) | M | SRS §14.3 | apps/* | All | CI step | Planned |
| NFR-404 | ADRs documented for major decisions in `docs/adr/` | M | SRS §14.4 | docs/adr/ | n/a | manual review per PR | Planned |

### 4.5 NFR-5xx — Usability & Accessibility

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-501 | WCAG 2.2 AA compliance on every public page | M | SRS §15.1 | frontend/ | n/a | E2E-22, E2E-23, E2E-24; axe-playwright per spec | Planned |
| NFR-502 | Keyboard navigation supported on every interactive surface | M | SRS §15.2 | frontend/ | n/a | E2E-15, E2E-24; tests/test_frontend/keyboard.test.tsx | Planned |
| NFR-503 | prefers-reduced-motion honored across animations | M | SRS §15.3 | frontend/ Alpine x-reveal directives | n/a | E2E-23 | Planned |
| NFR-504 | Mobile breakpoints render without horizontal scroll at 320px+ | M | SRS §15.4 | frontend/ | n/a | E2E-22 | Planned |
| NFR-505 | Color contrast 4.5:1 normal, 3:1 large per WCAG | M | SRS §15.5 | frontend/, design tokens | n/a | axe-playwright; Storybook contrast addon | Planned |

### 4.6 NFR-6xx — Compatibility

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-601 | Latest stable Chromium, WebKit, Firefox supported | M | SRS §16.1 | frontend/ | n/a | Playwright projects matrix | Planned |
| NFR-602 | iOS 17+ Safari and Android Chrome 120+ supported | M | SRS §16.2 | frontend/ | n/a | Playwright iPhone 14, Pixel 5 emulators | Planned |
| NFR-603 | Graceful degradation for users with JS disabled (public pages remain readable) | S | SRS §16.3 | frontend/ Next.js SSR | n/a | tests/test_frontend/no-js.spec.ts | Planned |

### 4.7 NFR-7xx — Scalability

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-701 | Architecture supports 10K MAU baseline + 1K concurrent peak | M | SRS §17.1 | All | n/a | k6 peak burst scenario | Planned |
| NFR-702 | Stateless web layer; horizontal scale via Railway replicas | M | SRS §17.2 | infra | n/a | tests/test_infra/test_stateless.py | Planned |
| NFR-703 | Celery worker pool autoscaling on queue depth | S | SRS §17.3 | infra | n/a | k6 comment-moderation backlog scenario | Planned |

### 4.8 NFR-8xx — Compliance

| Req ID | Title | Priority | Source | SAD Component | ICD Endpoint(s) | Test Case(s) | Status |
|---|---|---|---|---|---|---|---|
| NFR-801 | GDPR-style data export on request | M | SRS §18.1 | apps/accounts | POST /api/v1/me/export/ (Phase 8) | tests/test_api/test_data_export.py | Planned |
| NFR-802 | Right to erasure implemented per FR-115 | M | SRS §18.2 | apps/accounts | POST /api/v1/me/delete/ | tests/test_api/test_account_delete.py | Planned |
| NFR-803 | Cookie banner with privacy-by-default (no non-essential cookies pre-set) | M | SRS §18.3 | frontend/ | n/a | E2E-01 (banner check); tests/test_frontend/cookie-banner.test.tsx | Planned |
| NFR-804 | Privacy policy + terms surfaced in footer of every page | M | SRS §18.4 | frontend/ | n/a | E2E-01; tests/test_frontend/footer.test.tsx | Planned |

---

## 5. Forward / Reverse Traceability

This RTM supports both directions:

- **Forward (Req → Test)**: each requirement row lists the test cases that verify it. A requirement with no Test Case entry is a gap and must be remediated before its phase exits.
- **Reverse (Test → Req)**: every E2E spec file in `frontend/tests/e2e/` and unit/integration test path in `apps/*/tests/` carries a leading docstring listing the FR/NFR IDs it covers. CI script `scripts/check_traceability.py` parses both directions and fails the build if drift is detected.

Drift sources to watch:

- New endpoint added to ICD without adding a row here.
- Test removed without flipping the requirement Status to Deferred.
- Requirement upgraded in priority without a fresh ADR.

---

## 6. Status Update Process

1. PR that ships a feature flips matching rows from `Planned` to `In progress` in the same diff.
2. PR that adds the test case + sees it pass green flips rows to `Verified`.
3. Phase audit (`gsd-audit-uat` skill) reads this file and confirms no rows for in-scope phases remain `Planned` at exit.
4. Quarterly review re-prioritises any `Could/Won't` items based on telemetry.

---

## 7. Cross-References

- SRS.md — canonical requirement definitions.
- SAD.md — component map.
- ICD.md — every endpoint referenced in the table.
- MTP.md — every test case referenced in the table.
- ACCESS-MATRIX.md — role permissions cross-checked against FR-1xx and FR-7xx.
