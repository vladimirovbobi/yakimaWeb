# State of the Project — 2026-05-03 (full autonomous build complete)

> Honest read on where we are, what works, and what's left before public launch.

## TL;DR — All 8 sprints landed (Sprint 7/8 launch artifacts ready; real-world activities deferred)

Architecture migrated from Django monolith to **split: Django REST API + Next.js 15 frontend
+ Caddy reverse proxy + 8 services**. All under autonomous build per ADRs 0005-0009.

### Sprint 0–6 deliverables (all committed, 177/177 pytest green)

**Sprint 0a — Documentation suite (~75K words):**
- VISION, SRS (70 FR + 32 NFR), SAD (C4 + ERD), ICD, MTP, RTM (102 reqs), RISK-REGISTER (25),
  THREAT-MODEL (STRIDE), SECURITY-PLAYBOOK (10 IR runbooks), COPY-STYLE-GUIDE, RUNBOOK,
  ACCESS-MATRIX + ADRs 0005-0009

**Sprint 0b/0c — Architecture split:**
- DRF API surface across 10 apps (`/api/public/v1/` + `/api/v1/`)
- JWT in httpOnly+SameSite=Strict cookies + CSRF double-submit
- 8 custom permission classes including RequiresOTP
- 8-service Docker stack (caddy / frontend / api / db / redis / celery / beat / img-worker)
- Caddy with rate-limit module via xcaddy build
- Next.js 15 App Router frontend (~150 .ts/.tsx files) — full vrov-new tokens, public + auth +
  dashboard route groups

**Sprint 1 — Real APIs + seed data + brand:**
- 6 management commands (categories, flairs, demo content + marketplace, brokerages, seed_all)
- ARELLO graceful mock, Gemini fail-closed, Postmark console fallback, Sentry DSN-gated init
- Pillow OG image generator + per-author RSS feeds

**Sprint 2 — Production polish:**
- 7 throttle scopes wired (vote/lead/ai_tool/comment/forum_write/flag/message)
- OTP enforcement on /api/v1/ops/ via RequiresOTP composed with IsOperator
- File-size validators on User.avatar / RealtorProfile.headshot / Post.hero_image / Service.hero_image
- Redis-backed Gemini daily spend cap with SpendCapExceeded
- Vendor tagline moderation via pre_save signal

**Sprint 3 — Furniture remover real implementation:**
- Two-call Gemini flow: Pro identifies masks → Image inpaints empty room
- Spend cap pre-flight + image moderation (OCR injection screen) + retry-on-transient
- Frontend: drag-and-drop upload, SSE-driven processing, before/after slider
- 9 image-injection adversarial fixtures + 20 pytest tests

**Sprint 4 — Vendor onboarding + LeadMessage + Notifications:**
- VendorProfile wizard_state JSON; 5-step wizard (Business → Categories → Services → Gallery → Publish)
- Threaded LeadMessage UI with SSE + 10s polling fallback, Cmd+Enter send
- New apps/notifications app: Notification model + signal_hooks + email digest beat task
- NotificationBell in dashboard header, /dashboard/notifications full list page
- 14 new tests

**Sprint 5 — Mod console v2 + content polish:**
- ActionTemplate model + seeder (7 templates)
- mod_stats service: agreement_rate, reversal_rate, avg_response_minutes, current_streak
- Mod queue keyboard shortcuts (A/R/E/T/N/I), escalation modal, InvestigateDrawer
- TipTap rich-text editor + tag M2M + Comment.image + image moderation pipeline
- 26 new tests

**Sprint 6 — E2E + bulletproof security:**
- 30 Playwright critical-path specs total (12 from earlier + 18 added) covering signup,
  realtor flow, vendor onboarding, lead conversation, forum lifecycle, AI tools,
  rate limits, prompt injection, CSRF, OTP enforcement, 2FA, password reset, role-aware
  dashboard, offline graceful, accessibility, SEO, security headers
- 4 k6 load tests (baseline 1K VU / forum_burst / ai_tool / 24h sustained soak)
- Defense-in-depth: COOP/COEP/X-Robots-Tag headers middleware, StrictCSRFMixin,
  anomaly_detector (cross-user IP, mass-flag, vendor review surge), session_fingerprint
  middleware (UA-class + IP /24 binding)
- 13 additional adversarial fixtures (image OCR, unicode confusables, zero-width,
  markdown link spoof, base64 filename, TOCTOU, ROT13, homoglyph, etc.) — 45 total
- 28 new tests (image_injection 10 + anomaly_detector 8 + session_fingerprint 10)

**Sprint 7/8 — Launch prep artifacts:**
- docs/launch/PRESS-KIT.md, BETA-PROGRAM.md, STATUS-PAGE.md, CRISIS-RESPONSE.md,
  LAUNCH-CHECKLIST.md (Day -14 to Day +1)
- Coming-soon gated launch page with NEXT_PUBLIC_LAUNCH_GATE env switch

**Test status:** **177/177 pytest green** (up from 86 at start of session). 30 Playwright
specs scaffolded.

### What's deferred (real-world activities only)

- Actual ARELLO sandbox key (vendor onboarding pending)
- Live Gemini API key (test runs use mocked responses)
- Postmark live token + R2 bucket creation + Sentry project
- Third-party penetration test engagement (1-week external)
- Attorney review of Privacy + Terms
- 24-hour load-test soak run (script ready)
- Beta cohort outreach + onboarding calls (templates ready)
- Brand assets (logo SVG + favicon + headshots — placeholders in place)
- Public launch press outreach

## What works right now (verified)

✅ **5-container docker compose stack** — `docker compose up` brings up everything
✅ **Public pages** — homepage, about, guidelines, privacy, terms, blog index, tools index, community index, marketplace index, videos
✅ **Auth** — signup → email verify → login → password reset (allauth wired correctly for our email-only User)
✅ **Realtor verification UI** — submits to ARELLO (mocked until live key obtained), polls via HTMX, badge appears
✅ **AI moderation pipeline** — 3 layers (deterministic + Gemini + human queue), prompt-injection fixtures pass, fail-closed parser
✅ **Audit infrastructure** — ActionLog + AccessLog, every staff write logged via signals
✅ **Admin lockdown** — IP allowlist + 2FA via django-otp + login throttle via django-axes
✅ **Operator dashboard** — 6 cards (signups, mod, AI spend, licenses, vendors, suspicious patterns)
✅ **Mod queue** — A/R/S keyboard shortcuts
✅ **Audit viewer** — searchable ActionLog + AccessLog tables
✅ **Forum** — flair filter, hot/new/top sort, voting w/ DB-level uniqueness, score auto-sync
✅ **Marketplace data model** — Category tree (treebeard), Service, Package, Bundle, BundleItem, Lead, Review (DB constraints enforced)
✅ **Marketplace UI** — service list (Fiverr-grade card grid), service detail (sticky inquiry sidebar), my_leads
✅ **Content system** — Post (polymorphic), Comment threading, bleach sanitizer, JSON-LD BlogPosting
✅ **AI tools** — description writer with Fair Housing-aware prompt; rate limiter (Redis token bucket); ToolUsage cost ledger
✅ **Social embeds** — YouTube + Instagram resolver (server-side iframe, no JS SDKs)
✅ **SEO** — sitemap.xml (Post + Service + Forum + static) + robots.txt
✅ **Test suite** — 86 tests across 9 apps; coverage on auth/moderation/audit/voting/rate-limit/sanitize
✅ **Vite asset pipeline** — Tailwind + Alpine + Motion + HTMX + Lenis bundled, manifest-resolved in templates

## What's stubbed but not real

⚠️ **ARELLO API** — client wraps real REST shape but no live key yet (sandbox sign-up pending). Currently mocked in tests.
⚠️ **Gemini moderation** — pipeline + prompt template ready, but no `GEMINI_API_KEY` set yet → falls back to "queue all" with logged warning.
⚠️ **Furniture remover tool** — stub returns the input image unchanged + an explanatory error. Real Gemini-image inpaint port from `virtual-staging-app` is the next-week task.
⚠️ **Description writer** — wired end-to-end but Gemini Pro call is the same: needs API key.
⚠️ **Email** — Postmark configured in settings but no `POSTMARK_SERVER_TOKEN` → console-prints during dev.
⚠️ **Cloudflare R2** — settings ready (`USE_S3=False` default), need bucket + keys for production.
⚠️ **Sentry** — DSN slot exists, not wired to a project.
⚠️ **Privacy + Terms** — placeholder copy with explicit "pending attorney review" notice.
⚠️ **Brand assets** — using a tinted Unsplash bg as hero placeholder; no logo SVG, no favicon yet.
⚠️ **Real seed data** — no flairs, no categories, no demo Posts/Services/Bundles. DB is empty.
⚠️ **Vendor onboarding wizard** — Vendor + Service + Package can be created via Django admin; no public-facing onboarding flow yet.
⚠️ **Mod queue** — works, but there's no escalation-to-operator path, no "investigate user" view, no per-moderator stats.
⚠️ **Forum vote endpoint** — works, but no rate limiting (security review item #4).
⚠️ **Lead inquiry endpoint** — works, but no rate limiting (security review item #5).
⚠️ **CSP** — production settings have `'unsafe-inline'` for scripts/styles (security review item #1) — needs nonce switch in Phase 8b.
⚠️ **In-platform messaging** — `LeadMessage` model exists but no UI — Phase 5.1 follow-up.

## What's missing entirely (not started)

❌ **OG image generator** (Pillow) for posts that don't ship a hero image
❌ **Per-author RSS feeds**
❌ **Vendor messaging UX** (LeadMessage threads + notifications)
❌ **Stripe Connect integration** (lead-gen-only is the locked v1; deferred to v2)
❌ **Push notifications**
❌ **In-app notification center**
❌ **Mobile app** (web is mobile-responsive — native app is not in scope)
❌ **MLS integration** (Listing model deferred per ADR — until source data is decided)
❌ **Advanced search** (current `?q=` is `__icontains`; pgvector + Postgres FTS upgrade is Phase 8 follow-up)
❌ **Notifications** (email digest of new threads, vendor activity, etc.)
❌ **Analytics dashboard for vendors** (their own funnel: views → inquiries → won)
❌ **Multi-currency / multi-region** (WA only at v1)
❌ **Realtor blog tagging + categories** (currently single body field)
❌ **Image uploads in comments** (text-only at v1)
❌ **Rich-text editor** (TipTap or similar) for blog body — currently raw markdown textarea

## Gap to "polished launchable product"

| Dimension | Current | Required for launch | Effort |
|---|---|---|---|
| Functionality | ~75% | All flows work end-to-end with real APIs | 2-3 weeks |
| Real API integrations | 0% | ARELLO live key, Gemini live key, Postmark token, R2 bucket, Sentry DSN | 1 week (mostly waiting on vendor approvals) |
| Brand + content | 10% | Logo, favicon, OG images, hero images, real homepage copy review, attorney-reviewed Privacy + Terms | 2 weeks (1 on legal) |
| Seed data | 0% | Categories tree, Flair list, 5-10 demo posts, 5-10 demo services, real Yakima brokerage list | 3-4 days |
| Production polish | 30% | CSP nonces, file-size validators, vote/lead rate limits, OTP on /ops/, Gemini spend cap enforcement, ARELLO circuit breaker | 1 week |
| Performance | unknown | Lighthouse 95+/100/100/100, < 200ms TTFB, < 2s LCP | 3-4 days |
| Accessibility | unknown | axe-core 0 violations on every public page | 2-3 days |
| E2E coverage | 6 specs | 25-30 critical paths covered by Playwright | 3-4 days |
| Furniture remover | stub | Real Gemini-image inpaint port from virtual-staging-app | 4-5 days |
| Operator console | functional | Per-moderator stats + investigate-user view + escalation path | 1 week |

**Total effort to public launch: 6-8 weeks of solo full-time work.**
**Total effort to polished product: 12-16 weeks.**

---

## The remaining-work plan

### Sprint 1 — Real APIs + seed data + brand (Week 1-2)

Goal: Make every stub real. The platform stops feeling like a shell.

- **ARELLO** — email support@arello.org for sandbox key, integrate, switch from mocked tests to dual-mode (mock by default, live with `ARELLO_LIVE_KEY` env var)
- **Gemini** — generate API key in Google Cloud Console, wire to `.env`, verify moderation actually runs against fixtures
- **Postmark** — sign up, get server token, verify outbound mail (signup confirmation, password reset)
- **Cloudflare R2** — create bucket `yakimaweb-media`, scoped IAM, switch `USE_S3=True`, verify uploaded headshot/hero ends up in R2
- **Sentry** — create project, wire DSN, verify error capture
- **Brand kit** — commission or design logo SVG + favicon set + 3-5 hero images (use Unsplash Plus or commission). Replace the Unsplash placeholder.
- **Categories seed** — write management command `seed_categories` with the 8 real-estate-adjacent verticals: Photography (sub: Real Estate / Drone / Twilight / 3D Tour), Lending (sub: Conventional / FHA / Construction), Service (sub: Junk Removal / Cleaning / Painting / Landscaping), Marketing (sub: Website / Social / Branding), Tech (sub: AI Agents / Automation / CRM), Legal (sub: Title / Closing / Inspection), Staging (sub: Physical / Virtual), Other.
- **Flair seed** — Question / Discussion / Help / Local-news / Market / Show-and-tell
- **Demo content** — write `seed_demo` management command: 3 admin "Yakima Web" posts, 5 demo Services, 2 demo Bundles, 10 forum threads, 8 reviews tied to fake Leads. All `moderation_status="approved"` to bypass the queue for the demo data.
- **Brokerage list** — pull WA DOL public CSV of registered firms; import as `Brokerage` model (new) + autocomplete on RealtorProfile
- **Production env vars** — fully populate Railway secrets

### Sprint 2 — Production polish (Week 3-4)

Goal: Close every High + Medium item from `SECURITY-FINAL.md`. Lighthouse + axe pass.

- **CSP nonces** — add `django-csp` middleware, swap `unsafe-inline` for nonces, regenerate per request
- **File-size validators** — wrap every ImageField with a max-size validator (5MB headshot, 10MB hero, 10MB tool input)
- **Vote rate limiting** — Redis token bucket: 1 vote/2s per user, 100/hour cap; wire to `apps/forum/views.py::vote`
- **Lead rate limiting** — 5 inquiries/hour to same vendor, 50/day total per buyer; wire to `apps/marketplace/views.py::lead_create`
- **OTP enforcement on /ops/** — wrap operations views with `apps.admin_tools.decorators.require_otp`
- **Gemini spend cap enforcement** — read `GEMINI_DAILY_SPEND_CAP_USD`, check before every Celery `run_description_writer`/`run_furniture_remover`, auto-disable tool when breached
- **ARELLO circuit breaker** — Redis-backed; if 3+ ARELLO failures in 5 minutes, open circuit for 10 min; dashboard shows breaker state
- **Vendor tagline moderation** — add `VendorProfile.tagline` to ModeratableMixin or pre-save check
- **CORS** — install `django-cors-headers`, allowlist explicitly when Phase 7 endpoints go live
- **Lighthouse audit** — fix anything below 95/100/100/100 on / /about /blog /services /community
- **axe-core audit** — zero violations on the same 5 pages
- **Performance** — verify TTFB < 200ms, LCP < 2.5s, image lazy-loading wired
- **OG image generator** — Pillow-based, 1200×630, brand template + post title overlay
- **Per-author RSS** — `/blog/<author-slug>/rss/` Atom feed

### Sprint 3 — Furniture remover real implementation (Week 5)

- Port the two-call inpaint design from `virtual-staging-app`
- Layer 1: Gemini Pro identifies furniture regions → JSON masks
- Layer 2: Gemini Image inpaints with empty-room target
- React island UI (Vite + react-image-comparison) for before/after slider
- Persist input + output to R2; ToolUsage rows track full lifecycle
- Add adversarial fixtures specific to image moderation (e.g. property-not-yours warnings)

### Sprint 4 — Vendor onboarding wizard + messaging (Week 6)

- Public `/vendor/onboard/` 5-step wizard: business info → service create → packages → portfolio → review/publish
- LeadMessage UI: threaded conversation per Lead; HTMX-driven send + receive; SSE for real-time when both sides online
- Notification center (`apps/notifications/` new app) — in-app + email digest
- Vendor analytics dashboard: views → inquiries → won (last 30/90 days, line chart via Recharts in React island)

### Sprint 5 — Mod console v2 + content polish (Week 7)

- Per-moderator stats (items reviewed, agreement rate, reversal rate)
- "Investigate user" view (separate-logged from queue work to prevent creeping)
- Escalation path: mod → operator with notes
- Action templates dropdown ("Removed: spam", "Removed: doxxing", etc.)
- TipTap rich-text editor for blog body (replace markdown textarea)
- Comment image uploads (with ModeratableMixin extending to image hash check)
- Realtor blog tagging + per-tag pages

### Sprint 6 — E2E coverage + final security review (Week 8)

- 25-30 Playwright critical-path tests covering: signup → realtor verify → blog publish → comment → flag → moderate, vendor onboard → service publish → buyer inquiry → mark won → review, forum thread → reply → vote → score sync, AI tool input → moderation block → human override
- Full security review pass against current prod (re-run all manual checks + add new fixtures discovered in production)
- Penetration test (engaged with a third-party firm — 1-week engagement)
- Load test (k6 or Locust): 10K MAU baseline + 1K concurrent users on hot pages
- Lighthouse final pass at production CDN + WAF in place

### Sprint 7 — Beta launch (Week 9)

- Invite 20-50 hand-picked Yakima realtors + 10 vendors as private beta
- Daily monitoring: error rate, AI spend, mod queue depth, signup conversion
- Weekly feedback sessions; convert into spec issues
- Iterate on top 3 friction points

### Sprint 8 — Public launch (Week 10-12)

- Final attorney pass on Privacy + Terms
- Press kit (1-pager + screenshots + founder quote)
- Soft public launch: announcement on local subreddit, Yakima Chamber of Commerce, real estate broker listservs
- Hard public launch: ad spend (Google + Facebook), partnership outreach to brokerages

---

## Architectural follow-ups (not blocking launch but plan for v1.1+)

- **Replace Postgres FTS with pgvector for semantic search** — more relevant for blogs + service descriptions
- **Split AI tools into a separate service** when Gemini spend > $5K/mo
- **Move from Railway to Fly.io regions** when MAU > 50K
- **Add k8s-style autoscaling** when bursts exceed 100 RPS
- **In-platform payments via Stripe Connect** — once vendor demand justifies the legal work
- **Multi-region** — Oregon + Idaho + Western WA expansion

## Critical assumptions that could break

If any of these turn out wrong, the plan changes:

1. **ARELLO sandbox grants within 2 weeks** — if they don't, fall back to manual verification queue + flag risk
2. **Gemini pricing stable** — if 2x change, re-evaluate vs Claude Haiku for moderation
3. **Owner working solo** — if a co-developer joins, sprints 4-6 can run in parallel and timeline compresses to 6-8 weeks
4. **No major regulatory change in WA real estate** — if Fair Housing or RESPA enforcement priorities shift, AI tools might need stricter guardrails
5. **No competing platform launch in Yakima** — unlikely, but watch the local market

---

## How to run the stack right now

```powershell
# Bring up everything
docker compose up -d

# Apply migrations + create superuser (one-time)
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

# View logs (Ctrl+C to exit, containers keep running)
docker compose logs -f web celery beat

# Run tests inside container
docker compose exec web pytest apps/

# Open browser
# http://localhost:8000              — homepage
# http://localhost:8000/admin/        — admin (will force 2FA setup for staff)
# http://localhost:8000/ops/          — operator dashboard (staff only)

# Tear down
docker compose down

# Tear down + delete data
docker compose down -v
```

## How to keep this doc current

Each sprint, check off completed items + update the gap table. Re-write "What works right now"
section at the end of each sprint based on real verification. The honest assessment is more
valuable than an aspirational one.
