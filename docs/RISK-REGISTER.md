# Risk Register — Yakima Real Estate Hub

| Field | Value |
|---|---|
| Version | 1.0 |
| Date | 2026-05-03 |
| Owner | Yakima Real Estate Hub Security |
| Classification | Internal |
| Review cadence | Quarterly + on architecture change |
| Cross-references | `docs/THREAT-MODEL.md`, `docs/SECURITY-PLAYBOOK.md`, `docs/SRS.md`, `docs/SAD.md`, `docs/ICD.md`, `docs/MTP.md`, `docs/RUNBOOK.md` |

## 1. Scoring methodology

| Likelihood | Description | Score |
|---|---|---|
| Very Low | <1% in 12 months | 1 |
| Low | 1–10% | 2 |
| Medium | 10–40% | 3 |
| High | 40–80% | 4 |
| Very High | >80% | 5 |

| Impact | Description | Score |
|---|---|---|
| Insignificant | <$1k loss, no user harm, no PR damage | 1 |
| Minor | <$10k, <100 users affected, recoverable in <8h | 2 |
| Moderate | <$100k, <1k users, recoverable in <48h, local press | 3 |
| Major | <$1M, regulatory notification, multi-day outage, regional press | 4 |
| Catastrophic | >$1M, dissolution-grade, national press, lawsuit-bait | 5 |

Risk score = Likelihood × Impact (1–25). Tier: 1–4 Low, 5–9 Medium, 10–15 High, 16–25 Critical.

Mitigation effort levels referenced: P (preventive — reduces likelihood), R (reactive — reduces impact when fired).

## 2. Risks

### R-001 ARELLO API outage during signup surge

| Field | Value |
|---|---|
| Category | Technical / Operational |
| Description | ARELLO is a single upstream for WA license verification. Outage during a Yakima MLS launch event or Reddit-driven traffic spike blocks all realtor signups. Verified-realtor badge is a core trust contract; degraded checks risk fraud. |
| Likelihood (pre) | Medium (3) — third-party legacy SaaS, irregular maintenance windows |
| Impact (pre) | Moderate (3) — signup conversion drops, trust contract degraded |
| Score (pre) | 9 |
| Triggers | ARELLO 5xx >1% over 5min; ARELLO p95 >10s; SSL cert renewal failures upstream |
| Mitigation (P) | Circuit breaker (Sprint 2): 5 consecutive failures opens circuit for 60s. Async retry with jitter on transient 5xx. Pre-flight health probe in `apps/operations/healthz.py`. |
| Mitigation (R) | Auto-queue verifications in `LicenseCheck` with `pending` state; user receives "verification in progress" badge (read-only, no badge granted); on recovery, Celery beat reprocesses backlog. Operator can manual-verify against state DOL website with audit comment. |
| Residual likelihood | Medium (3) |
| Residual impact | Minor (2) |
| Residual score | 6 |
| Owner | Backend lead |
| Status | Open (circuit breaker pending Sprint 2) |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §License-fraud deep-dive; SECURITY-PLAYBOOK runbook 4; `apps/accounts/services/arello.py`; ADR-0002 |

### R-002 Gemini API outage or pricing 2x increase

| Field | Value |
|---|---|
| Category | Technical / Strategic |
| Description | Google Gemini is the AI substrate for both moderation (Layer 2) and AI tools (furniture remover, description writer). Provider outage halts moderation queue and AI lead magnets; surprise pricing change blows monthly budget. |
| Likelihood (pre) | Medium (3) — Google APIs have multi-hour quarterly incidents; pricing changes once/year |
| Impact (pre) | Major (4) — moderation degradation = unsanitized UGC publishes; cost blowout = opex hit |
| Score (pre) | 12 |
| Triggers | Gemini 5xx >0.5%; quota-exceeded errors; billing alert >2× baseline daily |
| Mitigation (P) | Layer-1 deterministic moderation (regex + bleach + entropy heuristics) holds line during Gemini outage — content stays in `pending_review` not auto-published. Daily Gemini spend cap (Sprint 2) feature-flag-kills tools at threshold. Multi-key rotation. Provider abstraction in `apps/moderation/services/llm_client.py` allows swap to Claude/OpenAI in <1d. |
| Mitigation (R) | Mod queue grows; human moderators triage. AI tools display "temporarily unavailable" banner. Comms template prepared. |
| Residual likelihood | Medium (3) |
| Residual impact | Moderate (3) |
| Residual score | 9 |
| Owner | Backend lead |
| Status | Open (spend cap pending Sprint 2) |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Gemini integration; SECURITY-PLAYBOOK runbook 5; ADR-0003 |

### R-003 Prompt injection bypassing 3-layer pipeline

| Field | Value |
|---|---|
| Category | Technical / Regulatory |
| Description | Adversary crafts UGC payload that gets Layer 2 Gemini classifier to emit `approved` JSON despite malicious content (e.g., doxxing, Fair Housing Act violation, scam link). If Layer 3 human queue does not catch, content publishes. |
| Likelihood (pre) | High (4) — active adversarial pressure expected from spam economy |
| Impact (pre) | Major (4) — defamation, FHA fines, brand damage |
| Score (pre) | 16 |
| Triggers | Pipeline approval rate spike >30% above baseline; user reports of clearly violating content surfacing live |
| Mitigation (P) | 3-layer architecture, fail-closed parser (`apps/moderation/services/injection_guard.parse_classifier_response`), 30+ adversarial fixtures with 5+/phase target, deterministic Layer 1 catches obvious injection markers, classifier output schema-validated, instruction segregation in prompt template. |
| Mitigation (R) | Capture failure as fixture, hot-add to `prompt_injection_attacks.json`, trigger retroactive scan over last 24h via `moderation.tasks.rescan_window`, redeploy classifier worker. Public statement template. |
| Residual likelihood | Medium (3) |
| Residual impact | Moderate (3) |
| Residual score | 9 |
| Owner | Moderation lead |
| Status | Mitigated (residual managed via fixture growth) |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Prompt injection deep-dive; SECURITY-PLAYBOOK runbook 3; `apps/moderation/services/pipeline.py`; `apps/moderation/tests/fixtures/prompt_injection_attacks.json` |

### R-004 License-fabrication attack

| Field | Value |
|---|---|
| Category | Regulatory / Operational |
| Description | Adversary signs up using a real WA license number scraped from public DOL records, posing as that licensee. Verified-realtor badge granted under another professional's identity. Liability + defamation risk. |
| Likelihood (pre) | Medium (3) — public DOL data + phishable email = low-skill attack |
| Impact (pre) | Major (4) — impersonation lawsuit, regulatory disclosure |
| Score (pre) | 12 |
| Triggers | License number used twice across distinct accounts; brokerage mismatch in ARELLO response vs claimed; reports from impersonated realtor |
| Mitigation (P) | ARELLO match requires legal name + brokerage + license + active status. Email-of-record cross-check against ARELLO-listed broker contact (Phase 2). Monthly re-verify cron rotates `LicenseCheck` rows. Same-license-different-account detection in `apps/accounts/signals.duplicate_license_check`. |
| Mitigation (R) | Operator dashboard "license dispute" workflow → revoke badge → notify both parties → audit trail. WA DOL referral if criminal indicators. |
| Residual likelihood | Low (2) |
| Residual impact | Moderate (3) |
| Residual score | 6 |
| Owner | Compliance / Operator |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §License-fraud deep-dive; SECURITY-PLAYBOOK runbook 4; ADR-0002 |

### R-005 Vendor review fraud

| Field | Value |
|---|---|
| Category | Operational / Strategic |
| Description | Vendor on marketplace fabricates leads (or solicits fake leads from sock puppets), then writes 5-star reviews against those leads to inflate score. Erodes marketplace trust. |
| Likelihood (pre) | High (4) — universal Fiverr-shaped marketplace pattern |
| Impact (pre) | Moderate (3) — trust collapse if undetected |
| Score (pre) | 12 |
| Triggers | Lead-to-review velocity outliers; IP/UA reuse across reviewers; perfect 5-star clusters; new-account reviewers with single-vendor history |
| Mitigation (P) | Reviews tied to `Lead` records (1:1, no orphans), reviewer must be verified-email user with ≥7 day account age, vendor cannot self-review (FK constraint). Operator dashboard surfaces velocity anomalies. |
| Mitigation (R) | Mass-invalidate reviews under suspicious pattern, recalculate aggregate scores, suspend vendor pending review, public takedown notice on marketplace listing. |
| Residual likelihood | Medium (3) |
| Residual impact | Minor (2) |
| Residual score | 6 |
| Owner | Marketplace lead |
| Status | Open (pattern detection pending Phase 5) |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Review-fraud deep-dive; ADR-0004 |

### R-006 Credential stuffing on /accounts/login/

| Field | Value |
|---|---|
| Category | Technical |
| Description | Bot operator runs breached username/password lists against login endpoint. Successful matches yield account takeover (realtor accounts particularly valuable for impersonation). |
| Likelihood (pre) | Very High (5) — universal threat for any auth endpoint |
| Impact (pre) | Moderate (3) — account compromise, badge abuse |
| Score (pre) | 15 |
| Triggers | django-axes lockout volume spike; geo-distributed login failures; same-password-multiple-accounts pattern |
| Mitigation (P) | django-axes 5-fail-in-5min IP+username lockout. Argon2id password hashing. Email-OTP enforced for new IP+device. CAPTCHA after 3 failures. Have-I-Been-Pwned integration on signup + password change (Sprint 3). HTTPS-only + httpOnly+SameSite=Strict cookies. |
| Mitigation (R) | Force password reset for impacted accounts, revoke all JWT refresh tokens (`SimpleJWT` blacklist), notify user, ActionLog audit. |
| Residual likelihood | Medium (3) |
| Residual impact | Minor (2) |
| Residual score | 6 |
| Owner | Backend lead |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Auth subsystem STRIDE; SECURITY-PLAYBOOK runbook 1 |

### R-007 UGC doxxing event

| Field | Value |
|---|---|
| Category | Regulatory / Operational |
| Description | Forum or comment author posts another resident's home address, phone, employer location, or daily routine — either in revenge or to harass. Yakima is a small market; doxxing risk is concrete. |
| Likelihood (pre) | High (4) — small community + heated real estate disputes |
| Impact (pre) | Major (4) — physical harm risk, lawsuit, regulatory complaint |
| Score (pre) | 16 |
| Triggers | PII regex matches (US addresses, phone numbers, SSN-shaped); user reports; moderator flag |
| Mitigation (P) | Layer 1 deterministic regex for US addresses (street + city + state + zip), phone, email, SSN; Layer 2 Gemini classifier with explicit doxxing rubric; Layer 3 human queue for any high-risk classification. Public-figure exception for properly licensed realtors' own publication. |
| Mitigation (R) | One-click takedown on operator dashboard, hard-redact from public DB (replace with `[removed]`), preserve original in moderation audit (encrypted), notify victim if identified, escalate to law enforcement if threats. WA Anti-Harassment Order coordination if requested. |
| Residual likelihood | Medium (3) |
| Residual impact | Moderate (3) |
| Residual score | 9 |
| Owner | Moderation lead |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Moderation subsystem STRIDE; SECURITY-PLAYBOOK breach notification |

### R-008 Compromised moderator account

| Field | Value |
|---|---|
| Category | Operational |
| Description | Mod credentials phished or reused from breach. Attacker mass-removes legitimate content or mass-suspends real users to discredit platform or harass specific users. |
| Likelihood (pre) | Low (2) — mod count small, MFA enforced |
| Impact (pre) | Major (4) — mass content destruction, public trust collapse |
| Score (pre) | 8 |
| Triggers | ActionLog volume spike from single mod; non-business-hours mod activity from new IP; mod actions targeting same user repeatedly |
| Mitigation (P) | django-otp TOTP enforced for `is_staff`. Per-mod rate limit on suspend/remove endpoints (50/hour, hard cap). Suspicious-pattern alerting on operator dashboard. Mod onboarding training + signed conduct policy. |
| Mitigation (R) | Operator one-click "freeze mod" → revoke session + JWT + lock TOTP. Rollback last N actions via ActionLog replay. ActionLog forensic audit. Force re-enrollment of TOTP. Public statement if user-visible. |
| Residual likelihood | Low (2) |
| Residual impact | Moderate (3) |
| Residual score | 6 |
| Owner | Operator |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Audit subsystem STRIDE; SECURITY-PLAYBOOK runbook 2; `apps/audit/signals.py` |

### R-009 Compromised admin/superadmin account

| Field | Value |
|---|---|
| Category | Operational |
| Description | Superadmin credential compromised via phishing, malware, or third-party breach. Attacker has full DB write access through Django admin or Postgres direct. |
| Likelihood (pre) | Low (2) — strict controls in place |
| Impact (pre) | Catastrophic (5) — total platform compromise, all user data at risk |
| Score (pre) | 10 |
| Triggers | /admin/ access from non-allowlisted IP (already blocked, alert fires); ActionLog superuser write outside business hours; failed TOTP volume; Sentry 4xx spike on /admin/login/; Postmark sees password-reset email to admin email |
| Mitigation (P) | `AdminIPAllowlistMiddleware` blocks /admin/ from non-allowlist. django-otp TOTP enforced. Hardware key (FIDO2) recommended for superadmin (Sprint 3). 30-day password rotation reminder. Admin email on dedicated domain not used elsewhere. No password manager auto-fill on admin URL. |
| Mitigation (R) | Cut admin via DB-level flag (`auth_user.is_active = false`) executed from Postgres direct. Rotate `DJANGO_SECRET_KEY` (revokes all sessions). Force password reset all is_staff users. ActionLog complete audit of past 30 days. Restore from clean backup if data tampering detected. WA breach notification if user data accessed. |
| Residual likelihood | Very Low (1) |
| Residual impact | Major (4) |
| Residual score | 4 |
| Owner | Compliance / Operator |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Auth subsystem; SECURITY-PLAYBOOK runbook 2; `apps/admin_tools/middleware.py` |

### R-010 Postgres data loss / corruption

| Field | Value |
|---|---|
| Category | Technical |
| Description | DB corruption from disk failure, bad migration, or manual operator error. Recent UGC, audit log, license-check rows lost between backup intervals. |
| Likelihood (pre) | Low (2) — Railway-managed PG with replication |
| Impact (pre) | Major (4) — audit log loss = compliance failure |
| Score (pre) | 8 |
| Triggers | PG WAL replay errors; replication lag >5min; backup integrity check failure; storage alert |
| Mitigation (P) | Daily automated `pg_dump` to Cloudflare R2 (different region than Railway). Migration safety review before merge. PITR enabled on Railway tier. WAL archived hourly. Monthly full-pipeline restore drill. |
| Mitigation (R) | Restore from latest verified backup (RPO 24h, RTO 4h), reconcile audit log gaps via Sentry/Postmark logs, public statement if user-visible data lost, process refunds (lead credits if any). |
| Residual likelihood | Very Low (1) |
| Residual impact | Moderate (3) |
| Residual score | 3 |
| Owner | Backend lead |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | SECURITY-PLAYBOOK runbook 6; RUNBOOK §Backups |

### R-011 Cloudflare R2 outage or data loss

| Field | Value |
|---|---|
| Category | Technical |
| Description | R2 hosts media (property photos, processed AI tool output, profile images). Outage = images broken site-wide; data loss = user-uploaded property photos gone. |
| Likelihood (pre) | Low (2) — R2 has 11-9s durability claim |
| Impact (pre) | Moderate (3) — degraded UX, user-uploaded content unrecoverable |
| Score (pre) | 6 |
| Triggers | R2 5xx spike; CDN cache miss with origin failures; r2.cloudflarestatus.com red |
| Mitigation (P) | R2 versioning enabled (90-day retention). Originals preserved separate from processed outputs. Cross-region replication for paid-tier media (Sprint 4). User-side upload retry with local cache. |
| Mitigation (R) | Fallback display logic (placeholder image, "media temporarily unavailable" banner). Feature-flag image-upload disable. R2 versioning rollback if corruption. Sentry alerts. |
| Residual likelihood | Very Low (1) |
| Residual impact | Minor (2) |
| Residual score | 2 |
| Owner | Backend lead |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | SECURITY-PLAYBOOK runbook 7 |

### R-012 Postmark deliverability collapse

| Field | Value |
|---|---|
| Category | Technical / Operational |
| Description | Yakima Real Estate Hub sender domain blacklisted (spam complaint cluster, DMARC failure, or shared-IP burn). Email-OTP, password resets, lead notifications stop reaching users. Effectively bricks signup + recovery flows. |
| Likelihood (pre) | Medium (3) — small senders are vulnerable |
| Impact (pre) | Major (4) — signup blocked, account recovery blocked |
| Score (pre) | 12 |
| Triggers | Postmark bounce rate >5%, spam complaint rate >0.1%, blacklist check (e.g., Spamhaus) hit |
| Mitigation (P) | DKIM + SPF + DMARC strict aligned. Dedicated IP. Suppression list management. Bounce-handling webhook in `apps/accounts/views/postmark_webhook.py`. Engagement-based throttling on lead emails. Pre-warm IP. |
| Mitigation (R) | Failover to AWS SES (configured but inactive); switch via `EMAIL_BACKEND` env flip. Public statement template. User comms via in-app banner during email outage. WA DOL contact through phone for compliance reporting if needed. |
| Residual likelihood | Low (2) |
| Residual impact | Moderate (3) |
| Residual score | 6 |
| Owner | Backend lead |
| Status | Open (SES failover pending Sprint 6) |
| Last reviewed | 2026-05-03 |
| Linked controls | SECURITY-PLAYBOOK runbook 8 |

### R-013 Sentry/Better Stack outage during incident

| Field | Value |
|---|---|
| Category | Operational |
| Description | Active SEV-1 incident coincides with monitoring vendor outage. Lose error visibility precisely when needed. |
| Likelihood (pre) | Low (2) — both vendors are reliable but compounding event possible |
| Impact (pre) | Moderate (3) — slower MTTR, blind incident response |
| Score (pre) | 6 |
| Triggers | Sentry status page red; Better Stack heartbeat missing; alerts dry-up despite traffic |
| Mitigation (P) | Local structured logging always written to Postgres `audit_actionlog` table regardless of Sentry state. Railway native log retention (7d). Healthz endpoint independent of Sentry. |
| Mitigation (R) | Manual log review via `python manage.py logreview --last 4h` (custom command, Sprint 6). SQL queries against `actionlog`/`accesslog`. Postgres slow-query log. Operator dashboard "manual incident mode" exposes raw recent error tails from DB. |
| Residual likelihood | Low (2) |
| Residual impact | Minor (2) |
| Residual score | 4 |
| Owner | Backend lead |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | SECURITY-PLAYBOOK runbook 10 |

### R-014 Railway hosting outage

| Field | Value |
|---|---|
| Category | Technical |
| Description | Railway region or platform outage. Site fully down. v1 has no multi-region failover. |
| Likelihood (pre) | Medium (3) — Railway has occasional multi-hour outages |
| Impact (pre) | Major (4) — full unavailability |
| Score (pre) | 12 |
| Triggers | Railway status page red; uptime check failures from external probes (Better Stack); DNS resolves but 502 |
| Mitigation (P) | Railway multi-AZ where available. Static-only fallback page hosted at Cloudflare Pages with same domain (active during outage). Image CDN at Cloudflare independent of origin. |
| Mitigation (R) | Cloudflare DNS swing to maintenance page in <5min. Public status page. Comms via Twitter/Reddit. Restore on Railway recovery. v1.1 will add Fly.io secondary. |
| Residual likelihood | Medium (3) |
| Residual impact | Moderate (3) |
| Residual score | 9 |
| Owner | Backend lead |
| Status | Open (multi-region deferred to v1.1) |
| Last reviewed | 2026-05-03 |
| Linked controls | SECURITY-PLAYBOOK runbook 9; ADR-0001 |

### R-015 AI tool spend runaway

| Field | Value |
|---|---|
| Category | Operational / Strategic |
| Description | Bug or abuse causes Gemini calls to spike (e.g., infinite loop, abuse via headless browser farm). Daily Gemini bill blows monthly opex budget overnight. |
| Likelihood (pre) | High (4) — common foot-gun pattern in LLM apps |
| Impact (pre) | Moderate (3) — financial hit, no user harm |
| Score (pre) | 12 |
| Triggers | Gemini billing alert >2× daily baseline; Celery task volume >10× baseline; same-IP AI-tool usage >100/hour |
| Mitigation (P) | Daily spend cap enforced in `apps/tools/services/budget_guard.py` (Sprint 2) — feature-flag-kills tools at 80% threshold. Per-user rate limit (10/day free tier). Per-IP rate limit (50/day). Output token cap. Idempotency keys to prevent retry storms. |
| Mitigation (R) | Feature-flag kill via Operator one-click. Gemini key rotation if abuse via leaked key. Refund flow for trapped users. Replay log to identify abuse pattern. Block offending IPs at Caddy. |
| Residual likelihood | Low (2) |
| Residual impact | Minor (2) |
| Residual score | 4 |
| Owner | Backend lead |
| Status | Open (spend cap pending Sprint 2) |
| Last reviewed | 2026-05-03 |
| Linked controls | SECURITY-PLAYBOOK runbook 5 |

### R-016 Lawsuit: defamatory UGC about a named realtor

| Field | Value |
|---|---|
| Category | Regulatory |
| Description | Forum poster falsely accuses a Yakima realtor of misconduct in detailed post. Realtor sues platform under WA defamation law. Section 230 protects but litigation cost is real. |
| Likelihood (pre) | Medium (3) — small market = personal feuds + lawsuits |
| Impact (pre) | Major (4) — legal cost + reputational |
| Score (pre) | 12 |
| Triggers | Subpoena; cease-and-desist; complaint about specific named professional |
| Mitigation (P) | Moderation pipeline flags accusations against named entities. ToS prohibits unsubstantiated accusations. Author IP + email retained for 1 year (forensic). 230-compliant takedown process documented. Realtor verification badge means we have a real-name escalation channel. |
| Mitigation (R) | Counsel-on-retainer takedown response within 24h. 230 safe-harbor invocation. Author identification under valid subpoena only. Public statement if litigation escalates. |
| Residual likelihood | Medium (3) |
| Residual impact | Moderate (3) |
| Residual score | 9 |
| Owner | Compliance |
| Status | Open (counsel retainer pending pre-launch) |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Moderation subsystem; SECURITY-PLAYBOOK breach notification |

### R-017 Lawsuit: Fair Housing Act violation in AI tool output

| Field | Value |
|---|---|
| Category | Regulatory |
| Description | Description-writer tool generates listing copy containing protected-class signaling ("great for young families", "ideal for [demographic]"). HUD investigation or private suit. |
| Likelihood (pre) | Medium (3) — LLMs produce FHA-violating language by default |
| Impact (pre) | Major (4) — HUD penalty up to $24k per violation, brand damage |
| Score (pre) | 12 |
| Triggers | User complaint; HUD inquiry; output contains regex-matched protected-class language |
| Mitigation (P) | FHA-aware prompt template forbidding protected-class language (race, color, religion, national origin, sex, familial status, disability). Post-generation regex scan against FHA blacklist (`apps/tools/services/fha_filter.py`). Disclaimer banner on tool output: "review for compliance before publishing". User must confirm review before download. |
| Mitigation (R) | Yank affected outputs (90-day retention enables retroactive purge). Notify users to review past usage. Public statement, HUD cooperation. Update prompts + fixtures. |
| Residual likelihood | Low (2) |
| Residual impact | Moderate (3) |
| Residual score | 6 |
| Owner | Compliance + AI lead |
| Status | Open (FHA filter pending Phase 3) |
| Last reviewed | 2026-05-03 |
| Linked controls | THREAT-MODEL §Gemini integration; ADR-0003 |

### R-018 Lawsuit: ADA accessibility violation

| Field | Value |
|---|---|
| Category | Regulatory |
| Description | Vision-impaired user cannot use platform; demand letter under ADA Title III (federal courts have ruled web platforms covered). |
| Likelihood (pre) | Low (2) — small site, low profile |
| Impact (pre) | Moderate (3) — settlement + remediation cost |
| Score (pre) | 6 |
| Triggers | Demand letter; user complaint; failing automated a11y scan in CI |
| Mitigation (P) | WCAG 2.1 AA target. Axe-core in CI (Phase 8). Manual screen-reader testing each phase. Semantic HTML, ARIA where required, focus management on HTMX swaps, keyboard navigation, prefers-reduced-motion honored, color contrast verified against design tokens. |
| Mitigation (R) | Remediation under counsel guidance. Public a11y statement. Voluntary VPAT publication. |
| Residual likelihood | Very Low (1) |
| Residual impact | Minor (2) |
| Residual score | 2 |
| Owner | Frontend lead |
| Status | Open (Phase 8) |
| Last reviewed | 2026-05-03 |
| Linked controls | SRS §a11y |

### R-019 WA licensing change requiring new verify path

| Field | Value |
|---|---|
| Category | Regulatory |
| Description | WA Department of Licensing changes verification interface, deprecates ARELLO, or introduces additional verification requirements (e.g., periodic re-verify mandate). Existing ARELLO integration breaks. |
| Likelihood (pre) | Low (2) — slow regulatory churn |
| Impact (pre) | Moderate (3) — re-implementation work, possible compliance gap |
| Score (pre) | 6 |
| Triggers | DOL bulletin; ARELLO deprecation notice; compliance counsel alert |
| Mitigation (P) | Subscribe to DOL real estate bulletins. Quarterly compliance review. ARELLO contract reviewed annually. Verification interface abstracted via `apps/accounts/services/license_verifier.py` (provider-agnostic). |
| Mitigation (R) | Rapid implementation of replacement provider behind same interface. Grace period for existing realtors. Public comms. |
| Residual likelihood | Low (2) |
| Residual impact | Minor (2) |
| Residual score | 4 |
| Owner | Compliance |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | ADR-0002; THREAT-MODEL §License-fraud |

### R-020 Solo developer unavailability

| Field | Value |
|---|---|
| Category | Operational / Strategic |
| Description | Solo dev incapacitated (illness, accident, family emergency). No on-call rotation. Site cannot be patched, incidents unhandled. |
| Likelihood (pre) | Medium (3) — non-trivial probability over 12 months |
| Impact (pre) | Major (4) — extended outages, missed SEV-1 windows |
| Score (pre) | 12 |
| Triggers | Solo dev unreachable >24h |
| Mitigation (P) | RUNBOOK + SECURITY-PLAYBOOK + this register written to enable cold-start by replacement contractor. Repo + secrets accessible to designated successor (legal arrangement, sealed envelope). Railway/Cloudflare/Postmark accounts use shared org with backup admin. Auto-pause feature flag pre-set; sets site read-only if no heartbeat in 72h (Sprint 7). |
| Mitigation (R) | Backup admin invokes site read-only mode → preserves trust + safety until permanent solution. Engage emergency contractor from preselected list. Public statement. |
| Residual likelihood | Medium (3) |
| Residual impact | Moderate (3) |
| Residual score | 9 |
| Owner | Solo dev / Founder |
| Status | Open (succession plan pending pre-launch) |
| Last reviewed | 2026-05-03 |
| Linked controls | RUNBOOK §Succession |

### R-021 Scope creep delaying public launch past 16 weeks

| Field | Value |
|---|---|
| Category | Strategic |
| Description | "Just one more feature" pattern delays launch. Beta participants lose interest. Competitor preempts. |
| Likelihood (pre) | High (4) — universal solo-dev pattern |
| Impact (pre) | Moderate (3) — opportunity cost |
| Score (pre) | 12 |
| Triggers | Sprint slippage >1 sprint; new requirement injected mid-phase; >2 phases simultaneous |
| Mitigation (P) | Phase plans frozen at start of phase; new ideas land in `.planning/backlog/`. Strict phase gating: only one active phase at a time. Karpathy-guidelines skill enforces minimal scope. Master plan reviewed weekly. |
| Mitigation (R) | Cut Phase 7 (social embeds) and ship at v1; embed in v1.1. Public beta rolling release model. |
| Residual likelihood | Medium (3) |
| Residual impact | Minor (2) |
| Residual score | 6 |
| Owner | Founder |
| Status | Open |
| Last reviewed | 2026-05-03 |
| Linked controls | `docs/STATE-OF-THE-PROJECT.md` |

### R-022 Beta user abandoned platform after early friction

| Field | Value |
|---|---|
| Category | Strategic |
| Description | Early Yakima beta cohort (target: 50 realtors) hits onboarding friction (license verify failure, slow page, confusing nav) and churns silently. Word-of-mouth poisoned in tight market. |
| Likelihood (pre) | High (4) — common B2B SaaS pattern, especially in skeptical pro market |
| Impact (pre) | Major (4) — Yakima reputation locally damaged, harder reseed |
| Score (pre) | 16 |
| Triggers | Drop-off rate >50% between signup-start and first-post; NPS <0 in beta survey; <30% Day 7 retention |
| Mitigation (P) | Concierge onboarding for first 50 realtors (1:1 phone walkthrough). License-verify <30s p95 SLO. Active in-product feedback widget (Sprint 4). Founder responds personally to all support requests during beta. Onboarding tutorial gated by completion checklist. |
| Mitigation (R) | Personal re-engagement outreach. Targeted feature fix for friction point. Beta extension if needed. |
| Residual likelihood | Medium (3) |
| Residual impact | Moderate (3) |
| Residual score | 9 |
| Owner | Founder |
| Status | Open |
| Last reviewed | 2026-05-03 |
| Linked controls | `docs/STATE-OF-THE-PROJECT.md` |

### R-023 Competing local platform launches in Yakima

| Field | Value |
|---|---|
| Category | Strategic |
| Description | National competitor (e.g., Homes.com, Zillow neighborhood) or local startup launches Yakima-specific community feature first. |
| Likelihood (pre) | Low (2) — Yakima is small, ignored by majors |
| Impact (pre) | Moderate (3) — first-mover advantage erosion |
| Score (pre) | 6 |
| Triggers | Market signal; new platform spotted in Yakima Reddit; competitor PR |
| Mitigation (P) | Concentrated Yakima focus (do not broaden to Kennewick/Tri-Cities until 6-month traction). Verified-realtor badge as moat. Local-knowledge content advantage. |
| Mitigation (R) | Differentiation push (more Yakima-specific events, partnerships with Yakima Association of Realtors). Pricing promo for marketplace vendors. |
| Residual likelihood | Low (2) |
| Residual impact | Minor (2) |
| Residual score | 4 |
| Owner | Founder |
| Status | Open |
| Last reviewed | 2026-05-03 |
| Linked controls | `docs/STATE-OF-THE-PROJECT.md` |

### R-024 SEO penalty / de-indexing event

| Field | Value |
|---|---|
| Category | Strategic / Operational |
| Description | Google de-ranks or de-indexes site for AI-assisted UGC, doorway-page pattern, or thin content. SEO is core to Yakima Web post growth strategy. |
| Likelihood (pre) | Medium (3) — Google's spammy-content updates land regularly |
| Impact (pre) | Major (4) — organic traffic collapse |
| Score (pre) | 12 |
| Triggers | GSC manual action; ranking drop >50% across tracked keywords; sudden indexed-pages decline |
| Mitigation (P) | Editorial-quality threshold (Layer 2 pipeline scores quality + originality). Per-realtor unique brokerage content. Author bylines + verified license markup (Real Estate Agent JSON-LD). Internal linking structure. No doorway-page pattern. AI-tool output watermarked + nofollowed when published. |
| Mitigation (R) | GSC reconsideration request. Content audit + thin-content removal. Schema fix. Public communication if user-visible. |
| Residual likelihood | Low (2) |
| Residual impact | Moderate (3) |
| Residual score | 6 |
| Owner | Founder + Frontend lead |
| Status | Open (Phase 8) |
| Last reviewed | 2026-05-03 |
| Linked controls | SRS §SEO |

### R-025 Critical CVE in Django/Next.js/dependencies

| Field | Value |
|---|---|
| Category | Technical |
| Description | Zero-day RCE or auth-bypass in Django, Next.js, allauth, SimpleJWT, bleach, or core dependency. Time-pressure to patch before exploitation. |
| Likelihood (pre) | Medium (3) — Django + Next.js have multiple advisories per year |
| Impact (pre) | Major (4) — RCE = full compromise |
| Score (pre) | 12 |
| Triggers | Django security release; Next.js advisory; CVE numbering authority publication; GitHub advisory database hit |
| Mitigation (P) | Subscribed to Django security mailing list, Next.js GitHub releases, npm audit + pip-audit weekly. Dependabot PRs. Patch SLA: critical within 24h, high within 72h. Pinned dependency versions with known-good hashes. WAF (Cloudflare) provides emergency rule capability. |
| Mitigation (R) | Patch deploy under emergency change window. WAF rule hot-patch if exploit signature known. Threat-hunt past logs for IoCs. Public statement if data risk. |
| Residual likelihood | Low (2) |
| Residual impact | Moderate (3) |
| Residual score | 6 |
| Owner | Backend lead |
| Status | Mitigated |
| Last reviewed | 2026-05-03 |
| Linked controls | SECURITY-PLAYBOOK §Dependency updates |

## 3. Heat map — pre-mitigation

Likelihood (rows, top = highest) × Impact (cols, right = highest). Cells list risk IDs.

| L \ I | 1 Insig | 2 Minor | 3 Mod | 4 Major | 5 Catas |
|---|---|---|---|---|---|
| **5 Very High** | | | R-006 | | |
| **4 High** | | | R-005, R-021 | R-003, R-007, R-022, R-015 | |
| **3 Medium** | | | R-013, R-001, R-018, R-019, R-023 | R-002, R-004, R-012, R-014, R-016, R-017, R-020, R-024, R-025 | |
| **2 Low** | | | R-011 | R-008, R-010 | R-009 |
| **1 Very Low** | | | | | |

Pre-mitigation distribution: 1 Critical (16+), 13 High (10–15), 11 Medium (5–9), 0 Low (1–4).

## 4. Heat map — post-mitigation (residual)

| L \ I | 1 Insig | 2 Minor | 3 Mod | 4 Major | 5 Catas |
|---|---|---|---|---|---|
| **5 Very High** | | | | | |
| **4 High** | | | | | |
| **3 Medium** | | R-005, R-006, R-021 | R-001, R-002, R-007, R-014, R-016, R-020, R-022 | | |
| **2 Low** | | R-013, R-023, R-019 | R-008, R-011 (Minor), R-012, R-015, R-017, R-018, R-024, R-025 | R-009 | |
| **1 Very Low** | | R-018, R-011 | R-010 | | |

Post-mitigation distribution: 0 Critical, 0 High, 18 Medium (5–9), 7 Low (1–4).

## 5. Aggregate posture

| Tier | Pre | Post | Delta |
|---|---|---|---|
| Critical (16–25) | 1 | 0 | -1 |
| High (10–15) | 13 | 0 | -13 |
| Medium (5–9) | 11 | 18 | +7 |
| Low (1–4) | 0 | 7 | +7 |

Net: zero unmitigated High or Critical residual. Largest residual cluster is Medium tier — acceptable for v1 launch with continuous review.

## 6. Open mitigation work tracked

| Risk | Outstanding control | Sprint |
|---|---|---|
| R-001 | ARELLO circuit breaker | 2 |
| R-002 | Gemini daily spend cap | 2 |
| R-005 | Review-fraud pattern detection | Phase 5 |
| R-012 | SES failover prewire | 6 |
| R-014 | Multi-region failover | v1.1 |
| R-015 | Spend cap | 2 |
| R-016 | Counsel retainer | pre-launch |
| R-017 | FHA filter | Phase 3 |
| R-018 | Axe-core in CI + manual a11y | Phase 8 |
| R-020 | Succession plan + 72h auto-pause | 7 |
| R-024 | Editorial quality scoring | Phase 8 |
