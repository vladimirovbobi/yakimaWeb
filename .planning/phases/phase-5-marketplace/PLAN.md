# Phase 5 — Marketplace (Fiverr-shaped, lead-gen only)

## Goal
Vendors expose Services + per-service Packages + cross-service Bundles. Buyers browse, request quotes (Lead). Reviews tied to verified Leads.

## Done
- [ ] Category tree (max 3 levels) seeded with real-estate-adjacent verticals
- [ ] Vendor onboarding: Vendor profile + Service create + Package create + Bundle create
- [ ] Public marketplace listing page (Fiverr-card grid + filters)
- [ ] Service detail (gallery + 3-tier package table + FAQ + reviews + seller sidebar)
- [ ] Bundle detail (line items + recurring cadence)
- [ ] Lead inquiry flow (request quote → vendor responds → status state machine)
- [ ] Review system (1 review per Lead, vendor can respond)
- [ ] Search + filter (category, price range, response time, level)
- [ ] Tests + 5 new prompt-injection fixtures (vendor descriptions are big attack surface)

## Models
- `Category` (treebeard MP_Node, max 3 levels)
- `VendorProfile` (already exists in accounts app — extend)
- `Service(ModeratableMixin, TimeStampedModel)` — vendor, category, title, slug, description, hero_image
- `Package(TimeStampedModel)` — service, tier (basic/standard/premium), name, description, price_low, price_high, delivery_days
- `Bundle(ModeratableMixin, TimeStampedModel)` — vendor, name, description, billing_cadence (one_time/monthly/quarterly/annual), price_total, min_term_months
- `BundleItem` — bundle, service, quantity_per_period, fulfillment_note
- `Lead(TimeStampedModel)` — vendor, buyer, service or package or bundle (nullable FKs), status (pending/contacted/won/lost), thread (in-platform messages later)
- `Review(ModeratableMixin, TimeStampedModel)` — lead, rating (1-5), body, vendor_response, vendor_response_at
- `LeadMessage(TimeStampedModel)` — lead, sender, body (in-platform messaging Phase 5.1)

## Skills: caveman, frontend-design (Fiverr-grade UX from research/marketplace-patterns/), security-review (treat vendor input as adversarial), copy-editing (category labels)
