# Remaining Work — what's left before "absolutely completed"

> Honest inventory of every gap. Audit date 2026-05-05. Sources cited inline.

## Status meaning

- `[WORKS]` fully shipped, tested, production-ready
- `[STUB]` scaffolded but core behavior is mocked / placeholder
- `[GAP]` not built at all
- `[BLOCKED]` waiting on external dependency (vendor key, attorney, brand work, founder ops)
- `[POLISH]` works but needs UX / visual / perf / test improvement

## TL;DR

**Total open items: 67** (10 hard blockers / 18 soft blockers / 22 medium / 11 low / 6 polish).

**Hard blockers for public launch (must close before saying "absolutely completed"):**

1. Real ARELLO API key + at least one live WA license verified end-to-end (`apps/accounts/services/arello.py:98` returns mocked record when key absent).
2. Real Gemini API key in production env + cost cap exercised against live spend (`apps/moderation/services/image_moderation.py:128` and `apps/tools/services/furniture_remover.py` both fall back to fail-closed without it).
3. Postmark live token + outbound deliverability test (signup verify, password reset, daily digest). `.env.example:39` ships empty; falls back to console.
4. Cloudflare R2 bucket created, IAM scoped, lifecycle rule set, `USE_S3=True` in prod, hero/avatar/portfolio uploads tested live.
5. Sentry project created, DSN wired, synthetic error captured (per LAUNCH-CHECKLIST Day -1).
6. Better Stack heartbeats + `status.yakimaweb.com` published (per `docs/launch/STATUS-PAGE.md`; today only documented, not deployed).
7. Attorney-reviewed Privacy + Terms (current `frontend/app/(public)/privacy/page.tsx` + `terms/page.tsx` are draft prose with no legal sign-off; `docs/launch/legal/` directory does not exist).
8. Third-party penetration test engaged + report received + Sev-1/2 closed (`docs/launch/LAUNCH-CHECKLIST.md` Day -14, not yet scheduled).
9. Real brand photography / logo (current logo.svg + 30-70 KB hero placeholders in `frontend/public/img/hero/` are Pillow-generated).
10. Domain `yakimaweb.com` registered + DNS pointing at Railway + production deploy. `.env.example:75` still defaults `DOMAIN=localhost`. No evidence of live deploy.

**Soft blockers (can launch without, but it feels incomplete):**

1. Realtor verify wizard UI (`/dashboard/realtor/verify` linked but missing — FEAT-015).
2. Realtor profile editor (`/dashboard/realtor/edit` linked but missing — FEAT-015).
3. Operator dashboard UI (`frontend/app/(dashboard)/ops/page.tsx` is `<ComingSoon>` — even though backend exists).
4. Mod queue depth wrong number bug (FEAT-014, deferred).
5. Reply tree never nests (FEAT-016).
6. Vendor public detail serializer missing 6 fields (FEAT-018).
7. Flyer-generator commercial backends (gemini, anthropic_api) both raise `FlyerGenerationError` — only `claude_cli` works (`apps/tools/services/flyer_generator/backends/gemini.py:35`).
8. Beta cohort outreach not done (templates ready in `docs/launch/BETA-PROGRAM.md`).
9. Press kit placeholders unfilled (`docs/launch/PRESS-KIT.md` Day -7 items).
10. Load-test results never captured (`load_tests/results/` directory does not exist).
11. Lighthouse 95+ + axe-core 0 not re-verified post-Sprint-2 (CLAUDE.md target unmet on record).
12. 24h k6 sustained soak not run.
13. Pen-test sign-off file `docs/launch/sign-off-day-1.md` does not exist.
14. RTM (`docs/RTM.md`) is 100% Planned / 0% Verified — never updated as features shipped.
15. 44 `test.skip` calls across 47 Playwright specs (only ~3 specs run unconditionally).
16. 3 pre-existing failing pytest tests on master (`apps/tools/tests/test_flyer_pdf.py` x2, `test_flyer_generator::test_backend_error_retries_then_fails`).
17. Notifications delivery is poll-only — no SSE for live in-app notifications (`apps/notifications/api/urls.py` has no stream endpoint).
18. CSP `'unsafe-inline'` still present on style-src (SEC-027 accepted-with-rationale, Sprint 9 tracked).

---

## 1. Lead magnets / AI tools

| Tool | Status | Evidence | Gap |
|---|---|---|---|
| Description writer | `[WORKS]` (when key present) | `apps/tools/services/description_writer.py`, frontend `frontend/components/tools/DescriptionWriterApp.tsx` | needs live `GEMINI_API_KEY` |
| Furniture remover | `[WORKS]` (when key present) | `apps/tools/services/furniture_remover.py` two-call Gemini Pro + Image | needs live key, never run against real listings |
| Image compressor | `[WORKS]` | Pillow-based, format-specific lossless. `apps/tools/services/image_compressor.py` | none |
| Flyer generator | `[STUB]` partly | `claude_cli` backend works for prototype only; `gemini.py` and `anthropic_api.py` both raise `FlyerGenerationError`; 3 failing tests on master | needs Gemini/Anthropic backend implementation; `RUNBOOK-flyer-keep-alive.md` documents fragile `~/.claude` mount |

No other AI tools advertised. CLAUDE.md mentions "AI lead magnets: furniture remover (port from virtual-staging-app), description writer" — both checked.

## 2. Marketplace

| Step | Status | Evidence |
|---|---|---|
| Vendor signup | `[WORKS]` | `apps/marketplace/api/views.py::VendorOnboardStepView` 5-step wizard backed by `wizard_state` JSON |
| Service publish (publish step materializes Service+Package rows) | `[WORKS]` | `_materialize_services()` at line 542 reads `wizard_state.data.services` and creates rows; idempotent on title |
| Vendor auto-approval | `[GAP]` by design | publish step leaves `status=DRAFT`, ops flips ACTIVE — no UI for ops to approve yet (backend endpoint exists; frontend `/dashboard/ops` is ComingSoon) |
| Lead inquiry create | `[WORKS]` | `/api/v1/leads/` |
| Lead messaging (threaded conversation) | `[WORKS]` | `LeadMessage` model + SSE stream `LeadMessageStreamView` + 10s polling fallback |
| Lead status flip via delivery webhook | `[WORKS]` | `apps/delivery/api/views.py::FinalizeWebhookView` post SEC-002 fix |
| Reviews on WON leads | `[WORKS]` | `/api/v1/leads/<id>/review/` |
| Vendor analytics dashboard | `[GAP]` | listed in STATE-OF-THE-PROJECT §"What's missing"; not built |
| Vendor public-detail serializer fields | `[GAP]` | `bio`, `hero_url`, `logo_url`, `is_verified`, `service_area`, `rating_count` missing (FEAT-018) |
| Featured services cross-promotion | `[WORKS]` | `apps/marketplace/services/featured.py` |
| Stripe Connect / in-platform payments | `[GAP]` deferred to v2 | locked per ADR-0004 |

## 3. Forum / community

| Feature | Status | Evidence |
|---|---|---|
| Thread CRUD + flair filter | `[WORKS]` | post-FEAT-001/002/003 fixes |
| Hot/new/top sort | `[WORKS]` | `_sort_threads` materialized list path fixed |
| Voting w/ DB-level uniqueness | `[WORKS]` | `apps/forum/models.py` UniqueConstraint |
| Reply tree (nested) | `[GAP]` | API returns flat replies w/ `parent` ids; `ReplyTree.tsx` iterates non-existent `replies` array (FEAT-016). Renders flat. |
| Mod queue + escalation | `[WORKS]` | `apps/moderation/api/views.py` + `Surface.INVESTIGATION` + per-mod stats |
| Comment image uploads | `[WORKS]` | `Comment.image` + image moderation pipeline |
| Investigate-user view | `[WORKS]` | `frontend/app/(dashboard)/mod/investigate/[user_id]/page.tsx` exists |
| Per-mod stats UI | `[WORKS]` | `frontend/app/(dashboard)/mod/stats` page exists |

## 4. Content / blog

| Feature | Status | Evidence |
|---|---|---|
| Polymorphic Post (yakimaweb / blog / landing) | `[WORKS]` | `apps/content/models.py` |
| Realtor authoring + TipTap rich editor | `[WORKS]` | `frontend/components/content/RichEditor.tsx`; `/dashboard/realtor/posts/[slug]/edit` route group |
| Threaded comments | `[WORKS]` | `apps/content/models.py::Comment` parent_id |
| Post tags M2M | `[WORKS]` | `apps/content/api/serializers.py::TagSerializer` (with N+1 micro-opt deferred — DEB-010) |
| Per-author RSS feed | `[WORKS]` | `apps/content/views_rss.py` |
| Pillow OG image generator | `[WORKS]` | `apps/content/services/og_image.py` (TODO Phase 2.1: brand fonts — currently uses fallback) |
| Newsletter confirmation email | `[GAP]` | `apps/content/api/views.py:160` `# TODO(phase-7): trigger Celery task to send confirmation email` |
| Postgres FTS search (`?q=`) | `[WORKS]` | tsvector column |
| Semantic search (pgvector) | `[GAP]` deferred to v1.1 | per ADR-0009 — schema exists, embeddings NULL, no Celery embed task, no search endpoint |

## 5. Auth / accounts

| Feature | Status | Evidence |
|---|---|---|
| Email signup + verify | `[WORKS]` | `apps/accounts/api/views.py::SignupView` post-SEC-007 fix |
| Login + JWT in httpOnly cookies | `[WORKS]` | post-ADR-0008 |
| Password reset flow | `[WORKS]` backend; `[GAP]` frontend `/forgot-password` + `/reset-password` pages still trigger `test.skip` in `password-reset-flow.spec.ts:48,66` |
| 2FA TOTP setup | `[WORKS]` UI exists at `/2fa/setup` (TotpVerifyForm.tsx); `2fa-enrollment.spec.ts:53` still skips ("/2fa/setup not built" comment is stale, but spec is) |
| ARELLO license verify | `[STUB]` | `arello.py:98` mocked when no key; never run against live ARELLO |
| Realtor profile editor | `[GAP]` | `/dashboard/realtor/edit` linked from `realtor/page.tsx:88,106`, no page (FEAT-015) |
| Realtor verify wizard | `[GAP]` | `/dashboard/realtor/verify` linked, no page (FEAT-015) |
| Account deletion | `[GAP]` | `FR-115` Phase 8; never built |

## 6. Moderation pipeline

| Layer | Status | Evidence |
|---|---|---|
| Layer 1 deterministic (regex + bleach) | `[WORKS]` | `apps/moderation/services/deterministic.py` |
| Layer 2 Gemini classifier | `[STUB]` (when no key) → `[WORKS]` (with key) | `apps/moderation/services/ai_classifier.py`, `injection_guard.parse_classifier_response` fail-closed |
| Layer 3 human queue | `[WORKS]` | `frontend/components/mod/QueueWorkstation.tsx` post-SEC-008 |
| Image OCR | `[WORKS]` | `apps/moderation/services/image_ocr.py` |
| Image vision moderation (Gemini Pro) | `[WORKS]` (with key) | `image_moderation.py:139-152` real `client.models.generate_content` call |
| Spend cap (daily $) | `[WORKS]` | `apps/tools/services/spend_cap.py` Redis-backed; never exercised against real spend |
| Adversarial fixtures | `[WORKS]` | 62 in `apps/moderation/tests/fixtures/prompt_injection_attacks.json` |

## 7. Notifications

| Feature | Status | Evidence |
|---|---|---|
| `Notification` model + signal hooks | `[WORKS]` | `apps/notifications/models.py` + `signal_hooks.py` |
| In-app feed list + read/unread | `[WORKS]` | `/api/v1/me/notifications/` |
| Notification bell in dashboard header | `[WORKS]` | mentioned in STATE-OF-THE-PROJECT §"Final integration polish" |
| Email digest (daily 09:00 PT) | `[WORKS]` (no key) | `apps/notifications/tasks.py::deliver_email_digest` registered in `config/celery.py:23-26`; falls to console without Postmark token; per-user errors silently swallowed (DEB-012, deferred) |
| Live SSE notification stream | `[GAP]` | no stream view in `apps/notifications/api/urls.py`; client polls only |
| Push notifications (web push / native) | `[GAP]` | listed in STATE-OF-THE-PROJECT §"Not started" |

## 8. Delivery service

| Feature | Status | Evidence |
|---|---|---|
| FastAPI sidecar on :8001 | `[WORKS]` | `delivery/main.py`, 6 endpoints |
| Magic-byte content sniff + size caps | `[WORKS]` | `delivery/storage.py` (per docs) |
| JWT verify against Django SECRET_KEY w/ role claims | `[WORKS]` | post-SEC-003 fix |
| HMAC-signed webhook back to Django (Lead → WON) | `[WORKS]` | post-SEC-002 fix |
| Signed download URLs (5 min TTL) | `[WORKS]` | per ADR-0010 |
| Playwright e2e | `[STUB]` | `delivery-service.spec.ts:9,24` skip when delivery not exposed publicly |

## 9. Audit + ops

| Feature | Status | Evidence |
|---|---|---|
| `ActionLog` + `AccessLog` (append-only) | `[WORKS]` | `apps/audit/models.py` |
| Auto-log staff writes via signals | `[WORKS]` | `apps/audit/signals.py` |
| Anomaly detector (cross-user IP, mass-flag, vendor review surge) | `[WORKS]` (registered but never observed firing) | `apps/audit/services/anomaly_detector.py`, beat-scheduled `crontab(minute=15)` in `config/celery.py:31` |
| Operator dashboard 6 cards | `[WORKS]` backend; `[STUB]` frontend (`ops/page.tsx` = ComingSoon) |
| Per-mod stats | `[WORKS]` | `apps/moderation/services/mod_stats.py` |
| Investigate-user view | `[WORKS]` | `frontend/app/(dashboard)/mod/investigate/[user_id]/page.tsx` |
| Operations API: cards, suspend, vendor status, takedown | `[WORKS]` | backend present in `apps/operations/api/views.py`; `# TODO: build apps.operations.tasks.reenable_user` at line 289 |

## 10. BFF / network obscuration

`frontend/lib/bff/routes.ts` declares **14** entries (CLAUDE.md says "15-entry manifest" — slight drift). Per-entry status: all 14 map to existing backend routes. Verified live in `docs/FEATURE-AUDIT-2026-05-05.md` Verification log.

| ID | Status |
|---|---|
| lead-c0nnect, lead-msg-snd, lead-status, rev-write | `[WORKS]` |
| forum-vote, forum-rply, forum-thrd | `[WORKS]` |
| cmt-write, cont-flag | `[WORKS]` |
| tool-desc, tool-furn, tool-cmpr | `[WORKS]` (Gemini-dependent) |
| me-update, newsltr-sub | `[WORKS]` |
| Upstream-host pin assertion (SEC-013) | `[WORKS]` |
| Path-traversal reject (SEC-009) | `[WORKS]` |

## 11. Infrastructure

| Component | Status | Evidence |
|---|---|---|
| 8-service Docker stack (caddy/frontend/api/db/redis/celery/beat/img-worker) — CLAUDE.md says 8 | `[WORKS]` locally | per STATE-OF-THE-PROJECT |
| 9-service stack incl. delivery FastAPI | `[WORKS]` | `delivery/` — but only 8 in CLAUDE.md table; minor drift |
| Caddy edge headers + rate limit module via xcaddy | `[WORKS]` | `caddy/Caddyfile`, ADR-0007 |
| Postgres 16 + pgvector extension | `[WORKS]` | `pgvector/pgvector:pg16` image per ADR-0009 |
| Redis published on host for dev parity | `[WORKS]` | per recent commit `2748615 fix(infra)` |
| Production deploy to Railway | `[GAP]` | nothing on record; CRISIS-RESPONSE.md still references "the standby Fly.io deployment" as a fallback that doesn't exist either |
| DNS + domain | `[GAP]` | `.env.example:75 DOMAIN=localhost` |
| Production env vars populated in Railway secrets | `[GAP]` | implied by all the missing keys |

## 12. External integrations (mostly BLOCKED)

| Vendor | Status | Required action |
|---|---|---|
| ARELLO | `[BLOCKED]` | request sandbox key; verify one live WA broker |
| Gemini | `[BLOCKED]` | enable billing in GCP, set `GEMINI_API_KEY`, observe spend-cap fire |
| Postmark | `[BLOCKED]` | sign up, set `POSTMARK_SERVER_TOKEN`, send test message |
| Cloudflare R2 | `[BLOCKED]` | create bucket, IAM, lifecycle, set 4 AWS_* env vars, flip `USE_S3=True` |
| Sentry | `[BLOCKED]` | create project, set `SENTRY_DSN`, capture synthetic error |
| Better Stack | `[BLOCKED]` | create heartbeats, publish status.yakimaweb.com (CNAME), test alert chain |
| Anthropic API | `[BLOCKED]` (optional) | only required if switching flyer-generator off `claude_cli` |

## 13. Documentation

| Doc | Status | Note |
|---|---|---|
| VISION-AND-SCOPE / SRS / SAD / ICD | `[WORKS]` | Sprint 0a deliverables |
| MTP | `[POLISH]` | scenarios written; many specs skip (see §14) |
| RTM | `[STUB]` | 102 reqs all `Status: Planned` — never advanced. Lying about coverage. |
| RISK-REGISTER | `[WORKS]` | 25 risks |
| THREAT-MODEL | `[WORKS]` | STRIDE matrix matches 2026-05-05 audit |
| SECURITY-PLAYBOOK | `[WORKS]` | 10 IR runbooks |
| RUNBOOK + RUNBOOK-flyer-keep-alive | `[WORKS]` | flyer keep-alive is fragile by design |
| LAUNCH-CHECKLIST | `[POLISH]` | every Day -14 to Day +1 box still unchecked |
| STATE-OF-THE-PROJECT | `[WORKS]` | this is the load-bearing doc, kept current |

## 14. Tests

- pytest: **264 passed, 3 failed** on master (`apps/tools/tests/test_flyer_pdf.py` x2 + `test_flyer_generator::test_backend_error_retries_then_fails`). Pre-existing per docs.
- Coverage gates: CLAUDE.md mandates ≥ 80% on `apps/accounts`, `apps/moderation`, `apps/audit` — not measured/published in any artifact.
- Playwright: 47 spec files; **44 `test.skip` calls**. Most specs gate on UI features not yet implemented (vendor wizard, 2FA setup, password reset pages, comment form, vote control, seed data).
- Vitest: present (`frontend/tests/unit/bff-host-pin.test.ts` post-SEC-013); coverage not measured.
- k6: 4 scripts present; **`load_tests/results/` directory does not exist** — never executed.

## 15. Performance / accessibility

- Lighthouse target ≥95 across home/blog/services/community/about — last measurement was deferred in Sprint 1 verification ("needs running dev stack"). No published number.
- axe-core 0 violations — same. Documented as deferred. `accessibility.spec.ts:31,59` skip cases for skip-to-main link absence + reduced-motion preference branch.
- TTFB / LCP targets — never measured.

## 16. Launch artifacts (Sprint 7/8)

| Artifact | Status | Evidence |
|---|---|---|
| Press kit | `[STUB]` | `docs/launch/PRESS-KIT.md` exists w/ placeholders, founder quote not filled, no signed PDF in `docs/launch/assets/` |
| Beta program plan | `[STUB]` | `docs/launch/BETA-PROGRAM.md` exists, no invite list compiled, no onboarding calls happened |
| Status page | `[STUB]` | `docs/launch/STATUS-PAGE.md` defines components — Better Stack property not provisioned |
| Crisis response runbook | `[WORKS]` | `docs/launch/CRISIS-RESPONSE.md` — references CNAMEs/dashboards that aren't wired |
| Launch checklist | `[GAP]` execution | every Day -14 → +1 box unchecked |
| Attorney review of Privacy/Terms | `[BLOCKED]` | `docs/launch/legal/` directory does not exist |
| Real photographer assets | `[BLOCKED]` | hero JPGs are 30-70 KB Pillow placeholders |
| Real logo | `[BLOCKED]` | logo.svg is generated, not designer-stamped |
| Domain registration | `[BLOCKED]` | `yakimaweb.com` not wired |
| Railway / Fly deploy | `[GAP]` | nothing on record |
| Pen-test report | `[BLOCKED]` | not engaged |
| 24h soak | `[GAP]` | k6 script ready, no run results |
| Press outreach | `[GAP]` | not started |

## 17. Mobile + browser support

Per `feat(mobile): comprehensive mobile-friendly audit + PWA manifest` (commit `6f51679`):

- PWA manifest, safe-area insets, role-aware bottom nav, 44×44 touch targets, hover-only effects disabled on touch, 16 px input minimum, sheet-mobile pattern, scroll-strip momentum.
- `[POLISH]` `mobile-comprehensive.spec.ts:64`, `mobile-navigation.spec.ts:9`, `pwa-offline-graceful.spec.ts:13` skip when bottom nav absent / offline shell missing.

## 18. Future-proofing (v1.1+ explicitly deferred)

| Item | Status |
|---|---|
| pgvector activation (Celery embed task + cosine search endpoint) | `[GAP]` ADR-0009 |
| Stripe Connect | `[GAP]` ADR-0004 |
| MLS integration | `[GAP]` deferred per Listing model decision |
| Multi-region (Oregon/Idaho/Western WA) | `[GAP]` |
| Native mobile app | `[GAP]` |
| Vendor analytics dashboard | `[GAP]` |
| Multi-currency | `[GAP]` |

---

## Path to "absolutely completed"

### Done already

The 8 sprints — auth, ARELLO client, content + comments + tags + RSS, forum + voting, marketplace + lead conversation + reviews, AI tools (3 of 4), moderation 3-layer + image vision + adversarial fixtures, audit + anomaly detector, BFF obscuration, delivery sidecar, mobile audit, PWA, brand placeholders, 8-service docker stack, Caddy edge, Sprint 1 SEO, Sprint 2 polish (CSP / rate limits / OTP / spend cap), Sprint 6 e2e + 4 k6 scripts, Sprint 7/8 launch doc artifacts, full doc suite (~75K words). All committed. **208/208 pytest green** (excluding 3 pre-existing flyer failures).

### Quick wins (≤4h each)

1. Fix RTM — sweep `Planned → Verified` for the 70+ FRs that are actually shipped.
2. Add `Cache-Control: public` + `Vary` to public REST list endpoints (DEB-011).
3. Drop `post_count` from inline tag serializer (DEB-010).
4. `log.exception(...)` in `deliver_email_digest` per-user error path (DEB-012).
5. Move `django_extensions` cleanup verification (already done; just confirm).
6. Add `apps.delivery` + `apps.notifications` to `[tool.setuptools].packages` in `pyproject.toml` (DEB-004).
7. Fix the 3 failing flyer tests on master.
8. Update CLAUDE.md "8 services" → "9 services" (delivery counted).
9. Fix BFF route count drift (14 vs documented 15).
10. Strip `'unsafe-inline'` from style-src CSP (Sprint 9 hardening / SEC-027).
11. Add `Notification` SSE stream endpoint (parity with leads + mod queue).
12. Add `loading.tsx` for tools landing if any data fetch lands there.
13. Wire `IsLeadParty.is_active` check (SEC-016).
14. SSE auth re-check loop (SEC-019).
15. Caddy log format console + level filter for prod (DEB-014).

Estimated total: **30-45 hours**.

### Real engineering (>1 day each)

1. Realtor verify wizard UI (`/dashboard/realtor/verify`) + edit page (FEAT-015) — ~3 days.
2. Operator dashboard UI (replace `ops/page.tsx` ComingSoon with 6-card grid + suspend/takedown actions) — ~3-4 days.
3. Vendor public detail expansion (`bio`, `hero_url`, `logo_url`, `is_verified`, `service_area`, `rating_count` migrations + serializer + R2 upload UI) — ~2 days (FEAT-018).
4. Reply tree nesting (server-side tree assembler in replies serializer) — ~1 day (FEAT-016).
5. Mod queue depth count endpoint (FEAT-014) — ~0.5 day.
6. Newsletter confirmation email Celery task (`apps/content/api/views.py:160` TODO) — ~0.5 day.
7. Account deletion w/ 30-day grace (FR-115) — ~2 days.
8. Replace 44 `test.skip` with real specs that exercise the now-shipped UI — ~3-5 days.
9. Lighthouse + axe-core audit pass + remediation — ~2-3 days.
10. k6: run 4 scripts against staging, capture results, fix bottlenecks — ~2 days.
11. 24h sustained soak — 1 calendar day + analysis.
12. Flyer-generator Gemini backend implementation (replace `gemini.py:35` raise) — ~1 day.
13. Vendor analytics dashboard — ~2-3 days.

Estimated total: **20-30 days of engineering**.

### External-blocked (waiting on vendors / legal / brand / ops)

- ARELLO sandbox grant — calendar wait 1-2 weeks.
- Postmark token — same-day after signup.
- R2 bucket setup — 1 hour.
- Sentry project — 1 hour.
- Better Stack — 2 hours.
- Domain registration + DNS — 1 day.
- Railway production deploy — 1-2 days for first pass.
- Attorney review of Privacy + Terms — 1-2 weeks of attorney time.
- Brand photography commission — 2-4 weeks (or buy Unsplash Plus for 1 day).
- Logo design — 1-2 weeks.
- Pen-test engagement — 1 week active + 1 week report.
- Beta cohort outreach + onboarding calls — 2-3 weeks.
- Press outreach — 1 week prep + ongoing.

---

## Definition of "absolutely completed"

The user said "all features, lead magnets and everything yet to be finished." This list is the bar:

- [ ] All 4 hard blockers vendor-key items live (ARELLO, Gemini, Postmark, R2) and exercised against real data.
- [ ] Sentry + Better Stack live; status page published; one synthetic error captured end-to-end.
- [ ] Privacy + Terms attorney-reviewed and committed under `docs/launch/legal/`.
- [ ] Brand assets are real (logo + ≥5 hero photos + 6 furniture-remover demos + favicon set).
- [ ] `yakimaweb.com` registered, DNS pointed at Railway, production deploy green.
- [ ] Realtor verify wizard + realtor edit page shipped (close FEAT-015).
- [ ] Operator dashboard UI shipped (replace ComingSoon).
- [ ] Vendor detail serializer + UI fields complete (close FEAT-018).
- [ ] Reply tree nests (close FEAT-016).
- [ ] Newsletter confirmation email task wired.
- [ ] Account deletion shipped (close FR-115).
- [ ] Flyer-generator Gemini backend works end-to-end (replace `claude_cli`).
- [ ] Notification SSE stream live.
- [ ] All 4 k6 scripts run against staging; results in `load_tests/results/`.
- [ ] 24h soak completed without OOM; results committed.
- [ ] Lighthouse ≥ 95 on / /blog /services /community /about.
- [ ] axe-core 0 violations on the same 5 pages.
- [ ] Pen-test Sev-1 + Sev-2 closed; report committed; sign-off file exists.
- [ ] 44 `test.skip` count reduced to ≤ 5 (only legitimate skips for env-conditional cases).
- [ ] 3 failing flyer pytest tests green.
- [ ] RTM 100% Verified rows for shipped FRs.
- [ ] LAUNCH-CHECKLIST Day -14 → +1 fully checked.
- [ ] Beta cohort live; ≥10 verified realtors + ≥5 vendors signed up.
- [ ] Press kit signed; ≥3 local-press emails sent.
- [ ] CLAUDE.md "Phase status" rows for Sprint 7 + Sprint 8 flipped to "done".

When every box is checked, the project is "absolutely completed."
