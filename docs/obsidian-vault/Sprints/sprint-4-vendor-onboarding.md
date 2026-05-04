---
sprint: 4
title: Vendor onboarding + lead messaging (audit)
status: done (audit pass)
date: 2026-05-04
plan_file: .planning/phases/sprint-4-vendor-onboarding/PLAN.md
---

# Sprint 4 — Vendor onboarding + lead messaging (audit)

## Goal

Confirm the already-shipped vendor onboarding wizard, lead messaging, and
notification center match the Sprint 4 plan.

## Audit findings

### Vendor onboarding wizard

- ✅ Multi-step wizard at `/dashboard/vendor/onboard/[step]`
- ✅ State persistence via `VendorProfile.wizard_state` JSON
- ✅ 5 steps: Business → Categories → Services → Gallery → Publish
- ✅ Submit flips `VendorProfile.status` from DRAFT → ACTIVE pending mod review
- ⚠ Sprint 1.5 fix: corrected `business_name` → `name` mismatch in
  `app/(dashboard)/vendor/onboard/[step]/page.tsx` to match
  `BusinessData` type

### Lead messaging UI

- ✅ Threaded `LeadMessage` UI on `/vendor/leads/[id]`
- ✅ SSE + 10s polling fallback
- ✅ Cmd+Enter send
- ✅ All messages route through ModeratableMixin → moderation pipeline

### Notification center

- ✅ `/dashboard/notifications` page wired
- ✅ NotificationBell in dashboard header
- ✅ apps/notifications app with Notification model + signal hooks +
  email digest beat task
- ✅ 14 tests in apps/notifications/tests/

### Postmark integration

- ✅ django-anymail wired; falls back to console backend in dev
- ✅ Templates registered for: welcome, email-verify, password-reset,
  lead-received, lead-message-received, mod-removed, mod-approved,
  license-renewal-{30d,7d,expired}

## Sprint 6 delivery integration

Sprint 6 (delivery service) will add a "Deliver assets" tab on
`/vendor/leads/[id]` and a "View deliveries" tab on `/dashboard/leads/[id]`.
Backend complete; UI follow-on.

## Cross-links

- Predecessor: [[sprint-3-tools]]
- Successor: [[sprint-5-mod-console]]
