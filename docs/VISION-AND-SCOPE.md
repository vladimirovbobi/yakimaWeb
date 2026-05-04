# Vision & Scope — Yakima Real Estate Hub

| Field | Value |
|---|---|
| Document | Vision & Scope (RFP-equivalent, internal product) |
| Version | 1.0 |
| Date | 2026-05-03 |
| Owner | Yakima Real Estate Hub Engineering |
| Status | Approved for Phase 2+ execution |
| Related | `docs/SRS.md`, `docs/SAD.md`, `docs/STATE-OF-THE-PROJECT.md`, `docs/adr/0001`–`0009` |

---

## 1. Problem Statement

Central Washington's real-estate market — anchored by Yakima County (~250K residents), Kittitas County, and the Tri-Cities corridor — is digitally underserved relative to Seattle, Spokane, or Boise. Five concrete pain points motivate this platform:

1. **Broker-site fragmentation.** Each brokerage publishes content on its own siloed Wix/Squarespace/WordPress site. Search engines see thin, duplicated copy. Buyers comparing listings must hop between 6–10 broker sites with inconsistent UX. There is no neutral aggregator that ranks for "[neighborhood] real estate."
2. **Vendor discovery is broken.** A realtor preparing a listing needs a photographer, a stager, a 3D-tour operator, a junk-removal crew, sometimes a lender introduction. Today they ask in WhatsApp groups or Facebook. Results are unverified, prices are opaque, and the same five names recycle. Out-of-network vendors with strong work cannot break in.
3. **No professional community for local realtors.** WA realtors have CE requirements, license-renewal rhythms, market-specific tactics, and zero locally-rooted forum to discuss them. National platforms (BiggerPockets, Inman) over-index on coastal markets and ignore the agricultural/exurban dynamics that define Central WA.
4. **AI tooling has not been adapted to the local market.** Generic AI listing-description tools produce coastal-style copy that misses Central WA buyers' actual concerns (irrigation rights, hop-yard adjacency, school-district lines around Selah/West Valley, propane vs. natural-gas heating). Furniture-removal/virtual-staging products charge per-image fees that price-out exurban listings under $400K.
5. **No trust layer.** No platform verifies that the person publishing a "realtor blog post" actually holds an active WA real-estate license. ARELLO data is public but no consumer-facing surface uses it. Bad-faith content (steering, dual-agency violations, fair-housing-adjacent language) circulates unchecked because moderation requires structure that a Facebook group cannot provide.

The opportunity: a single, locally-rooted hub that solves discovery, community, tooling, and trust together. None of the four pieces stands alone — discovery without community drives away professionals, community without trust attracts spam, tooling without distribution gets ignored.

## 2. Vision

Yakima Real Estate Hub is the trusted digital town square for Central Washington real estate — the place a verified local realtor publishes their market take, a homeowner finds a vetted photographer in three clicks, a buyer reads neighborhood-level guides, and an operator runs the whole community with a moderator console that catches problems before they reach the public feed. The platform is opinionated about quality (gold-and-dark editorial aesthetic, Cormorant headings, no engagement-bait), opinionated about safety (every UGC pipe behind a 3-layer moderation pipeline), and opinionated about scope (lead-gen marketplace, never payment middleman). At 10,000 monthly active users it should feel like a curated publication; at 100,000 it should still feel like one, because the systems that earn that trust are designed in from sprint one.

## 3. Target Users

### Persona A — Local Realtor ("Maria")

- **Profile.** 38, licensed WA real-estate broker since 2014, works the Selah/Yakima/Naches corridor, ~24 closings/year, GCI ~$280K. Maintains a personal Instagram (~3K followers) and a stale Wix site.
- **Motivations.** Build a credible online presence that ranks for her name + neighborhood. Find a photographer/stager fast. Read what other local realtors are seeing on the ground. Differentiate from the 800+ other licensed agents in the county.
- **Frustrations.** Wix site is invisible to Google. Vendor referrals are word-of-mouth. National platforms feel like marketing-junk. ARELLO verification is a lookup nobody surfaces; she has no way to *prove* her license to the public other than a hand-typed footer.
- **Success criteria.** Verified-realtor badge live within 7 days of signup. Publishes 1+ blog post in the first 30 days. Gets 3+ inbound vendor or buyer leads within 90 days. Returns weekly.
- **Anti-persona.** Out-of-state agents farming for referrals. Unlicensed "real-estate coaches." Wholesalers using realtor language without holding the license.

### Persona B — Service Vendor ("Diego")

- **Profile.** 31, runs Diego Photo, two-person real-estate-photo crew based in Yakima. Shoots ~12 listings/month at $295 starter, $495 with drone, $895 with 3D tour. Lives off Facebook referrals and a thin Squarespace.
- **Motivations.** Predictable lead flow that does not depend on Facebook's algorithm. A neutral surface that displays his portfolio, his packages, his turnaround time, his radius. A ranking signal that rewards quality (reviews, on-time delivery, dispute-free history) rather than ad spend.
- **Frustrations.** No platform exists that is local + real-estate-specific. Fiverr/Thumbtack are too generic; Houzz is interior-design-skewed. He wants leads, not a Stripe Connect middleman taking 15%.
- **Success criteria.** Profile live in <1 hour from signup. ≥5 inquiries/month within 60 days. Reviews accumulate organically. Bundle pricing (photo + drone + 3D) discoverable in one click.
- **Anti-persona.** Out-of-region vendors (>120 miles). Vendors offering services unrelated to real-estate transaction flow (e.g., generic web design, MLM). Vendors who refuse identity verification.

### Persona C — Home Buyer / Seller ("Linh & Marcus")

- **Profile.** Couple, mid-30s, dual-income, relocating from Seattle to Yakima for cost of living. Researching neighborhoods, school districts, irrigation-rights nuance on lots they're considering, and looking for a buyer's agent.
- **Motivations.** Understand the market without reading 50 broker-site blog posts. Find a realtor whose published content matches their style. Read forum threads on neighborhood-level questions ("How is the West Valley school district really?"). Compare a listing's photography quality before committing.
- **Frustrations.** Zillow/Redfin tell them nothing about *the people*. Facebook groups are noisy and unverified. They cannot tell which content is from a real local agent vs. a national content farm.
- **Success criteria.** Find 3+ neighborhood guides on first visit. Identify a candidate realtor (from blog content) within 2 sessions. Submit one buyer-side lead inquiry. Bookmark 5+ posts.
- **Anti-persona.** Investors hunting wholesale deals. Out-of-state buyers without specific Central WA intent. Bots scraping listing data.

### Persona D — Platform Operator ("Vladi")

- **Profile.** Solo founder/operator (initially), eventually a 2–3 person ops/mod team. Background in marketing automation. Owns mod-queue throughput, vendor onboarding quality, and platform-health metrics.
- **Motivations.** Run the platform with a small team. Catch fair-housing or RESPA-adjacent content before it reaches the feed. See, in one dashboard, "is the moderation pipeline keeping up?", "which vendors are being flagged?", "where is AI spend going?"
- **Frustrations.** Most CMS admin UIs are bottomless. Most moderation tools are bolted-on and require swivel-chairing between 4 SaaS dashboards. Most analytics products surface engagement, not safety.
- **Success criteria.** Mod-queue median resolution time <4 hours. Vendor onboarding takes <15 minutes including ARELLO/identity check. Operator dashboard surfaces every safety/spend/health metric without leaving Postgres. AI moderation cost <$80/mo at 10K MAU.
- **Anti-persona.** Operators who want a generic Wagtail/WordPress instance with bolt-on plugins. Operators uncomfortable with command-line and Docker.

## 4. In-Scope (v1, public launch)

| # | Surface | Rationale |
|---|---|---|
| 1 | Yakima Web posts (org-authored articles) | Anchor content, owns SEO for "Yakima real estate news/guides" |
| 2 | Realtor blogs (license-gated authoring) | Core trust differentiator; ARELLO verification gates publish |
| 3 | Comments under posts (auth-gated UGC) | Discussion attached to content; first UGC pipe through ModeratableMixin |
| 4 | Forum (Reddit-style: threads, replies, votes, flair) | Community surface; public read, auth write |
| 5 | Marketplace (lead-gen, no payments) | Vendor discovery; profile, services, packages, bundles, lead inquiries, reviews |
| 6 | AI lead magnets (description writer, furniture remover) | Top-of-funnel; drives signups; ported from `virtual-staging-app` |
| 7 | Three control surfaces (Django admin / mod console / operator dashboard) | Lets a 1–3 person team run the platform |
| 8 | 3-layer AI moderation pipeline | Safety contract #1; deterministic + Gemini classifier + human queue |
| 9 | Audit trail (ActionLog + AccessLog) | Safety contract #3; staff-action tamper-evidence |
| 10 | Auth (email + 2FA for staff, JWT cookies, allauth + django-otp + django-axes) | Replaces session auth from ADR-0001; see ADR-0005 |
| 11 | Email transactional (Postmark) | Verification, password reset, lead-inquiry notifications |
| 12 | SEO + social embeds (sitemap, robots, JSON-LD, OG, RSS) | Distribution; ties content surface to acquisition |
| 13 | Design system (vrov-new tokens) | Quality bar; gold-on-dark editorial palette |
| 14 | Public REST + read-only GraphQL | Frontend (Next.js) consumes both; future-proofs partner integration |

## 5. Out-of-Scope (v1)

- **MLS integration / IDX.** Costs $5K+/month, requires brokerage sponsorship, regulatory complexity. Defer to v2 once a sponsoring broker is on board.
- **In-platform payments / Stripe Connect / escrow.** Marketplace is lead-gen only. Payment middleman creates 1099-K reporting, dispute handling, PCI scope, and changes liability profile materially. v2 evaluation only.
- **Multi-region.** Central WA only at launch. URL routing, SEO, and content taxonomy assume single-market.
- **Mobile native app (iOS/Android).** Mobile web is a hard requirement (mobile-first design, ≥95 Lighthouse mobile). Native is deferred until web product-market fit is validated.
- **Multi-currency / internationalization.** USD only. `LANGUAGE_CODE = en-us`, `TIME_ZONE = America/Los_Angeles`.
- **User-to-user direct messaging.** Lead inquiries route through the platform with moderation; freeform DM is a moderation cost we will not bear in v1.
- **Live video / livestream.** Embed-only (YouTube, Instagram). No first-party streaming.
- **Listing data (price, address, bed/bath) for non-MLS sources.** No scraping. Realtor blog posts may reference listings descriptively, but the platform does not maintain a parallel listing database.
- **Buyer-side transaction tooling** (offer drafting, e-sign, escrow). Out of scope; refer users to their realtor.
- **Lender pre-qualification flows.** Lenders may appear as marketplace vendors, but the platform does not collect financial-application data.

## 6. Success Criteria (measurable)

| Metric | Target (6 months post-launch) | Measurement source |
|---|---|---|
| Monthly active users (MAU) | ≥10,000 | Sentry session events + Better Stack |
| Verified realtors (active license) | ≥100 | `accounts_realtorprofile` where `verified_at` is not null |
| Active vendors (≥1 published service) | ≥50 | `marketplace_vendor` with ≥1 `service` published |
| Forum threads/month | ≥200 | `forum_thread.created_at` aggregated |
| Comments + replies/month | ≥1,500 | UGC counts |
| AI tool runs/month | ≥1,000 | `tools_toolusage` row count |
| Net Promoter Score (NPS) | ≥40 | Quarterly in-app survey, n≥100 |
| Mod-queue median resolution time | <4 hours | `moderation_decision.created_at - flag.created_at` p50 |
| Pipeline false-negative rate (attacks approved) | 0 | Adversarial fixture pass-rate (must remain 100%) |
| Lighthouse mobile performance | ≥95 | Playwright-Lighthouse CI on top-20 routes |
| LCP p95 (mobile, 4G profile) | <2.5s | Real-user monitoring via Sentry |
| Uptime (rolling 30d) | ≥99.5% | Better Stack heartbeat checks |
| AI spend (Gemini, all categories) | <$80/month | Postmark/Gemini billing API + `ToolUsage` ledger |
| Pen-test High/Critical findings | 0 (pre-launch) | External pen-test report |

## 7. Constraints

### 7.1 Regulatory

- **Fair Housing Act (42 USC §3601 et seq.)** — content cannot use or imply discriminatory preference based on race, color, religion, national origin, sex, disability, familial status. Moderation Layer 1 includes a deterministic protected-class lexicon scan with a curated exceptions allowlist; Layer 2 (Gemini classifier) carries an explicit fair-housing rubric.
- **WA real-estate licensing (RCW 18.85).** Authoring as "realtor" requires verified active license. The platform does not provide brokerage services; it surfaces content authored by licensees.
- **RESPA (12 USC §2601, RESPA Section 8).** No referral fees between the platform and licensees, lenders, or settlement service providers. Marketplace is lead-gen only with no payment flow, removing Section 8 exposure.
- **WA Consumer Protection Act (RCW 19.86)** and **CAN-SPAM** — transactional email only by default; marketing email is opt-in.
- **ADA Section 508 / WCAG 2.1 AA** — public-facing surfaces meet AA contrast (4.5:1 body, 3:1 large text), keyboard nav, screen-reader compatibility.
- **GDPR-shaped data rights** — though the user base is US-domestic, we ship `GET /api/me/export/` and `DELETE /api/me/` to limit exposure if EU users access the platform.

### 7.2 Technical

- **Baseline scale: 10K MAU.** Architecture must serve 10K MAU comfortably on Railway's standard tiers (1×api 1GB, 1×celery 512MB, Postgres standard, Redis standard). Should accommodate 100K MAU without re-architecture (vertical scale + worker count).
- **Hosting: Railway (Phase 1).** Fly.io is documented alternate (`docs/adr/0001` §11). All code must be 12-factor portable.
- **Single Postgres instance, no sharding.** pgvector schema-ready (extension installed, columns reserved) but not active in v1.
- **Redis 7 single instance** — cache + sessions (during transition) + Celery broker + rate limits. No Redis cluster.
- **Stack lock.** Django 5.1, DRF, Next.js 15 App Router, Tailwind 3.4, Framer Motion 11. ADR-0005 documents the split-monolith decision.

### 7.3 Team

- **Solo developer/operator at launch.** Documentation, automation, and per-phase plans must reflect a single-person execution model. No "ask the platform team" — there is no platform team.
- **Skill profile:** Full-stack Django + Next.js + Tailwind + Postgres. Comfortable with Docker, Caddy, Celery. Limited Kubernetes; we deliberately avoid k8s.

### 7.4 Timeline

- **12–16 weeks from start to public launch** (8 sprints × 2 weeks each, see `docs/STATE-OF-THE-PROJECT.md`).
- Phases 0 + 1 complete (foundation: auth, license verify, design system, AI moderation, audit, admin lockdown).
- Phases 2–8 remaining: Content, AI Tools, Forum, Marketplace, Control Surfaces, Social Integration, Production Polish.
- No fixed external launch date; hold launch until all `NFR-2xx` security gates green.

### 7.5 Budget (operating)

| Line item | Monthly cost (10K MAU baseline) |
|---|---|
| Railway (api + celery + db + redis) | $40 |
| Cloudflare R2 (50 GB media, 200 GB egress) | $4 |
| Postmark (10K transactional emails) | $10 |
| Gemini API (moderation + tools, capped) | $50 |
| Sentry (Team plan) | $26 |
| Better Stack (Team plan) | $25 |
| Domain + TLS (TLS via Caddy + Let's Encrypt, free) | $1 |
| **Total** | **~$156/month** |

## 8. Stakeholders & Decision Rights

| Decision area | Owner | Consulted | Informed |
|---|---|---|---|
| Product scope (in/out of scope changes) | Operator (Vladi) | Engineering | Realtor advisory (post-launch) |
| Architecture / stack changes | Engineering | — | Operator |
| ADR additions / amendments | Engineering | Operator | All future contributors |
| Moderation policy (`platform-guidelines-v1.md`) | Operator + Legal review | Engineering | Realtor advisory |
| Pricing of vendor packages | Vendor (their own pricing) | — | Operator (visibility) |
| Verified-realtor approval | Automated via ARELLO; manual override = Operator | Engineering | — |
| Take-down / ban decisions | Mod/Operator (in mod console) | — | User (via notice) |
| Security disclosures / pen-test scope | Engineering | External pen-tester | Operator |
| Launch go/no-go | Operator | Engineering (security sign-off) | — |
| Brand / visual identity | Operator | Engineering (implementation) | — |

## 9. Approval & Sign-off

| Role | Name | Date | Status |
|---|---|---|---|
| Product Owner | Operator | 2026-05-03 | Approved |
| Engineering Lead | Engineering | 2026-05-03 | Approved |
| Security Reviewer | (external, scheduled Sprint 7) | TBD | Pending |
| Legal (Fair Housing / RESPA) | (external counsel review) | TBD | Pending |
| Accessibility (WCAG 2.1 AA) | Internal — axe-core CI gate | 2026-05-03 | Tooling green |

---

## 10. Cross-references

- **`docs/SRS.md`** — functional + non-functional requirements derived from this doc
- **`docs/SAD.md`** — architecture realizing the requirements
- **`docs/STATE-OF-THE-PROJECT.md`** — sprint plan to public launch
- **`docs/adr/0001-django-monolith.md`** — original monolith decision (superseded for transport by ADR-0005)
- **`docs/adr/0002-arello-for-license-verification.md`** — license trust layer
- **`docs/adr/0003-gemini-as-ai-provider.md`** — Gemini for moderation and tools
- **`docs/adr/0004-lead-gen-only-marketplace-v1.md`** — payments out of scope
- **`docs/research/platform-guidelines-v1.md`** — community standards and moderation policy
