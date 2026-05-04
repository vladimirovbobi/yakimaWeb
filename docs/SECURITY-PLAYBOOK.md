# Security Playbook — Yakima Real Estate Hub

## Document control

| Field | Value |
|---|---|
| Version | 1.0 |
| Date | 2026-05-03 |
| Owner | Yakima Real Estate Hub Security |
| Classification | Internal |
| Review cadence | Quarterly + after every SEV-1/SEV-2 |
| Cross-references | `docs/RISK-REGISTER.md`, `docs/THREAT-MODEL.md`, `docs/SRS.md`, `docs/SAD.md`, `docs/ICD.md`, `docs/MTP.md`, `docs/RUNBOOK.md` |

---

## 1. Roles and RACI

For v1 the platform is solo-operated. The roles below describe the structure that becomes active when a second engineer joins; in solo mode the founder fills every role, and the pre-defined succession contract (R-020 in risk register) names a backup contractor.

| Role | Definition |
|---|---|
| Incident Commander (IC) | Coordinates response, owns timeline, makes call/no-call decisions, assigns severity. |
| Security Lead (SL) | Forensics, controls evaluation, post-incident threat-model update. |
| Communicator (C) | User-facing communication, status page, social, support inbox, regulator contact. |
| Engineering Lead (EL) | Code-level fix, deploy, validation, restoration. |

### RACI matrix (incident response)

| Activity | IC | SL | C | EL |
|---|---|---|---|---|
| Sev triage decision | A/R | C | I | C |
| Forensic evidence collection | I | A/R | I | C |
| Containment actions | A | C | I | R |
| Patch development + deploy | A | C | I | R |
| User notification | A | C | R | I |
| Regulator notification | A | R | C | I |
| Status page updates | A | I | R | I |
| Postmortem authoring | A | R | C | C |

R = Responsible, A = Accountable, C = Consulted, I = Informed.

---

## 2. Severity definitions

| Sev | Trigger conditions | On-call response |
|---|---|---|
| SEV-1 | Confirmed breach with data exfiltration; production fully down; financial fraud confirmed; admin account confirmed compromised; widespread doxxing event. | Page on-call. All-hands. T0 to engagement < 15min. Status page within 30min. SLA: containment < 4h. |
| SEV-2 | Vulnerability with active exploitation but limited blast radius; partial outage > 30min; one-account compromise; pipeline failure approving multiple bad items per hour; license-fabrication confirmed. | Page on-call business hours; ticket out-of-hours. T0 < 1h. Status page < 2h. SLA: containment < 24h. |
| SEV-3 | Known vulnerability without active exploitation; intermittent outage; isolated audit anomaly; single-item moderation miss. | Ticket. Address in current sprint. SLA: fix < 1 sprint. |
| SEV-4 | Hygiene improvements, observed weakness, dependency update. | Backlog item. SLA: address in next planning cycle. |

---

## 3. Incident response procedures

Every incident follows: **Detect → Triage → Contain → Eradicate → Recover → Postmortem**.

### 3.1 SEV-1 procedure

**Detect** — Alert from Sentry, Better Stack, user report, security@ inbox, or operator dashboard alarm.

**Triage (T0 → T+15min)**

- IC acknowledges page in chat.
- IC opens incident channel `inc-YYYYMMDD-NN`.
- IC sets severity, summarizes initial signal in pinned message.
- C posts initial status page entry: "Investigating incident affecting [scope]. Updates every 30 min."
- SL begins forensic capture (Section 9).
- EL stands by for containment actions.

**Contain (T+15min → T+1h)**

- IC authorizes one of: feature-flag kill, IP block, user lock, role revoke, full read-only mode.
- EL executes containment. SL captures every command run with timestamps.
- C updates status page after first contain action.

**Eradicate (T+1h → T+8h)**

- SL identifies root cause + IoCs.
- EL builds patch + tests in branch with `incident/` prefix.
- IC reviews; deploy under emergency change window (skip standard approval gate but document).
- SL confirms IoCs cleared.

**Recover**

- EL restores normal operation (un-flag features, restore traffic).
- C posts resolved status.
- IC declares incident closed.

**Postmortem (within 5 business days)**

- IC drafts blameless postmortem in `docs/incidents/YYYY-MM-DD-<slug>.md`.
- Sections: timeline, impact, root cause, what went well, what didn't, action items, owners, due dates.
- SL updates THREAT-MODEL.md if new threat or control discovered.
- IC reviews RISK-REGISTER.md scoring for affected risk.
- New fixtures added if applicable.

**Checklist**

- [ ] Channel opened
- [ ] Severity assigned
- [ ] Status page live
- [ ] Forensic capture started
- [ ] Containment authorized + executed
- [ ] Root cause identified
- [ ] Patch deployed
- [ ] Verification completed
- [ ] Status page resolved
- [ ] User notification sent (if required)
- [ ] Regulator notification sent (if required)
- [ ] Postmortem published
- [ ] Action items tracked

### 3.2 SEV-2 procedure

Same shape as SEV-1, relaxed timing: T+1h triage, T+24h containment, T+72h fix. Status page only if user-visible.

### 3.3 SEV-3 procedure

- File ticket in current sprint.
- EL fixes in a normal feature branch.
- Standard review + verify + merge.
- Update fixtures + tests.

### 3.4 SEV-4 procedure

- File backlog ticket.
- Address in next sprint planning.

---

## 4. Runbooks

### 4.1 Suspected credential compromise (single user)

**Indicators** — login from unusual geo/UA, password-reset flood, user reports unauthorized actions, ActionLog shows actions user denies.

**Steps**

```
1. Confirm signal:
   .venv/Scripts/python.exe manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> u = get_user_model().objects.get(email="<user>")
   >>> u.accesslog_set.order_by('-created_at')[:50]

2. Lock the account:
   >>> u.is_active = False
   >>> u.save()

3. Revoke all refresh tokens:
   >>> from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
   >>> for tok in OutstandingToken.objects.filter(user=u):
   ...     BlacklistedToken.objects.get_or_create(token=tok)

4. Audit recent ActionLog entries by this user:
   >>> from apps.audit.models import ActionLog
   >>> ActionLog.objects.filter(user=u, created_at__gte=...).order_by('-created_at')

5. Initiate password reset:
   >>> from django.contrib.auth.forms import PasswordResetForm
   >>> form = PasswordResetForm({'email': u.email})
   >>> form.is_valid() and form.save(request=None)

6. Email user from security@ explaining lockout + reset path.

7. After reset confirmed:
   >>> u.is_active = True
   >>> u.save()

8. Log incident in incidents/ folder.
```

**Decision points**

- If admin/staff account → escalate to runbook 4.2.
- If multiple users showing same pattern → likely credential stuffing, escalate to SEV-1, rotate JWT signing key (Section 5).

### 4.2 Suspected admin or superadmin account compromise

**Indicators** — admin login from new IP (already blocked, but alert fires), TOTP failures, unexplained mass changes, password-reset email to admin email, ActionLog superuser write outside business hours.

**Steps (SEV-1)**

```
1. INSTANT cut — disable account at DB level:
   psql $DATABASE_URL
   UPDATE auth_user SET is_active = false, is_staff = false, is_superuser = false
   WHERE id = <admin_id> RETURNING email, last_login;

2. Tighten admin IP allowlist to known-good only:
   Edit ALLOWED_ADMIN_IPS env var on Railway (push deploy or apply via dashboard).
   Confirm middleware reload.

3. Force re-enroll TOTP for all is_staff users:
   >>> from django_otp.plugins.otp_totp.models import TOTPDevice
   >>> TOTPDevice.objects.filter(user__is_staff=True).delete()
   On next login, staff prompted to re-enroll.

4. Rotate DJANGO_SECRET_KEY following Section 5 procedure.
   This invalidates ALL sessions and JWTs system-wide.

5. ActionLog forensic audit — last 30 days, all writes by compromised admin:
   SELECT user_id, model, instance_id, action, created_at, ip_address
   FROM audit_actionlog
   WHERE user_id = <admin_id>
     AND created_at > NOW() - INTERVAL '30 days'
   ORDER BY created_at;

6. AccessLog cross-check — every page touched:
   SELECT path, ip_address, user_agent, created_at, status_code
   FROM audit_accesslog
   WHERE user_id = <admin_id>
     AND created_at > NOW() - INTERVAL '30 days'
   ORDER BY created_at;

7. Identify any data tampering:
   For each ActionLog row showing UPDATE on user-visible models, validate
   that the change was legitimate by comparing payload_json to current state.

8. If tampering found, restore from latest pre-incident backup (runbook 4.6).

9. Revoke any API tokens issued to the admin (Postmark webhook tokens, etc.).

10. Communicate:
    - User comms ONLY if user-visible data tampered (WA RCW 19.255 trigger).
    - Otherwise internal-only incident report.
```

### 4.3 Prompt injection that bypassed pipeline

**Indicators** — user report of policy-violating content live; mod queue audit shows item that should have been flagged; ActionLog shows pipeline approval on retrospective review.

**Steps (SEV-2)**

```
1. Capture the failing input verbatim:
   >>> from apps.moderation.models import ModerationDecision
   >>> dec = ModerationDecision.objects.get(content_pk=<id>, model_name='<Model>')
   >>> print(dec.layer1_output)
   >>> print(dec.layer2_prompt)
   >>> print(dec.layer2_raw_response)
   >>> print(dec.classification)

2. Take the bad item out of public:
   >>> from apps.<app>.models import <Model>
   >>> obj = <Model>.objects.get(pk=<id>)
   >>> obj.moderation_state = 'pending_review'
   >>> obj.save()
   This triggers re-queue via post_save signal.

3. Add fixture to apps/moderation/tests/fixtures/prompt_injection_attacks.json:
   - Append entry: {input: <full text>, expected_classification: "reject"|"escalate", category: <doxx|spam|injection|...>}

4. Run test corpus locally — must fail (proves new fixture is hard):
   .venv/Scripts/python.exe -m pytest apps/moderation/tests/test_pipeline.py::test_attack_corpus

5. Patch the pipeline. Decide layer:
   - Pattern detectable deterministically → add Layer 1 regex/heuristic in
     apps/moderation/services/layer1_deterministic.py
   - LLM rubric needs sharpening → update apps/moderation/services/prompts/layer2_classifier.txt
     and add example to few-shot section
   - Parser tolerated bad output → tighten apps/moderation/services/injection_guard.py

6. Re-run corpus locally — must pass.

7. Deploy patch.
   uv run pytest && deploy

8. Retroactive scan over the last 24h of approved content:
   .venv/Scripts/python.exe manage.py rescan_moderation --since=24h --layer=all

9. Process any newly-flagged items via Layer 3 mod queue.

10. If user-visible incident (e.g., bad content was on public surface long enough):
    - C posts public statement using template (Section 8).
    - Email affected users.

11. Postmortem.
```

**Public statement template**

```
On <date>, our content moderation system briefly approved a piece of user-generated content
that violated our policies. The item was removed within <duration> of being detected.
We have updated our automated and human review systems to prevent recurrence.
If you encountered the content and have concerns, please contact security@<domain>.
```

### 4.4 License-fraud event

**Indicators** — duplicate-license signal fires (same WA license # → two accounts); impersonated realtor reports via security@; ARELLO re-verify shows status mismatch.

**Steps (SEV-2)**

```
1. Identify all accounts touching the license:
   >>> from apps.accounts.models import RealtorProfile, LicenseCheck
   >>> license_no = "<wa_license>"
   >>> profiles = RealtorProfile.objects.filter(license_number=license_no)
   >>> for p in profiles:
   ...     print(p.user.email, p.verified_at, p.status)

2. Pull all LicenseCheck rows for this license (history):
   >>> LicenseCheck.objects.filter(license_number=license_no).order_by('created_at')

3. Trigger fresh ARELLO verify:
   >>> from apps.accounts.services.arello import ARelloClient
   >>> client = ARelloClient()
   >>> result = client.verify(license_no, force=True)
   >>> print(result.raw_response)

4. Compare ARELLO ground truth (legal name + brokerage + status) against each
   account's signup data. The non-matching account is the impostor.

5. Revoke verified-realtor badge on impostor:
   >>> impostor = RealtorProfile.objects.get(user__email="<impostor>")
   >>> impostor.status = "revoked"
   >>> impostor.revoked_reason = "License fraud — incident <id>"
   >>> impostor.save()
   Public-facing badge disappears immediately (cached for <60s).

6. Lock impostor account pending investigation:
   >>> impostor.user.is_active = False
   >>> impostor.user.save()

7. Notify legitimate license holder via email of dispute resolution.

8. Determine regulatory disclosure threshold:
   - If <10 affected users on impostor's content → internal documentation only.
   - If 10+ affected users OR consumer harm (e.g., a sale processed via impostor's
     contact info) → WA Department of Licensing referral.
     Contact: WA DOL Real Estate Division (Section 12).

9. Public statement only if user complaints or media inquiry. Default: do not
   broadcast — disclosing teaches attackers.

10. Postmortem; update fraud signals in apps/accounts/signals.py if pattern is novel.
```

### 4.5 AI tool spend runaway

**Indicators** — Gemini billing alert >2x baseline; Sentry spike of `tools.tasks.run_*`; Better Stack uptime check showing extreme p99 on AI endpoints; per-user counter shows abnormal volume.

**Steps (SEV-2)**

```
1. INSTANT kill via feature flag:
   In Django shell or operator dashboard:
   >>> from waffle.models import Switch
   >>> Switch.objects.update_or_create(name='ai_furniture_remover', defaults={'active': False})
   >>> Switch.objects.update_or_create(name='ai_description_writer', defaults={'active': False})
   Frontend hides tool entry points within 60s of cache TTL.

2. Identify abuse pattern:
   SELECT user_id, COUNT(*), MIN(created_at), MAX(created_at)
   FROM tools_aiusage
   WHERE created_at > NOW() - INTERVAL '24 hours'
   GROUP BY user_id
   ORDER BY 2 DESC LIMIT 20;

3. If single-user abuse, lock that user:
   >>> u = User.objects.get(id=<user_id>)
   >>> u.is_active = False
   >>> u.save()

4. If distributed (botnet), block IP ranges at Cloudflare:
   Cloudflare dashboard → Security → WAF → custom rule.
   Match condition: IP source ASN, country, or specific CIDR observed in
   accesslog query:
   SELECT ip_address, COUNT(*) FROM tools_aiusage_log
   WHERE created_at > NOW() - INTERVAL '6 hours'
   GROUP BY ip_address ORDER BY 2 DESC LIMIT 50;

5. If suspect Gemini key leaked:
   Rotate Gemini key per Section 5.

6. Refund flow for legitimate users mid-task:
   >>> from apps.tools.models import AIUsage
   >>> stuck = AIUsage.objects.filter(state='running', created_at__lt=...)
   >>> for u in stuck:
   ...     u.state = 'failed_refunded'
   ...     u.save()
   Tool re-enables with credit refund visible in user account.

7. Identify root cause (loop bug? attacker payload?). Patch + deploy.

8. Re-enable tools via feature flag once spend cap (Sprint 2 control) is in place.

9. Postmortem covering: detection time, kill time, total cost incurred, refund total.
```

### 4.6 Postgres incident (corruption / data loss)

**Indicators** — Sentry repeated DB errors, Railway PG status alarm, replication lag, integrity check failure, manual operator error.

**Steps (SEV-1)**

```
1. Halt all write traffic immediately. Set the entire site read-only:
   In operator dashboard → Maintenance → "Read-only mode" toggle ON.
   This sets a global flag the API checks; non-GET requests respond 503 with
   maintenance page.

2. Snapshot current DB state for forensics (do NOT discard, even if corrupt):
   pg_dump $DATABASE_URL > /tmp/forensic_$(date -u +%Y%m%dT%H%M%SZ).sql

3. Identify last known good backup:
   - Railway PITR window (configured retention)
   - Daily R2 backup at gs://yakima-backups/postgres/YYYY-MM-DD/

4. Validate backup integrity in staging:
   railway environment use staging
   psql $STAGING_DATABASE_URL -c "DROP DATABASE yakimadb;"
   psql $STAGING_DATABASE_URL -c "CREATE DATABASE yakimadb;"
   psql $STAGING_DATABASE_URL < /path/to/backup.sql
   .venv/Scripts/python.exe manage.py check
   .venv/Scripts/python.exe manage.py runserver  # smoke test

5. If staging restore is sound, proceed to prod. RPO max = 24h.

6. Restore prod (this is destructive — IC must give explicit go):
   railway environment use production
   - Use Railway PITR if available (less data loss)
   - OR restore from R2 backup

7. After restore, replay audit log for missing window:
   - ActionLog and AccessLog from forensic snapshot covers gap.
   - Reconcile critical state changes (license verifications, mod decisions,
     account bans) by replaying ActionLog rows newer than restore point.
   - Document any unrecoverable losses.

8. Resume traffic: read-only OFF.

9. Public statement template (data loss):
   "On <date> we experienced a database incident affecting data created between
    <start> and <end>. Affected data: <list>. We have restored the database from
    backup. Specific affected accounts will receive direct email. We are taking
    additional measures to prevent recurrence."

10. Email per affected user: list specifically lost items.

11. Postmortem.
```

### 4.7 R2 outage

**Indicators** — Sentry image-load 5xx spike, r2.cloudflarestatus.com red, Better Stack image-CDN check failing.

**Steps (SEV-2)**

```
1. Confirm with R2 status page.

2. Activate fallback display logic:
   >>> Switch.objects.update_or_create(name='r2_fallback_mode', defaults={'active': True})
   Frontend renders placeholder image with text "media temporarily unavailable".

3. Disable upload endpoints:
   >>> Switch.objects.update_or_create(name='media_uploads', defaults={'active': False})
   Profile photo, AI tool input, vendor portfolio uploads return 503 with friendly message.

4. Update status page.

5. Wait for R2 recovery; do not migrate during outage.

6. On recovery, verify versioned objects intact (R2 versioning is the safety net):
   spot-check 20 random recent uploads via signed URL.

7. Re-enable uploads. Disable fallback flag.
```

### 4.8 Postmark deliverability collapse

**Indicators** — Postmark dashboard shows bounce rate >5%, complaint rate >0.1%; multiple users report missing email-OTP/password-reset; Spamhaus/Barracuda hit alert.

**Steps (SEV-2)**

```
1. Confirm Postmark suppression list growth via dashboard.

2. Inspect bounces / complaints for pattern:
   - Single-domain cluster (recipient blocking us)?
   - Shared-IP burn?
   - DMARC failure (DNS issue)?

3. If DNS issue:
   - Verify DKIM/SPF/DMARC TXT records in Cloudflare DNS.
   - re-publish if drift.

4. If sender reputation issue, failover to AWS SES (Sprint 6 prewire):
   - Set EMAIL_BACKEND=django_anymail.backends.amazon_ses.EmailBackend
   - Push deploy via Railway.
   - Verify SES domain identity is verified + warming.
   - Send test email; confirm delivery.

5. Public statement on status page:
   "We are experiencing email delivery delays. Affected: signup verification,
    password reset, lead notifications. Estimated resolution: <time>."

6. In-app banner on authenticated pages while degraded:
   "Email is currently delayed. If you need to reset your password, contact
    support@<domain>."

7. After recovery:
   - Switch back to Postmark only after sender reputation stabilizes (warmed
     IP, suppression list cleared).
   - Postmortem covering reputation event root cause.
```

### 4.9 Railway hosting outage

**Indicators** — Railway status page red, external uptime probes failing, DNS resolves but origin 502.

**Steps (SEV-1)**

```
1. Confirm: railway status, https://status.railway.app

2. If Railway-wide:
   - DNS swing to Cloudflare Pages maintenance page:
     In Cloudflare DNS, change A record for app.<domain> to point to maintenance worker.
     Cloudflare Pages already hosts a static maintenance/status page that pulls
     status from public status JSON.
   - Cloudflare cache TTL ≤ 60s for app.<domain> ensures fast swing back.

3. Public statement on status page (Cloudflare-hosted, independent of Railway):
   "Our hosting provider is experiencing an outage. We are monitoring and
    will restore service as soon as possible."

4. Reddit/Twitter heads-up.

5. On Railway recovery:
   - Verify origin healthy via direct curl.
   - DNS swing back.
   - Cloudflare cache purge.
   - Confirm functional via smoke tests.

6. v1.1 will deliver Fly.io secondary as warm failover. Until then, this runbook
   accepts an extended outage as residual risk.
```

### 4.10 Sentry / Better Stack outage

**Indicators** — alerts dry-up despite traffic; sentry.io status red.

**Steps (SEV-3)**

```
1. Verify outage with vendor status page.

2. Switch to manual monitoring:
   - Tail Railway logs via railway logs.
   - Run hourly checks against AccessLog/ActionLog for anomalies:

   .venv/Scripts/python.exe manage.py logreview --last 1h
   (custom command — Sprint 6)

3. Operator dashboard "manual incident mode" exposes:
   - Last 100 5xx responses with stack hash
   - Last 100 4xx by endpoint
   - Anomalous AccessLog patterns (per-user request rate)

4. If Better Stack down, fall back to email alerts from Cloudflare uptime.

5. Restore observability tools when vendor recovers; verify alert backfill.
```

---

## 5. Routine security operations

### 5.1 Key rotation cadence

| Key | Rotation | Procedure summary |
|---|---|---|
| `DJANGO_SECRET_KEY` | 90 days | Two-key zero-downtime window (5.1.1) |
| JWT signing key | 30 days (derived from `SECRET_KEY` salt) | On `SECRET_KEY` rotate, also bump `SIMPLE_JWT.SIGNING_KEY` salt; sliding window 24h |
| Postmark API token | 180 days | Generate new in Postmark, set `POSTMARK_TOKEN_NEW`, swap, verify, retire old |
| R2 access key | 90 days | Generate new in Cloudflare, dual-set `R2_KEY_PRIMARY/SECONDARY`, app reads both, swap, retire |
| ARELLO API key | 365 days (vendor constraint) | Coordinate with vendor; capability swap at midnight low-traffic |
| Gemini API key | 90 days | Generate new in GCP, dual-set, app uses primary, swap, retire; immediate-rotate on any abuse signal |
| Sentry DSN | On-incident only | If suspected disclosure or staff exit |
| TOTP `OTP_TOTP_KEY` (encryption-at-rest secret) | 365 days | Apply via `manage.py rotate_otp_keys` (custom command); re-encrypts existing TOTPDevice rows |

#### 5.1.1 `DJANGO_SECRET_KEY` rotation procedure

```
1. Generate new key (50+ random chars):
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

2. Set NEW key as SECRET_KEY, MOVE old to SECRET_KEY_FALLBACKS:
   Railway env:
     SECRET_KEY = <new>
     SECRET_KEY_FALLBACKS = ["<old>"]

3. Settings already read SECRET_KEY_FALLBACKS — Django verifies signed cookies
   against fallback during rotation window.

4. Deploy. Verify:
   - Existing sessions still work (read via fallback).
   - New sessions sign with new key.

5. After 7-day grace window (covers cookie max-age), remove fallback:
   SECRET_KEY_FALLBACKS = []

6. Document rotation in audit/key_rotation_log.md:
   <date> | DJANGO_SECRET_KEY | <fingerprint of new> | <fingerprint of old retired> | <operator>

7. JWT impact: SimpleJWT signing key derives from SECRET_KEY. Existing JWTs
   verified against fallback during window; refresh issues new tokens signed
   under new key.
```

### 5.2 Log review cadence

| Cadence | Activity | Owner |
|---|---|---|
| Daily | Mod queue clearance check (no item older than 24h) | Mod / Operator |
| Daily | Sentry triage (every error reviewed) | EL |
| Weekly | ActionLog spot-check: pick 5 random staff actions, validate against expected behavior, document in `audit/spot_check_YYYY-WW.md` | SL |
| Weekly | Mod queue audit: pick 20 random mod decisions, second-mod review for consistency | Operator |
| Monthly | AccessLog pattern review: per-staff browsing patterns, anomalous time-of-day, anomalous record-access volumes | SL |
| Monthly | Failed login pattern review (django-axes log): top 20 IPs, geo distribution, repeating usernames | SL |
| Quarterly | Full audit replay drill: pick 3 user accounts, reconstruct full action history from ActionLog, compare against current state | SL |

### 5.3 Dependency updates

| Activity | Cadence |
|---|---|
| Dependabot PRs | Weekly (auto) |
| `pip-audit` triage | Weekly |
| `npm audit` triage | Weekly |
| Manual review of major version bumps | Monthly |
| Patch SLA — critical CVE | 24 hours |
| Patch SLA — high CVE | 72 hours |
| Patch SLA — medium/low | Next sprint |

### 5.4 Backups

| Activity | Cadence | Owner |
|---|---|---|
| Postgres full dump → R2 | Daily, 03:00 UTC | Automated (Celery beat) |
| Postgres WAL archive | Hourly | Railway-managed |
| R2 versioning | Continuous | R2-managed |
| Restore drill (dev) | Weekly | EL |
| Full pipeline restore drill (full env spin-up from cold) | Monthly | EL |
| Backup integrity check | Daily (automated checksum) | Automated |
| Off-site copy verification | Monthly | EL |

### 5.5 Penetration testing

- Annual external pen test (vendor TBD; OWASP ASVS L2 target).
- On-major-feature launch (Phases 3, 5 specifically — AI tools and marketplace). Internal red-team pass first; external if budget allows.
- Findings → `docs/pentest/YYYY-<vendor>.md`. Critical → SEV-1 fix; High → next sprint; Medium → backlog.

### 5.6 Threat-model review

- Every 6 months scheduled review.
- Triggered review on any of: new external integration, new role, new data type, new UGC surface, change to auth or moderation pipeline.
- Output: revised THREAT-MODEL.md, RISK-REGISTER.md scoring updates.

---

## 6. Audit replay procedure

To reconstruct exactly what happened to a record:

```sql
-- Given a target row, e.g. content_post.id = 42
-- 1. Find every ActionLog row referencing it:
SELECT
    al.id,
    al.created_at,
    u.email AS actor,
    al.ip_address,
    al.action,
    al.payload_json
FROM audit_actionlog al
JOIN auth_user u ON al.user_id = u.id
WHERE al.model = 'content.Post'
  AND al.instance_id = '42'
ORDER BY al.created_at ASC;

-- 2. Reconstruct field-by-field state by walking payload_json diffs forward:
-- Each row has shape:
--   {"action": "create"|"update"|"delete",
--    "before": {field: value, ...} or null,
--    "after":  {field: value, ...} or null}
-- Apply each diff to a pristine state to reach final.

-- 3. Cross-reference AccessLog for context:
SELECT
    accesslog.created_at, accesslog.path, accesslog.method, accesslog.status_code, u.email
FROM audit_accesslog accesslog
JOIN auth_user u ON accesslog.user_id = u.id
WHERE accesslog.path LIKE '%/posts/42%'
ORDER BY accesslog.created_at ASC;

-- 4. Validate: ActionLog should match ROW count of UPDATE statements applied.
--    Mismatch = something bypassed the signal (investigate immediately).
```

For systematic replay across many records, a Django management command:

```bash
.venv/Scripts/python.exe manage.py audit_replay --model content.Post --instance 42
```

(custom command, Sprint 4 deliverable)

---

## 7. Data subject request handling

### 7.1 Access (GDPR-shaped, voluntary)

Although not formally GDPR-subject (US-only userbase v1), apply principles.

```
1. Verify requester via TOTP-backed email link (not just account email).

2. Run export:
   .venv/Scripts/python.exe manage.py export_user_data --user <id> --output /tmp/user_<id>.zip

   Contents:
     - profile.json (email, name, dates, license info)
     - posts/ (markdown files, one per UGC item)
     - leads/ (lead records where user is buyer or vendor)
     - accesslog.csv (last 12 months — pruned beyond)
     - actionlog.csv (last 12 months on user's records)
     - ai_tool_inputs/ (links to R2 objects with signed URLs valid 7 days)

3. Send via Postmark with download link valid 7 days (signed URL).

4. SLA: 30 days. Most requests turnaround < 7 days.
```

### 7.2 Deletion (Right to be forgotten)

```
1. Verify requester (same as 7.1).

2. Run staged deletion:
   .venv/Scripts/python.exe manage.py delete_user --user <id> --confirm

   Effects:
     - User record: hard-delete (auth_user row gone)
     - UGC: replace text with "[removed]", set author = null, retain timestamps
       and FKs (preserves thread structure for other users)
     - LicenseCheck: retain (regulatory requirement, anonymized)
     - ActionLog: retain (immutable; user_id replaced with NULL after grace
       period of 90 days; audit integrity preserved by hash chain — Sprint 8)
     - AccessLog: retain 12 months from event, then auto-pruned anyway
     - R2 objects (uploaded photos): hard-deleted from R2 + versions purged
     - Email: opt-out + unsubscribe across all lists

3. Confirm with user via final email pre-deletion (24h cooldown).

4. Document deletion in deletion_log table (id only, no email).
```

### 7.3 Rectification

For factual corrections (e.g., name change, brokerage transfer):

```
1. User submits via account → settings.

2. License re-verify required if it touches realtor data.

3. Operator approval if change might be fraud (e.g., new brokerage doesn't match ARELLO).

4. ActionLog records the change automatically.
```

---

## 8. Breach notification

### 8.1 Thresholds

| Trigger | Notification |
|---|---|
| Any unauthorized access to PII (email + name +) for any user | WA RCW 19.255 process |
| 500+ users affected | WA AG notification within 30 days; user notification "without unreasonable delay" |
| Sensitive data class accessed (license number with name + address) | Treat as 19.255-trigger; same notification |
| User credentials confirmed leaked | User notification within 7 days; password reset force |
| Audit log integrity compromised | Internal SEV-1; no automatic public disclosure unless tied to user-data breach |
| Moderation bypass causing harmful UGC live for >1h | Affected-user-only notification |
| AI tool output containing protected-class language (FHA) | User notification + retraction; HUD coordination if pattern |

### 8.2 WA RCW 19.255 outline

WA breach-notification statute requires notice to affected residents "without unreasonable delay" and to AG when 500+ residents affected. Apply principles even when below threshold.

### 8.3 Public statement template — confirmed breach

```
Subject: Important security notice for your Yakima Real Estate Hub account

Dear <user>,

On <date>, we detected unauthorized access to a portion of our system. Our
investigation indicates that the following information of yours may have been
exposed: <specific fields — e.g., email address, hashed password, full name>.

We do NOT have evidence of <e.g., financial information, government IDs> being
accessed. Passwords were stored using <Argon2id>, an industry-standard hashing
algorithm.

What we have done:
- Contained the incident on <date>.
- Forced password resets on all potentially-affected accounts.
- Engaged independent security experts to verify remediation.
- Reported to <WA Attorney General | WA DOL | etc., as applicable>.

What you should do:
- Reset your password if you have not already done so.
- Enable two-factor authentication if you have not already done so.
- Change your password on any other site where you may have used the same one.
- Watch for phishing emails impersonating us.

We deeply regret this incident. For questions, contact security@<domain>.

— Yakima Real Estate Hub Security
```

### 8.4 Public statement template — moderation bypass

(See runbook 4.3.)

---

## 9. Forensic evidence collection

When responding to any SEV-1 or SEV-2:

```
1. Snapshot environment:
   railway logs -n 1000 > /tmp/inc_<id>_railway.log
   pg_dump --schema-only $DATABASE_URL > /tmp/inc_<id>_schema.sql

2. Capture state of relevant tables:
   psql $DATABASE_URL -c "COPY (SELECT * FROM audit_actionlog WHERE created_at > NOW() - INTERVAL '24 hours') TO STDOUT WITH CSV HEADER" > /tmp/inc_<id>_actionlog.csv
   (and accesslog, moderation_decision, license_check as relevant)

3. Capture Sentry events:
   Use Sentry CLI: sentry-cli events list --project yakima --since 24h > /tmp/inc_<id>_sentry.json

4. Hash artifacts:
   sha256sum /tmp/inc_<id>_*.{log,sql,csv,json} > /tmp/inc_<id>_hashes.txt

5. Upload artifacts to forensic R2 bucket (write-once, audit-only):
   rclone copy /tmp/inc_<id>_*.* yakima-forensics:incidents/inc_<id>/

6. Create incident folder:
   docs/incidents/<date>-<slug>/
     timeline.md
     evidence/
     postmortem.md (built later)
```

Chain of custody: record every command run with timestamp + operator + output file.

---

## 10. On-call rotation

For v1 (solo operation):

- Primary: Founder.
- Backup: Pre-arranged contractor (named in succession contract, sealed envelope arrangement).
- Pager: PagerDuty configured for Sentry + Better Stack alerts (paid tier required).
- Hours: 24/7 for SEV-1 only; SEV-2 business hours acceptable.

When second engineer joins:

- Weekly rotation, primary + secondary.
- 2-week notice for vacation; secondary covers.
- Quarterly chaos drill (game day) with simulated SEV-1.

---

## 11. Contacts

| Vendor / Authority | Purpose | Contact |
|---|---|---|
| Cloudflare support | CDN, DNS, R2, WAF | dashboard support; status: cloudflarestatus.com; phone: enterprise tier only |
| Railway support | Hosting | help@railway.app; status: status.railway.app |
| Postmark support | Email | support@postmarkapp.com; status: status.postmarkapp.com |
| Sentry support | Error monitoring | dashboard support; status: status.sentry.io |
| Better Stack support | Uptime + logs | hello@betterstack.com |
| ARELLO support | License verification | support@arello.com (vendor SLA: 1 business day) |
| Google Cloud / Gemini support | AI provider | console support cases; status: status.cloud.google.com |
| WA Department of Licensing — Real Estate Division | License-fraud referral, regulatory | 360-664-6500; realestate@dol.wa.gov; PO Box 9015, Olympia WA 98507 |
| WA Attorney General — Consumer Protection | Breach notification trigger | atg.wa.gov; 1-800-551-4636 |
| Federal Trade Commission | CAN-SPAM / consumer protection | reportfraud.ftc.gov |
| HUD Fair Housing | FHA complaint coordination | 1-800-669-9777; fhcomplaints@hud.gov |
| Pen test vendor | Annual + on-feature | TBD pre-launch |
| Legal counsel | Defamation, breach disclosure, ADA, FHA | TBD on retainer pre-launch |
| Cyber insurance | Incident coverage | TBD (deferred to post-launch as opex) |

---

## 12. Appendix — useful commands

### 12.1 Last 50 logins for a user

```python
.venv/Scripts/python.exe manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from apps.audit.models import AccessLog
>>> u = get_user_model().objects.get(email="<email>")
>>> AccessLog.objects.filter(user=u, path="/api/auth/login").order_by('-created_at')[:50].values('created_at', 'ip_address', 'user_agent', 'status_code')
```

### 12.2 All staff writes in last 24h

```sql
SELECT al.created_at, u.email, al.model, al.instance_id, al.action
FROM audit_actionlog al
JOIN auth_user u ON al.user_id = u.id
WHERE u.is_staff = true
  AND al.created_at > NOW() - INTERVAL '24 hours'
ORDER BY al.created_at DESC;
```

### 12.3 Failed-login top offenders (last 24h)

```sql
SELECT ip_address, COUNT(*) AS attempts, COUNT(DISTINCT username) AS distinct_usernames
FROM axes_accessattempt
WHERE attempt_time > NOW() - INTERVAL '24 hours'
GROUP BY ip_address
ORDER BY attempts DESC
LIMIT 20;
```

### 12.4 Pipeline approve/reject ratio (last 7d)

```sql
SELECT classification, COUNT(*)
FROM moderation_decision
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY classification;
```

### 12.5 License verification outcomes (last 30d)

```sql
SELECT
    DATE(created_at) AS day,
    COUNT(*) FILTER (WHERE outcome = 'verified') AS verified,
    COUNT(*) FILTER (WHERE outcome = 'not_found') AS not_found,
    COUNT(*) FILTER (WHERE outcome = 'inactive') AS inactive,
    COUNT(*) FILTER (WHERE outcome = 'error') AS error
FROM accounts_licensecheck
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY day DESC;
```

### 12.6 Mod queue depth and oldest item

```sql
SELECT
    COUNT(*) AS pending,
    MIN(created_at) AS oldest_item
FROM moderation_decision
WHERE classification = 'escalate'
  AND resolved_at IS NULL;
```

### 12.7 Force-revoke all sessions for one user

```python
.venv/Scripts/python.exe manage.py shell
>>> from django.contrib.sessions.models import Session
>>> from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
>>> from django.contrib.auth import get_user_model
>>> u = get_user_model().objects.get(email="<email>")
>>> # Sessions
>>> for s in Session.objects.all():
...     if s.get_decoded().get('_auth_user_id') == str(u.id):
...         s.delete()
>>> # JWT refresh tokens
>>> for tok in OutstandingToken.objects.filter(user=u):
...     BlacklistedToken.objects.get_or_create(token=tok)
```

### 12.8 Spot moderation pipeline performance regressions

```bash
.venv/Scripts/python.exe -m pytest apps/moderation/tests/test_pipeline.py::test_attack_corpus -v
.venv/Scripts/python.exe -m pytest apps/moderation/tests/test_pipeline.py::test_layer1_latency_budget -v
.venv/Scripts/python.exe manage.py moderation_stats --window=7d
```

### 12.9 Verify HSTS / security headers

```bash
curl -sI https://<domain>/ | grep -iE 'strict-transport|content-security|x-frame|x-content|referrer'
```

### 12.10 Manual incident timer / drill

```bash
.venv/Scripts/python.exe manage.py incident_drill --scenario sev1-prompt-injection --dry-run
```

(Sprint 7 deliverable — table-top exercise harness producing report on response timing and gap.)
