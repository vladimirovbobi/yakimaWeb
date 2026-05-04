# Yakima Web — Launch Checklist

Two weeks of countdown. One owner per item. One green checkmark per success.

## Day -14 — Final pen test results

- [ ] External pen test report received and triaged.
- [ ] All Sev-1 + Sev-2 findings have a fix branch open.
- [ ] Sev-3 findings logged in `docs/RISK-REGISTER.md`.
- [ ] Founder + security reviewer signed off on the pen test summary.

## Day -10 — Privacy + Terms attorney signoff

- [ ] Final draft of `frontend/app/(public)/privacy/page.tsx` — attorney red-lined.
- [ ] Final draft of `frontend/app/(public)/terms/page.tsx` — attorney red-lined.
- [ ] DPA + cookie disclosure cross-checked against tracker list.
- [ ] Privacy + Terms versions pinned in `docs/launch/legal/`.

## Day -7 — Press kit final

- [ ] `docs/launch/PRESS-KIT.md` placeholders filled.
- [ ] Founder quote approved.
- [ ] Brand assets exported in 1x and 2x at the paths listed in the press kit.
- [ ] Press release PDF generated, founder-signed, dropped into `docs/launch/assets/`.
- [ ] Email targets list curated (local Yakima press first).

## Day -5 — Brand assets locked + OG images regenerated

- [ ] OG images for /, /blog, /services, /community regenerated.
- [ ] Twitter Card metadata validated via Twitter card validator.
- [ ] Favicon set + apple-touch-icon up to date.
- [ ] Social previews (LinkedIn, Facebook, Mastodon) tested manually.

## Day -3 — Load test passes

- [ ] `load_tests/k6/baseline.js` passes against staging.
- [ ] `load_tests/k6/forum_burst.js` passes — VoteThrottle fires.
- [ ] `load_tests/k6/ai_tool.js` passes — spend cap fires.
- [ ] `load_tests/k6/sustained.js` 24h soak finishes without OOM kill.
- [ ] Results files committed to `load_tests/results/`.

## Day -2 — Smoke checklist on production

Hit production directly, with a clean browser, no extensions:

- [ ] Homepage loads, hero animates, CTAs work.
- [ ] /signup -> verify email -> login.
- [ ] /dashboard/realtor -> license verify (real ARELLO).
- [ ] /dashboard/realtor/posts/new -> publish a draft, then unpublish.
- [ ] /services -> filter, view detail, send inquiry as anon.
- [ ] /community -> create thread, vote, reply.
- [ ] /tools/furniture-remover -> upload + run a real image.
- [ ] /tools/description-writer -> generate + save.
- [ ] /privacy, /terms, /guidelines render and have correct contact info.
- [ ] /admin/ requires 2FA + IP allowlist.

## Day -1 — Monitoring + alerting verified, on-call on standby

- [ ] Better Stack heartbeats green.
- [ ] Sentry catches a synthetic error from production (test alert chain).
- [ ] PagerDuty test ping reaches primary on-call within 60s.
- [ ] Status page is up and announces "Standby for launch".
- [ ] On-call rotation Day-0 to Day-7 is scheduled.
- [ ] `docs/launch/CRISIS-RESPONSE.md` printed and on the desk.
- [ ] Privacy + Terms pages have the correct contact email.
- [ ] DNS TTLs lowered to 300s for fast rollback.

## Day 0 — Soft launch

- [ ] Beta cohort emailed: "We are live. Tell your friends."
- [ ] Status page set to "Operational".
- [ ] Founder posts to local Yakima Valley Slack / Facebook groups.
- [ ] Press kit emailed to local press list.
- [ ] First public blog post by a verified realtor goes live by 10 AM PT.
- [ ] Soft launch: do NOT publish on Hacker News. The Valley audience first.

## Day +1 — Monitor + iterate

- [ ] Read every Sentry issue from launch. Tag urgent vs noise.
- [ ] Review Better Stack uptime + p95 latency.
- [ ] Read every flag in the moderation queue.
- [ ] Review the in-app feedback widget submissions.
- [ ] Daily standup at 9 AM PT for the first 7 days.
- [ ] Day +7: Public post on /blog "What we learned in our first week".

## Sign-off

- [ ] Founder signs Day-1 readiness in `docs/launch/sign-off-day-1.md`.
- [ ] On-call signs the smoke checklist in the same file.
- [ ] Operator confirms moderation queue is staffed for 7 days.

If any unchecked box exists at Day -1, push the launch by 24 hours. There is
no shame in delay. There is shame in a public failure on Day 0.
