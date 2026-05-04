# Yakima Web — Beta Program

## Goals

1. Validate the verified-realtor flow end-to-end with real ARELLO data.
2. Stress-test the marketplace inquiry loop with real vendors and real buyers.
3. Surface friction in onboarding (signup, license verify, vendor wizard).
4. Catch moderation false positives before public launch.

## Cohort plan

- 20 to 50 hand-picked Yakima realtors (mix of independent + brokerage-affiliated).
- 10 service vendors (3 photographers, 2 lenders, 2 junk removal, 2 3D-tour, 1 drone).
- 5 to 10 power-buyer testers (recurring forum users).
- 2 outside moderators paid hourly for the first month.

Recruitment via direct outreach. No public signup until the public launch.

## Invite template

**Subject:** Early invite — Yakima Web beta

Hi [Name],

I am inviting a small group of Yakima Valley realtors to test Yakima Web before
the public launch. The platform combines license-verified realtor blogs, a
vendor marketplace, AI listing tools, and a community forum. Local-first.
Designed for the Valley.

What we need from you for the next 4 weeks:
- Verify your license (one-time, takes 2 minutes).
- Publish at least one blog post or comment on someone else's post.
- Try the AI furniture remover or description writer once.
- Reply to a 5-question feedback survey at the end of the month.

What you get:
- Early access — your blog index page goes live the day the platform opens.
- Free first month of any paid tier we eventually launch.
- Direct line to me for any bug, gripe, or idea.

Reply yes and I will send a unique invite link.

— [FILL founder name]

## Onboarding call script (15 minutes)

1. Confirm beta-tester role and expectations (5 min).
2. Walk through signup -> email verify -> license verify (3 min).
3. Tour blog editor + community forum + a sample marketplace inquiry (5 min).
4. Provide direct support line + Slack invite + feedback form link (2 min).

## Weekly feedback session

- Time: Friday 4 PM PT, 30 min, Zoom.
- Format: rotating cohorts of 5 to 8 testers.
- Agenda:
  1. What worked this week (5 min).
  2. What broke or annoyed you (15 min).
  3. One thing you would change before public launch (10 min).
- Notes published to `docs/launch/beta-feedback/YYYY-MM-DD.md`.

## Issue triage flow

1. Tester reports via in-app feedback widget OR Slack `#yw-beta` OR email.
2. Operator triages within 24h:
   - Severity 1 (data loss, security, paid feature broken) -> fix immediately.
   - Severity 2 (functional but degraded) -> file GitHub issue, fix in current sprint.
   - Severity 3 (cosmetic, copy, request) -> backlog.
3. GitHub issue template: `.github/ISSUE_TEMPLATE/beta-feedback.md` (TODO).
4. Auto-link beta findings to their GitHub issue in the weekly note.

## NDA notes

Beta participation is non-confidential by default. Privacy + Terms of Service
cover normal use. We do **not** require beta testers to sign an NDA. Any
participant may screenshot or describe the platform publicly without
restriction except:

- Do not share credentials or personal data of other participants.
- Do not redistribute the source code (the repo is private).

If a participant wants to formally co-author a case study, we can sign a
mutual NDA per case. Use a standard 1-page mutual NDA — keep it light.

## Beta exit criteria

The beta is "done" when all five are true:

- [ ] 30 verified realtors active for at least 14 days.
- [ ] 8 vendors with at least 3 leads each.
- [ ] No severity-1 issues open for more than 4 hours.
- [ ] Moderation false-positive rate under 5 percent (manual sample).
- [ ] Founder + on-call signed off on `docs/launch/LAUNCH-CHECKLIST.md` Day -7.
