# Sprint 4 — Vendor Onboarding + Lead Messaging + Notification Center

> Predecessor: Sprint 3. Master plan: `C:\Users\vladi\.claude\plans\i-want-you-to-validated-brook.md`.

## Goal

Vendor multi-step onboarding wizard goes from scaffolded to complete. In-platform `LeadMessage` UI lets vendors and buyers converse on a lead. Notification center wires Postmark + in-app stream.

## Tasks

1. **Vendor wizard finish.** Existing scaffolding at `frontend/app/(dashboard)/vendor/onboard/[step]/page.tsx`. Steps: Business → Categories → Service catalog → Bundle (optional) → Contact + verify → Submit. Each step persists `VendorProfile.wizard_state` JSON; back/forward navigation safe; submit flips status from DRAFT → ACTIVE pending mod review.
2. **Lead messaging UI.** Vendor lead detail (`/vendor/leads/[id]`) and a buyer-side lead view (new: `/dashboard/leads/[id]`) both render the `LeadMessage` thread. Compose box, attachment via R2, every message routes through moderation pipeline (already wired model-side via `ModeratableMixin`). Real-time updates via TanStack Query polling (1 minute) for v1; SSE in v2.
3. **Notification center.** New page `/notifications` (already scaffolded). Lists all in-app notifications with unread badge in top nav. Categories: lead_received, lead_message, post_approved, post_flagged, license_renewal_due, mod_action. User preferences page lets user mute by category and choose email/in-app/both per category.
4. **Postmark templates**: welcome, email-verify, password-reset, lead-received, lead-message-received, mod-removed, mod-approved, license-renewal-30d, license-renewal-7d, license-expired. Postmark template IDs in env. `apps/notifications/services/postmark.py` sends via django-anymail.

## Verification

- E2E: vendor signs up → completes 5-step wizard → submits → lands on /vendor → sees pending status
- Lead conversation: buyer sends inquiry → vendor receives email + in-app notification → vendor responds in /vendor/leads/{id} → buyer receives email + in-app notification
- Notification preferences: mute "lead_message" emails → buyer message arrives → in-app shows it but no email sent

## Sign-off

- [ ] Wizard 5-step flow complete with state persistence
- [ ] Lead messaging works both directions, with moderation
- [ ] Notification center renders unread badge + filterable list
- [ ] User notification preferences work per category
- [ ] All 10 Postmark templates wired
- [ ] pytest + Playwright green for vendor onboard + lead conversation flows
- [ ] Sprint 4 commit pushed
