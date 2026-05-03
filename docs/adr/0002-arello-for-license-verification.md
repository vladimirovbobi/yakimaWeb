# ADR 0002 — ARELLO API for WA Real Estate License Verification

**Status:** Accepted (2026-05-03)

## Context
Realtor accounts on the platform get a verified badge + ability to author blog posts only after their WA real estate license is confirmed active. We need a programmatic, automatable check at signup + recurring re-verification (catch suspended/revoked/expired licenses).

We considered:
1. **ARELLO Licensee Verification Service v2** (chosen) — REST API, ~3M records across all US jurisdictions, daily updates, ~$300/mo
2. **Scrape WA DOL public lookup** (https://professions.dol.wa.gov/s/license-lookup) — Salesforce Lightning Aura UI, JS-required, no documented API, fragile, likely rate-limited and ToS-grey
3. **Manual verification by ops** — doesn't scale past ~50 realtors
4. **No verification, trust-on-claim** — kills the badge's value; opens platform to imposters

## Decision
ARELLO API v2 (https://www.arello.com/information.cfm). Synchronous call on signup (~100ms latency, blocks registration form by ~1 polling tick), async re-verification every 30 days via Celery beat. Store full raw response per call in `LicenseCheck` table for audit. Accept license types: Broker, Managing Broker, Designated Broker.

Sandbox first (free); production key after Phase 1 deploy.

## Consequences
**Positive**
- One vendor, one bill, one integration
- Daily-updated database — catches revocations within 24h
- Multi-state ready (we expand outside WA later → no rework)
- REST + JSON → trivial Django integration
- Audit blob lets us defend deactivation decisions to disputing realtors

**Negative / Accepted**
- $300/mo recurring ($3,600/yr) — line item we eat to avoid scraping fragility
- Vendor lock-in — mitigated by `LicenseCheck.source` field; could swap to scraping or manual fallback
- ARELLO downtime blocks signup — mitigated: queue verification, allow account creation in `pending` state, retry; downgrade UX shows "verification queued"
- License renewal is 2-year cycle in WA → 30-day re-check cadence is overkill but cheap insurance against silent revocations

## Implementation notes
- Client wrapper: `apps/accounts/services/arello.py`
- Celery task: `apps/accounts/tasks.py::verify_license_task` (signup) + `reverify_all_active_realtors` (beat)
- Failure modes (ARELLO down, license not found, API quota exceeded) all logged + surfaced to ops dashboard
- Test fixtures cover: active broker, expired, suspended, revoked, not-found, API timeout

## Revisit when
- ARELLO pricing > $1K/mo with negligible volume → evaluate state-by-state alternatives
- We expand to a state ARELLO doesn't cover well → add second verification source per jurisdiction
