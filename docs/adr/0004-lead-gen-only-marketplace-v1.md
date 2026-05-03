# ADR 0004 — Marketplace v1 is Lead-Gen Only (No Payments / Escrow)

**Status:** Accepted (2026-05-03)

## Context
Marketplace lets Yakima/Central WA realtors find real-estate-adjacent service providers (photographers, junk removal, 3D tours, lenders, websites, AI agents, etc.) and lets vendors expose services + bundles. Reviews, ratings, vendor badges. Question: do we process payments in v1?

We considered:
1. **Lead-gen only — vendor and buyer connect on-platform, transact off-platform** (chosen)
2. **Stripe Connect (vendors as connected accounts)** — full payment processing; massive regulatory + engineering footprint
3. **Escrow with platform-held funds** — even heavier; triggers state money-transmitter licensing requirements
4. **Subscription billing for vendors only (lead gen + paid featured listings)** — partial; revenue-on-platform but limited scope

## Decision
v1 is lead-gen only. Buyer requests a quote on a service or bundle → vendor responds in-platform → status moves through `pending → contacted → won / lost`. Reviews tied to the `Lead` (verified-transaction badge), not the `Vendor` directly. Off-platform payment / contract / fulfillment.

Featured-listing fees and vendor subscriptions deferred to v2 (also no Stripe — manual invoicing initially, swap to Stripe when volume warrants).

## Why
- Skip Stripe Connect onboarding (KYC, 1099, tax forms, dispute handling, chargebacks) — months of work
- Skip state money-transmitter licensing analysis (WA, OR, ID) — needs lawyer
- Skip PCI scope (we never touch card data)
- Lets us validate marketplace product-market fit before committing infra to revenue
- Reviews still verifiable because Lead is the verifiable transaction record

## Consequences
**Positive**
- 4-6 weeks of engineering avoided
- Zero payment-related security surface in v1
- Faster path to live marketplace
- Vendors keep 100% of their revenue → easier sell to early vendors

**Negative / Accepted**
- No platform revenue from marketplace in v1 — accepted; revenue plan = featured listings + vendor subscriptions added in v2
- Buyers can't pay through platform → friction in conversion; mitigated with clear UX expectations + integrated messaging
- Some vendors may want platform-handled invoicing (signal of trust) — we collect this feedback to size v2

## Schema implication
- `Lead` table is the v1 transaction record
- `Order` table deferred to v2 (will sit alongside Lead, sharing review pipeline)
- `Review.lead_id` (not `vendor_id`) — verified-transaction trust mechanism

## Revisit when
- 50+ active vendors + 200+ leads/mo → add Stripe Connect for one-shot payments
- Vendor demand for platform invoicing > 30% in survey → prioritize subscription billing
- Marketplace gross volume estimable at > $500K/yr off-platform → evaluate platform fee model
