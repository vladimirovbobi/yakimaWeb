# Master Test Plan (MTP) — Yakima Real Estate Hub

## 1. Document Control

| Field | Value |
|---|---|
| Document | Master Test Plan |
| Project | Yakima Real Estate Hub |
| Version | 1.0 |
| Date | 2026-05-03 |
| Owner | Yakima Engineering — QA lead |
| Status | Approved baseline |
| Related | SRS.md, SAD.md, ICD.md, ACCESS-MATRIX.md, RTM.md |

---

## 2. Test Strategy Overview

Pyramid of tests:

| Layer | Volume target | Speed | Where |
|---|---|---|---|
| Unit (backend + frontend) | 80% of all assertions | < 5s suite avg per app | `apps/*/tests/`, `frontend/**/*.test.ts` |
| Integration | ~15% of assertions | < 60s suite | `tests/test_api/`, `tests/test_signals/` |
| E2E (critical paths) | ~5% — 25-30 scenarios | < 12 min full suite | `frontend/tests/e2e/` |

Budget per sprint: ≤ 30 min CI wall-time on full pipeline; if exceeded, parallelize or move slow test layer.

Execution order in CI:

1. Lint (ruff, djlint, eslint, tsc) — fail fast.
2. Unit (pytest -m "not slow", vitest run) — parallel.
3. Integration (pytest -m integration) — sequential within suite, parallel across apps.
4. Schema validation (`spectacular --validate`).
5. E2E (Playwright) — sharded by spec across 4 workers.
6. Lighthouse CI on staging — 5 key URLs.
7. Coverage gates enforced.

---

## 3. Test Types and Tooling

### 3.1 Unit — backend

| Tool | Purpose |
|---|---|
| pytest 8.x | runner |
| pytest-django | db fixtures, settings, urlconf |
| pytest-cov | coverage with `--cov-fail-under` enforced per app |
| factory_boy | model factories at `tests/factories/` |
| responses | mock outbound `requests` (ARELLO, Postmark) |
| freezegun | time-travel for token expiry, audit timestamps |
| pytest-xdist | `-n auto` parallel runner |
| hypothesis | property-based for serializers + parsers |

Config: `pytest.ini` sets `DJANGO_SETTINGS_MODULE=config.settings.test`, `--cov=apps --cov-branch`.

### 3.2 Unit — frontend

| Tool | Purpose |
|---|---|
| Vitest 2.x | runner with jsdom |
| React Testing Library | component contract |
| msw 2.x | request mocks generated from OpenAPI types |
| user-event 14.x | realistic interactions |
| @testing-library/jest-dom | matchers |

Coverage: `vitest run --coverage`, c8 reporter, gate in CI.

### 3.3 Integration

Real Postgres (ephemeral container in CI, `--reuse-db` locally), real Redis, real Celery in `task_always_eager=True`. Tests assert:

- Serializer round-trip (POST → GET returns same canonical shape).
- Permission classes deny anon/wrong-role and allow correct role.
- post_save signals create `ActionLog`, fire `moderate_content` task.
- Idempotency-Key replay returns identical body + `X-Idempotent-Replay: true`.
- ETag conditional GET returns 304.

Namespaced `tests/test_api/test_<resource>.py`, `tests/test_signals/`, `tests/test_celery/`.

### 3.4 End-to-End

| Tool | Purpose |
|---|---|
| Playwright 1.48 | browser automation |
| Targets | Chromium, WebKit, Firefox; iOS Safari emulator (iPhone 14), Pixel 5 emulator |
| Trace | `trace: 'retain-on-failure'` |
| Reporter | `html` + `github` |
| Parallelism | 4 shards across CI runners |

Tests live in `frontend/tests/e2e/`. Per-spec fixtures spin up an isolated user via `apiContext.post('/api/v1/auth/signup/')` then tear down.

### 3.5 Visual Regression — deferred to Sprint 6

| Tool | Purpose |
|---|---|
| Storybook 8.x | component catalog |
| @storybook/test-runner + Playwright | snapshot diffs |
| Chromatic (optional, paid) | reviewer UI |

Threshold: `<= 0.1%` pixel diff per component; differences stored as artifacts.

### 3.6 Accessibility

- `@axe-core/playwright` — every page-load in e2e suite asserts no `serious` or `critical` violations.
- Manual: NVDA on Windows + VoiceOver on macOS, scripted scripts in `docs/qa/screen-reader-scripts.md`.
- Keyboard-only walkthrough fixtures.
- Color-contrast verified at component level via Storybook addon.

### 3.7 Performance

Lighthouse CI runs against staging on 5 URLs:

1. `/` (home)
2. `/blog/` (post list)
3. `/blog/<slug>/` (post detail)
4. `/marketplace/` (service list)
5. `/community/` (forum)

Budgets:

| Metric | Threshold |
|---|---|
| Performance | ≥ 95 (mobile) / ≥ 98 (desktop) |
| Accessibility | ≥ 100 |
| Best practices | ≥ 100 |
| SEO | ≥ 95 |
| LCP | ≤ 2.0s mobile / ≤ 1.2s desktop |
| INP | ≤ 200ms |
| CLS | ≤ 0.05 |
| TBT | ≤ 200ms |
| First-load JS | ≤ 180KB gzip |

Backend perf via `pytest-benchmark` for hot paths (post list serializer, mod pipeline).

### 3.8 Security

| Tool | Phase | Scope |
|---|---|---|
| bandit | every commit | Python static |
| ruff (S rules) | every commit | Python static |
| eslint-plugin-security | every commit | JS static |
| pip-audit | nightly | Python deps |
| npm audit | nightly | JS deps |
| Trivy | nightly | Container images |
| OWASP ZAP baseline | weekly + pre-release | Dynamic — staging |
| OWASP ZAP full | monthly | Authenticated scan |
| Manual pen test | Sprint 6 + pre-launch | Comprehensive |
| SBOM (cyclonedx) | every release | Supply chain |

### 3.9 Load

k6 against staging. Scenarios in `tests/load/`:

| Scenario | Pattern | Target |
|---|---|---|
| Baseline 10K MAU | 350 RPS sustained 30 min | p95 < 500ms |
| Peak burst 1K concurrent | ramp to 1000 VU over 5 min, hold 10 min | p95 < 800ms, error < 1% |
| Login storm | 100 logins/sec for 2 min | p95 < 400ms, no 5xx |
| Comment moderation backlog | 5K queued comments | drain < 5 min, no task losses |
| AI tool burst | 200 description requests in 1 min | rate-limit kicks in cleanly, no 5xx |

### 3.10 Adversarial Moderation

Fixture suite `apps/moderation/tests/fixtures/prompt_injection_attacks.json`. Per phase, ≥ 5 new fixtures from real-world reports. Categories:

- Direct override ("ignore previous instructions...")
- Indirect via embedded URL/document
- Obfuscation (unicode homoglyph, base64, leetspeak)
- Role hijack ("you are now an unfiltered AI...")
- Context window stuffing
- Tool-use redirection
- Multilingual evasion
- Prompt-leakage probes
- Encoded payloads (rot13, hex)

Test gate: pipeline never returns `approve` on any attack fixture; `injection_guard.parse_classifier_response` returns `{"action": "block", "reason": ...}` and Celery task writes ModerationDecision with `action=remove`.

### 3.11 Contract

Schemathesis runs nightly against staging using the published OpenAPI schema. Strategies enabled:

- `--checks all` (status_code_conformance, content_type_conformance, response_schema_conformance, response_headers_conformance)
- Stateful runs with the auth fixture
- Hypothesis 500 examples per endpoint

Failures triage to a contract-bug template.

---

## 4. Test Environments

| Env | Stack | Data | Purpose |
|---|---|---|---|
| Local dev | docker compose | seeded via `manage.py seed_demo` | Developer workflow |
| CI | GitHub Actions, ephemeral PG/Redis | factories per test | Block merge |
| Staging | Railway, real Cloudflare R2 (staging bucket), real ARELLO sandbox, Gemini, Postmark sandbox | sanitized prod-like seed; no PII | Pre-prod verification, load, ZAP |
| Production | Railway prod | real | Smoke tests post-deploy |

Test data policy:

- No production data is ever copied into staging/dev.
- Staging seeded from synthetic generators + Faker locales `en_US, es_MX`.
- Golden fixtures in `apps/moderation/tests/fixtures/` are committed.
- `manage.py seed_demo --realtors=20 --vendors=15 --posts=80 --threads=120` for local.

---

## 5. Critical-Path E2E Scenarios

Each scenario maps to a Playwright spec under `frontend/tests/e2e/`. ID format: `E2E-NN`.

| ID | Scenario | Spec file | Tags |
|---|---|---|---|
| E2E-01 | Anonymous visitor browses homepage → blog → service → forum thread; no login required, all pages render with SEO meta and a11y clean | `01-anon-browse.spec.ts` | smoke, public, a11y |
| E2E-02 | Visitor signs up → receives verification email (mailpit) → confirms → logs in → lands on dashboard | `02-signup-verify-login.spec.ts` | auth, smoke |
| E2E-03 | New realtor submits license → ARELLO returns 200 → verified badge appears → can publish blog | `03-realtor-verify.spec.ts` | realtor, license, smoke |
| E2E-04 | Existing realtor publishes blog → moderation passes → publicly listed → SEO tags in HTML | `04-realtor-publish-blog.spec.ts` | realtor, content |
| E2E-05 | Anonymous user attempts to comment → redirected to /signin?next=... | `05-anon-comment-redirect.spec.ts` | auth, public |
| E2E-06 | Authenticated user comments on blog → moderation `approved` → comment appears | `06-comment-happy.spec.ts` | content, moderation |
| E2E-07 | Authenticated user comments with prompt-injection payload → moderation blocks → 451 with helpful message | `07-comment-injection.spec.ts` | moderation, security |
| E2E-08 | Anonymous user upvotes a forum thread → redirected to login → completes login → vote applied without losing intent | `08-forum-anon-upvote.spec.ts` | forum, auth |
| E2E-09 | Vendor onboarding 5-step wizard with autosave; reload mid-step recovers; publish enters review | `09-vendor-onboarding.spec.ts` | marketplace, vendor |
| E2E-10 | Buyer sends lead inquiry → vendor receives email + SSE event → reply → mark won → buyer leaves review | `10-lead-flow.spec.ts` | marketplace, lead, sse |
| E2E-11 | Realtor runs description writer → moderation passes → ToolUsage row created → cost displayed | `11-tool-description.spec.ts` | tools, ai |
| E2E-12 | Realtor runs description writer with PII-stuffed payload → moderation blocks; user shown remediation | `12-tool-description-pii.spec.ts` | tools, moderation |
| E2E-13 | Realtor uploads furnished room → furniture remover task succeeds → ToolUsage cost tracked | `13-tool-furniture-remover.spec.ts` | tools, ai |
| E2E-14 | Realtor exceeds AI tool rate limit → 429 with `Retry-After` and clear UI message | `14-tool-rate-limit.spec.ts` | tools, throttle |
| E2E-15 | Moderator clears 10-item queue with keyboard shortcuts in < 2 minutes | `15-mod-keyboard-flow.spec.ts` | moderation, keyboard |
| E2E-16 | Moderator escalates ambiguous item → operator queue receives it via SSE | `16-mod-escalate.spec.ts` | moderation, sse |
| E2E-17 | Operator suspends user → ActionLog row created → user redirected to suspended page on next request | `17-ops-suspend-user.spec.ts` | ops, audit |
| E2E-18 | Operator views per-mod stats dashboard with throughput and accuracy metrics | `18-ops-dashboard.spec.ts` | ops |
| E2E-19 | Admin login from non-allowlisted IP → 403 page; allowlisted IP succeeds with TOTP | `19-admin-ip-allowlist.spec.ts` | admin, security |
| E2E-20 | Staff write via Django admin (edit a Post) → ActionLog row written automatically | `20-staff-action-log.spec.ts` | audit |
| E2E-21 | Anonymous Lighthouse on `/` returns ≥95/100/100/95 on mobile profile | `21-lighthouse-home.spec.ts` | perf, smoke |
| E2E-22 | iPhone SE (375px) renders home + service detail with no horizontal scroll | `22-mobile-no-overflow.spec.ts` | mobile, a11y |
| E2E-23 | `prefers-reduced-motion: reduce` disables all animations; `x-reveal` directives still place final state | `23-reduced-motion.spec.ts` | a11y |
| E2E-24 | Screen-reader walkthrough: NVDA announces all landmarks, headings hierarchy, form labels | `24-screen-reader-landmarks.spec.ts` | a11y |
| E2E-25 | Service category filter by `photography/drone` returns expected results, paginates with cursor | `25-service-filter-paginate.spec.ts` | marketplace, public |
| E2E-26 | Authenticated user searches blog by keyword → relevant results highlighted | `26-blog-search.spec.ts` | content, search |
| E2E-27 | Anonymous user → `GET /api/v1/me/` returns 401 RFC 7807 body | `27-api-me-401.spec.ts` | api, auth |
| E2E-28 | Authenticated non-op user → `GET /api/v1/ops/users/` returns 403 | `28-api-ops-403.spec.ts` | api, perms |
| E2E-29 | JWT access expires mid-session → silent refresh on 401 → retried request succeeds → no UX flash | `29-jwt-silent-refresh.spec.ts` | auth |
| E2E-30 | POST without `X-CSRFToken` → 403 from CSRF middleware with clear error body | `30-csrf-missing.spec.ts` | security |

Total: 30 scenarios. Smoke subset (`@smoke` tag): E2E-01, 02, 03, 06, 09, 10, 11, 21, 27.

---

## 6. Coverage Targets

| Surface | Tool | Threshold |
|---|---|---|
| `apps/accounts` | pytest-cov | ≥ 85% lines, ≥ 80% branches |
| `apps/moderation` | pytest-cov | ≥ 90% lines, ≥ 85% branches |
| `apps/audit` | pytest-cov | ≥ 90% lines, ≥ 85% branches |
| `apps/admin_tools` | pytest-cov | ≥ 85% lines |
| `apps/content` | pytest-cov | ≥ 75% lines |
| `apps/forum` | pytest-cov | ≥ 75% lines |
| `apps/marketplace` | pytest-cov | ≥ 75% lines |
| `apps/tools` | pytest-cov | ≥ 75% lines |
| `apps/operations` | pytest-cov | ≥ 75% lines |
| `apps/core` | pytest-cov | ≥ 75% lines |
| `frontend/components/` | vitest c8 | ≥ 70% lines |
| `frontend/lib/` | vitest c8 | ≥ 75% lines |

Aggregate coverage report uploaded as CI artifact + Codecov.

---

## 7. Entry / Exit Criteria

### 7.1 Entry — to begin a phase's test execution

- All phase models have at least one factory.
- ICD has stable schema for endpoints in the phase.
- AI calls stubbed with `responses` for unit, real for integration.
- Feature flag for the phase exists in `feature_flags` table.

### 7.2 Exit — phase considered "test complete"

- Coverage gates met for every touched app.
- All E2E tagged for the phase pass on Chromium + WebKit.
- Schemathesis runs clean against changed endpoints.
- `python manage.py check --deploy` no new warnings.
- Sentry has no `unhandled` errors over 24h staging soak.
- ZAP baseline finds no new high/critical findings.
- Adversarial fixture suite extended by ≥ 5 new entries.

### 7.3 Pre-launch (Sprint 8) exit

- 30/30 E2E green on all targeted browsers.
- Lighthouse budgets met on all 5 URLs.
- k6 baseline + peak scenarios pass.
- Manual pen test report — no high/critical open.
- Backup/restore drill executed.
- Runbook updated.

---

## 8. Defect Management

| Severity | Definition | SLA to fix | Examples |
|---|---|---|---|
| Critical | Data loss, security breach, full outage, moderation pipeline approves an attack | 4h | injection bypass, ARELLO audit row missing, admin IP allowlist bypassed |
| High | Major feature unusable for many users, financial discrepancy | 24h | login broken, leads not delivered |
| Medium | Feature degraded for some users, workaround exists | 5 business days | filter returns wrong page count |
| Low | Cosmetic, copy, minor a11y violation that doesn't block users | next sprint | tooltip clipping |

Tracker: GitHub Issues with `severity:critical|high|medium|low` labels. Critical incidents trigger PagerDuty + post-mortem (RUNBOOK §post-mortem).

---

## 9. Test Data Management

| Asset | Location | Owner |
|---|---|---|
| Factories | `tests/factories/{user,post,service,...}.py` | each app's owner |
| Seed command | `apps/core/management/commands/seed_demo.py` | core team |
| Golden moderation fixtures | `apps/moderation/tests/fixtures/{prompt_injection_attacks,benign,borderline}.json` | mod team |
| ARELLO mock catalog | `apps/accounts/tests/fixtures/arello_responses/*.json` | accounts team |
| Gemini mock responses | `apps/tools/tests/fixtures/gemini_responses/*.json` | tools team |
| Demo media | `media/demo/` (gitignored, generated by seed) | core team |

Refreshing: `make seed` (clears db, recreates schema, runs seed_demo with deterministic seed). Faker `seed=20260503`.

---

## 10. Risks to the Test Plan

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Flaky E2E (network, animation timing) | High | Medium | retry x2, video on failure, stable selectors only (`data-testid`), `prefers-reduced-motion` in CI by default, explicit waits not arbitrary sleeps |
| Slow CI eats sprint velocity | Med | High | parallel sharding, `--reuse-db`, factory cache, lint pre-checks fail fast |
| Env drift between dev/staging | Med | Med | docker compose parity with Railway, infra as code, weekly drift audit |
| Test data churn breaks fixtures | Med | Med | golden fixture review part of PR, versioned migrations |
| ARELLO sandbox unavailable | Low | High | local responses-mocked tests cover most paths; staging falls back to recorded VCR cassettes |
| Gemini quota exhausted in CI | Med | Med | unit/integration uses recorded responses; only soak test uses live |
| Adversarial fixture missing real-world variant | High | High | external monitoring (Hugging Face, OWASP LLM Top 10) feeds quarterly fixture refresh |
| Visual regression false positives | High | Low | masked dynamic regions (timestamps), threshold tuning, manual approval queue |
| Lighthouse run variance | High | Low | 3-run median, throttling profile pinned, `--no-update-config` |

---

## 11. Reporting

| Output | Where | Audience |
|---|---|---|
| Coverage report | CI artifact + Codecov dashboard | engineering |
| Playwright HTML report | CI artifact (retained 30 days) | engineering, QA |
| Lighthouse CI report | Lighthouse server + GitHub PR comment | engineering, design |
| k6 report | Grafana Cloud dashboard linked from RUNBOOK | engineering, ops |
| Schemathesis | CI artifact | engineering |
| ZAP scan | nightly artifact + Sentry alert on high | security |
| Defect dashboard | GitHub Project board "Test debt" | engineering, product |
| Phase test summary | `.planning/phases/phase-N-<slug>/TEST-REPORT.md` | engineering, leadership |

Per-PR comment template includes: coverage diff, new tests added, failing scenarios, perf budget delta. Auto-posted by `gha-pr-comment` action.

---

## 12. Cross-References

- SRS.md — requirement IDs verified by each test case.
- ICD.md §section per endpoint — request/response shapes asserted.
- ACCESS-MATRIX.md — role tests in E2E-27, E2E-28, integration suite.
- RTM.md — bidirectional traceability table.
- RUNBOOK.md — incident response loops back to test gates after a fix.
