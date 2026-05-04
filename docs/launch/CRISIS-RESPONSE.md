# Yakima Web — Crisis Response Playbook

Every crisis: detect, contain, communicate, fix, post-mortem. The five
scenarios below cover roughly 90 percent of the failure surface. For anything
else, fall through to `docs/RUNBOOK.md`.

---

## 1. Site down (Caddy / API / DB / Railway outage)

### Detection signals
- Better Stack pings homepage probe 3 times consecutively.
- Sentry transaction error rate jumps above 10 percent for 3 minutes.
- User reports in Slack `#yw-alerts`.

### Immediate response (under 15 min)

1. Confirm the outage from a clean device on a different network. Don't fix
   what isn't broken.
2. Update https://status.yakimaweb.com to `INVESTIGATING — Site down`.
3. Check Railway dashboard:
   - Is the API service healthy?
   - Is the database connection count saturated?
   - Did a deploy just complete?
4. If a deploy is the cause: roll back via `railway redeploy --previous`.
5. If Postgres is unreachable: check Railway DB metrics, page on-call DBA.
6. If Caddy is unreachable: check Railway logs for the proxy service.
7. If Railway itself is down: switch DNS to the standby Fly.io deployment
   (TTL is 60s — change in Cloudflare DNS).

### Stabilization (1 hour)

- Confirm root cause — read the last 30 minutes of `railway logs` for each service.
- Update status page to `IDENTIFIED — [root cause in plain English]`.
- Verify backups are current. If we lost data, page founder.

### Resolution (24 hours)

- Status page to `RESOLVED` with brief root cause + duration.
- Post-mortem doc filed at `docs/launch/post-mortems/YYYY-MM-DD-site-down.md`.
- Tag related Sentry issues. Open a follow-up issue if a permanent fix is needed.

### Communication template

> We are investigating a site-wide outage that started at [time PT].
> Estimated impact: [duration]. We will post the next update in 30 minutes or
> when service is restored, whichever is sooner.

---

## 2. AI spend runaway (Gemini bill spiking)

### Detection signals
- Gemini daily spend metric crosses 80 percent of `GEMINI_DAILY_SPEND_CAP_USD`.
- Anomaly detector raises HIGH severity finding for AI tool usage.
- Sudden burst of 422 "moderation_blocked" responses (could indicate adversarial probing).

### Immediate response (under 15 min)

1. Verify the spend metric in Better Stack. False alarms come from missed retries.
2. Inspect `apps.tools.models.ToolUsage` for the last hour:
   - Is one user accountable for the surge?
   - Is one tool runaway?
3. Hard cut: set `GEMINI_DAILY_SPEND_CAP_USD=0` in Railway env and redeploy.
   This is a 1-line, 1-minute action. Do not hesitate.
4. Status page `INVESTIGATING — AI tools temporarily disabled`.

### Stabilization (1 hour)

- If a single user is responsible: ban them via admin (auto-logged), refund
  their usage credits if any.
- If a script / prompt-injection is responsible: escalate to security review,
  add the payload to `apps/moderation/tests/fixtures/prompt_injection_attacks.json`.
- If legitimate usage simply exceeded cap: raise the cap with founder approval.

### Resolution (24 hours)

- Restore AI tools by re-enabling the cap.
- Post-mortem at `docs/launch/post-mortems/YYYY-MM-DD-ai-spend.md`.
- File issue to harden the responsible code path.

### Communication template

> AI tools (furniture remover, description writer) are temporarily disabled
> while we investigate elevated usage. Other features (blog, marketplace,
> forum) remain available. Update in 1 hour.

---

## 3. Major moderation failure (offensive UGC visible)

### Detection signals
- User reports via in-app flag.
- Outside party emails press@yakimaweb.com or general@.
- Sentry catches a moderation pipeline exception.

### Immediate response (under 15 min)

1. Take the offending content down via `apps/moderation/services/` admin actions.
   Soft-delete first; hard-delete only after capture.
2. Capture evidence: screenshot, full HTML, original post body. Save to
   `docs/launch/incident-evidence/YYYY-MM-DD/`.
3. If the offender is a known user: suspend the account.
4. Status page `INVESTIGATING — Content moderation review`.

### Stabilization (1 hour)

- Walk the moderation log: did the pipeline fire? What did it return?
- If pipeline approved erroneously: open a Sev-1 issue, write a regression
  test in `apps/moderation/tests/test_pipeline.py` that fails until fixed.
- Notify the operator group. If user data may be exposed (doxxing), notify
  founder.

### Resolution (24 hours)

- Patch the pipeline if a bug is found. Deploy + run the regression suite.
- Post-mortem: what broke, what regressed, what new fixture was added.
- If press attention occurs, see Section 5 (data breach) communication tone.

---

## 4. License-fraud event (fake realtor)

### Detection signals
- ARELLO callback returns `unverified` for an account previously marked verified.
- A user reports another user's license number is wrong.
- Anomaly detector raises new_account_burst from a verified realtor account.

### Immediate response (under 15 min)

1. Mark the suspect account `verification_status=under_review` (admin action).
   This blocks publishing without notifying the user.
2. Re-run the ARELLO check via `apps/accounts/services/arello.py` directly.
3. If the second check confirms unverified: revoke verification + suspend posts.
4. Capture all `LicenseCheck` rows for this account — they are append-only.

### Stabilization (1 hour)

- Email the account holder asking for a current proof-of-license screenshot.
- If no response in 24h, leave account suspended.
- If response confirms fraud: hard-suspend, remove all their content, log to
  ActionLog with `reason="license_fraud_confirmed"`.

### Resolution (24 hours)

- Reach out to ARELLO if a systemic verification miss is likely.
- File a regression test that covers the verification path.
- If the fake realtor harmed users, prepare a mitigation comms statement.

---

## 5. Data breach suspected

### Detection signals
- Sentry catches an unauthorized DB query pattern.
- AnomalyDetector raises `shared_ip_multi_user` HIGH for a staff IP.
- External report from security researcher.
- Unusual pattern in `apps/audit/models.AccessLog` for /admin/.

### Immediate response (under 15 min)

1. Treat as confirmed until proven otherwise.
2. Founder + on-call enter a private channel. No social media, no public posts.
3. Rotate `DJANGO_SECRET_KEY` in Railway secrets. Flush sessions.
4. Force-logout all users (delete all SimpleJWT outstanding tokens).
5. Pause all non-essential services: Celery beat, image worker.
6. Status page: `INVESTIGATING — Maintenance window in progress` (do not say
   "breach" until we know).

### Stabilization (1 hour)

- Pull the last 24h of `AccessLog` and `ActionLog`. Look for unusual paths,
  IPs, or write patterns by staff accounts.
- If exfiltration is confirmed: identify what was taken, who is affected.
- Notify legal counsel (founder retains).
- Begin drafting the public disclosure.

### Resolution (24 to 72 hours)

- File a CVE if the vulnerability is novel.
- Notify affected users by email. Be specific: what data, when, what we did.
- File breach disclosure with WA AG if more than 500 WA residents affected
  (RCW 19.255). Within 30 days.
- Post-mortem published publicly within 7 days (with sensitive details redacted).

### Communication template (public)

> On [date PT], we detected a security event that may have affected
> [N] Yakima Web accounts. We have [contained / stopped / patched] the issue.
>
> Affected data: [be specific — emails, hashed passwords, post content].
> Not affected: [be specific — credit cards if true, etc.].
>
> What you should do: [reset password / enable 2FA / monitor account].
>
> What we did: [summary].
>
> We are sorry. We will publish a full post-mortem at [URL] within 7 days.

### Communication template (affected user, email)

> Subject: Security incident affecting your Yakima Web account
>
> [Name],
>
> We are writing to let you know that on [date], a security incident may have
> exposed [specific data]. We have already [action]. Please [user action].
>
> If you have any questions, reply to this email or contact security@yakimaweb.com.
>
> Sincerely,
> [Founder name], Yakima Web

---

## On-call rotation

| Week | Primary | Secondary |
|---|---|---|
| 1, 3 | [FILL] | [FILL] |
| 2, 4 | [FILL] | [FILL] |

Primary phone is in 1Password under `oncall-primary`.

## Escalation paths

- Tier 1: Better Stack pages on-call.
- Tier 2: After 15 min unack, pages secondary.
- Tier 3: After 30 min unack, pages founder directly.

## Post-mortem template

Always write a post-mortem within 48h of resolution, even for low-severity events.
Template at `docs/launch/post-mortems/_TEMPLATE.md` (TODO — fill in with first event).

Required sections:
- Summary (3 sentences max)
- Timeline (UTC)
- Root cause
- What went well
- What went poorly
- Action items (with owner + due date)
