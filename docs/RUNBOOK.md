# Operations Runbook — Yakima Real Estate Hub

**Version:** 1.0
**Date:** 2026-05-03
**Owner:** Yakima Real Estate Hub Engineering
**Status:** Active
**Cross-references:** [SAD.md](./SAD.md), [SRS.md](./SRS.md), [ICD.md](./ICD.md), [SECURITY-PLAYBOOK.md](./SECURITY-PLAYBOOK.md), [ACCESS-MATRIX.md](./ACCESS-MATRIX.md), [COPY-STYLE-GUIDE.md](./COPY-STYLE-GUIDE.md)

> Source of truth for "how do I…" during operations. Update whenever a procedure changes. Procedures here are tested mentally before commit; if a sequence does not work in practice, fix it here in the same PR.

---

## 1. Document Control

| Field | Value |
|---|---|
| Version | 1.0 |
| Effective | 2026-05-03 |
| Owner | Yakima Real Estate Hub Engineering |
| Review cadence | After each phase ships, plus quarterly otherwise |
| Approvers | Lead engineer (PR sign-off) |
| Supersedes | RUNBOOK.md v0.x (initial scaffold from Phase 0) |
| Distribution | Repo contributors. Excerpts shared with on-call (solo for v1). |

---

## 2. Architecture Overview

The platform is an 8-service Docker Compose stack, fronted by Caddy as a reverse proxy. Django REST Framework serves the API; Next.js 15 serves the public frontend (App Router, RSC, JWT cookies handled in middleware). Postgres 16 is the system of record. Redis 7 handles cache, session, rate-limit keys, Celery broker, and Celery result backend. Two Celery processes (worker + beat) handle every async job — moderation, ARELLO calls, AI tool runs, email sends, image processing trigger fan-out. An `img-worker` service handles signed-URL uploads to Cloudflare R2 with on-the-fly resize. Caddy terminates TLS (Let's Encrypt staging in dev, prod certs in prod) and routes by path: `/api/*` → Django, `/*` → Next.js.

| Service | Image / build | Port | Purpose |
|---|---|---|---|
| `caddy` | caddy:2-alpine | 80, 443 | Reverse proxy, TLS, static asset cache |
| `web` | local Dockerfile (Django + gunicorn) | internal 8000 | DRF API + admin |
| `next` | local Dockerfile (Node 20 + Next.js) | internal 3000 | Public site, RSC, ISR |
| `db` | postgres:16-alpine | internal 5432 | System of record |
| `redis` | redis:7-alpine | internal 6379 | Cache, sessions, rate limit, Celery broker |
| `worker` | local Dockerfile (Celery worker) | — | Async tasks |
| `beat` | local Dockerfile (Celery beat) | — | Scheduled jobs (`django-celery-beat` DB scheduler) |
| `img-worker` | local Dockerfile (image resize daemon) | — | R2 upload + resize + variant generation |

See [SAD.md](./SAD.md) for full diagrams. The compose file: `docker-compose.yml`. Production `docker-compose.prod.yml` overrides resource limits and removes dev-only volumes.

---

## 3. Local Development

### 3.1 Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker Desktop | latest | Windows: WSL2 backend recommended |
| Python | 3.12+ | Use `uv` to install — system Python is fine as a fallback |
| `uv` | latest | `pip install uv` or `winget install astral-sh.uv` |
| Node | 20+ | LTS. Use `nvm-windows` if juggling multiple |
| npm | 10+ | bundled with Node 20 |
| Git | 2.40+ | line-ending policy: `core.autocrlf=false`, repo is LF |
| make | optional | A few convenience targets in `Makefile` |
| `gh` (GitHub CLI) | optional | for PR workflows |

### 3.2 First-time setup

```bash
# clone
git clone git@github.com:yakima-web/yakimaweb.git
cd yakimaweb

# env
cp .env.example .env
# Edit .env. At minimum:
#   - DJANGO_SECRET_KEY: 50 random chars (see below)
#   - DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
#   - POSTGRES_* defaults are fine for local
#   - GEMINI_API_KEY: optional locally — set MOCK_GEMINI=True to skip

# Generate a secret key:
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Python deps
uv venv
uv pip install -e . --group dev

# JS deps + build
npm install
npm run build

# bring up infra (db + redis + img-worker)
docker compose up -d db redis img-worker

# bring up application services
docker compose up -d web next worker beat caddy

# OR run web/next on the host while infra is in compose:
docker compose up -d db redis img-worker
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py createsuperuser
.venv/Scripts/python.exe manage.py seed_demo   # demo content for local UAT
.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000

# In another shell — Celery worker
.venv/Scripts/python.exe -m celery -A config worker -l info

# In another shell — Celery beat (scheduled tasks)
.venv/Scripts/python.exe -m celery -A config beat -l info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

# In another shell — Next.js dev server (host mode)
cd frontend && npm run dev
```

Verify:

- `http://localhost:8000/api/public/v1/healthz/` returns `{"status":"ok"}`.
- `http://localhost:3000/` renders the home page.
- `http://localhost:8000/admin/` returns the admin login (locked behind 2FA + IP allowlist in prod, not in dev).
- `docker compose ps` shows all services healthy.

### 3.3 Daily workflow

```bash
# start the stack
docker compose up -d

# tail logs of one service
docker compose logs -f web

# run tests
.venv/Scripts/python.exe -m pytest

# lint + format
ruff check . && ruff format .
djlint templates/
cd frontend && npm run lint && npm run typecheck && cd ..

# format on save: configure your editor to run ruff + prettier on save

# commit
git add -p
git commit -m "feat(scope): short imperative subject

Why this change exists in 1–3 lines."

# push + open PR
git push -u origin phase-2/stream-1-content
gh pr create --fill
```

### 3.4 Common commands cheatsheet

| Command | Purpose |
|---|---|
| `docker compose up -d` | Start full stack detached |
| `docker compose down` | Stop stack, keep volumes |
| `docker compose down -v` | Stop stack + delete volumes (DESTRUCTIVE — see §3.5) |
| `docker compose ps` | Service status snapshot |
| `docker compose logs -f <svc>` | Tail logs |
| `docker compose exec web bash` | Shell into Django container |
| `docker compose exec db psql -U postgres yakima` | Postgres prompt |
| `docker compose exec redis redis-cli` | Redis prompt |
| `python manage.py migrate` | Apply migrations |
| `python manage.py makemigrations <app>` | Create migration |
| `python manage.py shell_plus` | Django shell with auto-imports (django-extensions) |
| `python manage.py seed_demo` | Load demo content for local UAT |
| `python manage.py check --deploy` | Production-readiness check |
| `python manage.py collectstatic --noinput` | Collect static for prod |
| `pytest` | Run all tests |
| `pytest apps/accounts -k arello` | Filter by path + keyword |
| `pytest -x --pdb` | Stop at first failure, drop into debugger |
| `pytest --cov=apps --cov-report=term-missing` | Coverage |
| `ruff check . && ruff format .` | Lint + format Python |
| `djlint templates/` | Template lint |
| `npm run dev` (frontend/) | Next.js dev server with hot reload |
| `npm run build` (frontend/) | Production build |
| `npm run typecheck` | TypeScript check |
| `npm test` | Vitest unit tests (frontend) |
| `npx playwright test` | E2E (servers must be up) |
| `npx playwright test --headed` | Headed mode for debugging |
| `npx playwright test --ui` | Interactive runner |
| `gh pr create --fill` | Open PR using commit messages |

### 3.5 Resetting state

`docker compose down -v` deletes the Postgres and Redis volumes. **This wipes all local data.** Recover by:

```bash
docker compose down -v
docker compose up -d db redis img-worker
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py createsuperuser
.venv/Scripts/python.exe manage.py seed_demo
```

To reset only Postgres without touching Redis:

```bash
docker compose stop db
docker volume rm yakimaweb_db_data
docker compose up -d db
.venv/Scripts/python.exe manage.py migrate
```

### 3.6 Running specific test subsets

| Need | Command |
|---|---|
| One app | `pytest apps/moderation` |
| One file | `pytest apps/moderation/tests/test_pipeline.py` |
| One test | `pytest apps/moderation/tests/test_pipeline.py::test_three_layer_passes` |
| Keyword match | `pytest -k injection` |
| Failing-only after partial run | `pytest --lf` |
| Stop on first failure | `pytest -x` |
| Verbose output | `pytest -vv` |
| Show stdout | `pytest -s` |
| Coverage on accounts | `pytest apps/accounts --cov=apps.accounts --cov-report=term-missing` |
| Frontend unit | `cd frontend && npm test` |
| Frontend type check | `cd frontend && npm run typecheck` |
| E2E smoke | `npx playwright test tests/e2e/smoke.spec.ts` |
| E2E headed (single test) | `npx playwright test tests/e2e/auth.spec.ts --headed -g "sign up"` |

### 3.7 Debugging Celery

```bash
# inspect what's running
.venv/Scripts/python.exe -m celery -A config inspect active
.venv/Scripts/python.exe -m celery -A config inspect scheduled
.venv/Scripts/python.exe -m celery -A config inspect reserved
.venv/Scripts/python.exe -m celery -A config inspect stats

# task history (last 100)
.venv/Scripts/python.exe manage.py shell_plus
>>> from django_celery_results.models import TaskResult
>>> TaskResult.objects.order_by("-date_done")[:100]

# replay a task
>>> from apps.moderation.tasks import moderate_content
>>> result = moderate_content.delay(post_id=42)
>>> result.get(timeout=10)

# purge a clogged queue (DEV ONLY)
.venv/Scripts/python.exe -m celery -A config purge -f

# Watch the worker log live
docker compose logs -f worker
```

If a Celery task is stuck, see §6.6.1.

### 3.8 Frontend development

```bash
cd frontend
npm run dev                  # http://localhost:3000 with HMR
npm run build && npm start   # production build, served on 3000
```

Notes:

- `next/` uses App Router with Server Components. Anything that needs the JWT cookie runs in middleware or a Route Handler. RSCs read from cookies via `cookies()` from `next/headers`.
- The Django API base URL is configured via `NEXT_PUBLIC_API_BASE_URL`. In compose, that's `http://web:8000`. From the browser, it's `http://localhost/api`.
- HMR works for client components; RSC changes trigger a full reload.
- Tailwind classes are JIT-compiled. The brand tokens (gold #BFA06A on dark) live in `frontend/tailwind.config.ts` — change once, propagate everywhere.

To debug an RSC:

1. Add a `console.log` — output goes to the Next.js server stdout (terminal running `npm run dev`).
2. Use the React DevTools "Server Components" tab in the browser to see what props were sent.
3. For network calls from RSCs, watch the `web` service log too — that's the Django side.

### 3.9 Mocked vs live external services

| Service | Env var | When to mock |
|---|---|---|
| Gemini | `MOCK_GEMINI=True` | Local dev without API key. Returns canned responses defined in `apps/moderation/services/mock_gemini.py`. |
| ARELLO | `MOCK_ARELLO=True` | Local dev. Returns "verified" for license `12345` and "not_found" otherwise. |
| Postmark | `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` | Local dev. Emails print to stdout instead of sending. |
| R2 / S3 | `USE_S3=False` | Local dev. Files write to `media/` on the host. |
| Sentry | unset `SENTRY_DSN` | Local dev. No telemetry. |

In CI: all mocks ON except for the dedicated "live integrations" job that runs nightly with sandbox credentials.

In staging + prod: all mocks OFF. `MOCK_*` env vars are forbidden in production by `manage.py check --deploy` (custom check).

---

## 4. Deployment

### 4.1 Environments

| Environment | Hosting | Branch | URL pattern | Notes |
|---|---|---|---|---|
| Local dev | Docker Compose on developer machine | feature branches | `localhost` | All services local. |
| CI | GitHub Actions ephemeral | PR branch | — | Runs lint + tests + Playwright on every PR. |
| Staging | Railway | `staging` branch | `staging.yakimaweb.com` | Auto-deploy on merge to `staging`. Live integrations with sandbox credentials. |
| Production | Railway | `main` branch | `yakimaweb.com` | Manual promotion from staging. Strict deploy gates. |

### 4.2 Branching strategy

```
main                  always-deployable. tagged releases.
└── staging           auto-deploys to staging on merge.
    └── phase-N/stream-X-name
                      feature work. PR target = staging (then main).
```

Rules:

- `main` is always deployable. No direct pushes. PRs only.
- `phase-N/stream-X-name` for feature work — names match the phase plans.
- One PR per stream. Squash on merge to `staging`. Fast-forward (or rebase merge) from `staging` to `main`.
- Hotfix branch: `hotfix/<issue>` — PRs to `main` directly with same gates.
- All PRs require: green CI, code review, security review for security-touching diffs.

### 4.3 Pre-deploy checklist

Before any merge to `main`:

| # | Check | Command / signal |
|---|---|---|
| 1 | Tests green | CI status check |
| 2 | Coverage holds | `pytest --cov=apps --cov-report=term-missing` (≥80% on accounts/moderation/audit) |
| 3 | Ruff clean | `ruff check . && ruff format --check .` |
| 4 | Templates clean | `djlint templates/ --check` |
| 5 | Django deploy check | `python manage.py check --deploy` (no warnings beyond explicit waivers) |
| 6 | Migrations atomic | Inspect migration: zero-downtime patterns (§4.6) |
| 7 | Frontend type check | `cd frontend && npm run typecheck` |
| 8 | Frontend lint | `cd frontend && npm run lint` |
| 9 | Lighthouse on staging | Score ≥90 perf, ≥95 a11y, ≥90 SEO on key routes |
| 10 | axe scan | No violations on key public pages |
| 11 | Playwright critical paths | `npx playwright test --grep critical` |
| 12 | Security review (if security-touching) | `security-review` skill output approved |
| 13 | ADR (if architectural) | New ADR file committed |
| 14 | Docs updated | RUNBOOK / SRS / ICD / ACCESS-MATRIX reflect changes |

### 4.4 Deploy procedure — staging

Auto on merge to `staging`. No human steps for routine changes.

1. PR merged to `staging`.
2. Railway picks up the push, builds the Dockerfile, runs migrations as a release command, deploys.
3. Smoke tests run (Playwright "critical" tag against `staging.yakimaweb.com`) via a GitHub Action.
4. On failure: Railway auto-rollback. Slack notification to engineer.

Manual smoke after auto-deploy:

```bash
# from a dev machine
curl -fsS https://staging.yakimaweb.com/api/public/v1/healthz/
curl -fsS https://staging.yakimaweb.com/ | grep -q "Yakima"
```

### 4.5 Deploy procedure — production

Manual promotion. The point of "manual" is the smoke checklist below; the actual click is one button.

1. Confirm staging has been green for ≥24 hours.
2. Spot-check the live business metrics dashboard for anything unusual on staging.
3. Merge `staging` → `main` via PR. PR title: `release: vYYYY.MM.DD`. Tag the commit on `main` with that version.
4. Railway deploys `main` to production. Migrations run as the release command.
5. Run prod smoke checklist:

| # | Check | Expected |
|---|---|---|
| 1 | `curl -fsS https://yakimaweb.com/api/public/v1/healthz/` | `{"status":"ok"}` |
| 2 | Browse `/`, `/about/`, `/guidelines/`, `/privacy/`, `/terms/` | 200, no console errors |
| 3 | `/accounts/signup/` | Form renders, no errors |
| 4 | Sign in as a known test member | JWT cookie set, redirect succeeds |
| 5 | `/admin/` from allowlisted IP | Login page renders + 2FA prompt on submit |
| 6 | `/admin/` from non-allowlisted IP | 403 |
| 7 | Mod queue (test mod account) | Loads, count matches staging-as-of-promotion |
| 8 | Operator dashboard (test op account) | Loads, no 5xx |
| 9 | Send a test inquiry through marketplace | Email arrives at vendor inbox within 60s |
| 10 | Sentry has no new errors in last 5 min | Sentry dashboard |

If any step fails: rollback (§4.7).

### 4.6 Database migrations in prod (zero-downtime)

The platform serves traffic during deploys. Schema changes that lock or break old code are forbidden.

**Three-PR pattern for non-trivial column changes:**

Example — renaming `Vendor.bio` to `Vendor.about`:

| PR | Action | Behavior |
|---|---|---|
| 1 | Add `about` as nullable. Code writes both `bio` and `about`. Reads prefer `about`, fallback to `bio`. | Old + new code coexist. |
| 2 | Backfill: `UPDATE vendor SET about = bio WHERE about IS NULL` (run via `RunPython` or out-of-band SQL). | All rows now have `about`. |
| 3 | Drop `bio`. Make `about` non-null. Remove fallback code. | Final state. |

**Forbidden in a single PR:**

- `ALTER TABLE … DROP COLUMN` on a column the running code still references.
- `ALTER TABLE … ALTER COLUMN … TYPE …` on a column with non-trivial data.
- `ALTER TABLE … ADD COLUMN … NOT NULL` without a default (Postgres rewrites the table — OK on small tables, slow on big ones; for tables >100k rows, use the three-PR pattern).
- Adding a unique constraint on existing data without first verifying uniqueness via a query.

**Allowed in a single PR:**

- `ADD COLUMN nullable` (Postgres ≥11 makes this metadata-only).
- `ADD INDEX CONCURRENTLY` (not the default — see migration template `apps/<app>/migrations/_concurrent_index_template.py`).
- `DROP INDEX CONCURRENTLY` (same).
- New tables.
- Data-only `RunPython` migrations that don't lock long.

Migration commits use scope `chore(migrations): …` or `feat(<app>): … + migration`. Always include a one-line comment in the migration explaining what the migration does (Django auto-generated headers are not enough).

### 4.7 Rollback procedure

#### 4.7.1 Code rollback

Railway has a one-click rollback:

```
Railway dashboard → Service → Deployments → previous deployment → Redeploy
```

Or via CLI:

```bash
railway service:rollback --service web --to <deployment-id>
```

Rolling back rebuilds and redeploys the previous image. Sessions persist (Redis). JWTs persist (signed). Caddy auto-reloads.

#### 4.7.2 Database rollback

**Default policy: forward-only migrations.** A botched migration is fixed by another migration. Backwards migrations are technically possible but risk data loss and are reserved for catastrophic schema corruption.

Backwards migration is allowed only when:

1. The forward migration is purely additive (added a column, added a table, added an index).
2. The forward migration is data-clean (no rows depend on the new column/table).
3. There's a documented reason it must come out (incident, security issue).
4. It's run in maintenance mode (Caddy returns 503 for non-/healthz routes).

For an additive forward migration that needs to come out:

```bash
# put site in maintenance mode (set MAINTENANCE_MODE=True in Railway env)
# run reverse migration
railway run python manage.py migrate <app> <previous_migration_name>
# verify
railway run python manage.py showmigrations <app>
# turn maintenance off
```

Document any backwards migration in [SECURITY-PLAYBOOK.md](./SECURITY-PLAYBOOK.md) post-incident.

### 4.8 Feature flags

V1 uses env-var feature flags:

| Flag | Default (prod) | Effect when False |
|---|---|---|
| `FEATURE_AI_TOOLS` | True | AI tool routes return 404. Description writer + furniture remover hidden from nav. |
| `FEATURE_MARKETPLACE` | True | Marketplace routes return 404. Vendor onboarding hidden. |
| `FEATURE_FORUM` | True | Forum routes return 404. Forum nav hidden. |
| `FEATURE_REGISTRATION` | True | New signups blocked. Existing users unaffected. |
| `MAINTENANCE_MODE` | False | All non-/healthz routes return 503 with a static page. |

Flags are read at process start. Toggling requires a Railway env-var update + redeploy (~30s).

Runtime DB-backed flags (django-waffle) are deferred until v2.

### 4.9 Secrets management

All secrets live in Railway environment variables, scoped per environment. Local dev uses `.env` (in `.gitignore`).

Never commit:

- `DJANGO_SECRET_KEY`
- `GEMINI_API_KEY`
- `ARELLO_API_KEY`
- `POSTMARK_SERVER_TOKEN`
- `AWS_SECRET_ACCESS_KEY` (R2)
- `SENTRY_DSN`
- `JWT_SIGNING_KEY`

Pre-commit hook (`gitleaks` config in `.pre-commit-config.yaml`) blocks commits containing secret-shaped strings.

Rotation cadence is in [SECURITY-PLAYBOOK.md §Secret rotation](./SECURITY-PLAYBOOK.md). Quick reference:

| Secret | Cadence |
|---|---|
| `DJANGO_SECRET_KEY` | Annually + on staff offboarding |
| `JWT_SIGNING_KEY` | Annually + on suspected leak |
| `GEMINI_API_KEY` | Quarterly |
| `ARELLO_API_KEY` | Annually + on incident |
| `POSTMARK_SERVER_TOKEN` | Annually |
| R2 credentials | Quarterly |
| Database password | Annually (rolling restart) |

---

## 5. Monitoring & Observability

### 5.1 Sentry

- Project: `yakima-web` (production), `yakima-web-staging` (staging).
- DSN injected via `SENTRY_DSN` env var.
- Sample rate: 100% errors, 10% performance traces (prod), 100% both (staging).
- Sensitive data scrubbing: configured to drop `password`, `token`, `csrf*`, `authorization`, `cookie`, `set-cookie`, `*_key`, JWT cookie names. PII fields (email, phone, address) are scrubbed before send via the `before_send` hook. License numbers redacted to last 4.
- Release tracking: each Railway deploy tags Sentry with the git SHA via `SENTRY_RELEASE`.
- Source maps: uploaded for Next.js builds via `@sentry/nextjs` plugin; Django source not uploaded (server-side only).

Routine: skim Sentry once per business day. Triage:

- New error type → open issue, assign owner, target fix in ≤7 days.
- Spiking error → page on-call (§5.6).
- Known/triaged error → mark "Ignored until next release."

### 5.2 Better Stack

- Uptime monitor on `https://yakimaweb.com/api/public/v1/healthz/` every 60s from 3 regions.
- Heartbeat: Celery beat sends a heartbeat every 5 min. Missed heartbeat after 10 min → alert.
- Status page: `status.yakimaweb.com` (subdomain CNAME'd to Better Stack).
- On-call: solo for v1. Webhook → email + SMS to lead engineer.

### 5.3 Application logs

- Format: structured JSON via `structlog`.
- Destination: stdout. Railway captures and aggregates.
- Optional: forward to Logtail (Better Stack's log product) by setting `LOGTAIL_TOKEN`.
- Standard fields: `timestamp`, `level`, `event`, `request_id`, `user_id` (if authenticated), `path`, `method`, `status`, `duration_ms`, `app`, `version`.
- Sensitive fields scrubbed at the structlog processor level — same allowlist as Sentry.

To search logs locally:

```bash
docker compose logs web --since 30m | jq 'select(.level=="ERROR")'
docker compose logs worker --since 1h | jq 'select(.event=="task_failure")'
```

In Railway: dashboard → service → Logs tab → search by field.

### 5.4 Health checks

| Endpoint | Service | Returns |
|---|---|---|
| `/api/public/v1/healthz/` | Caddy → web | `{"status":"ok"}` if DB + Redis reachable. 503 otherwise. |
| `/api/public/v1/healthz/deep/` | Caddy → web | Slower check: ARELLO ping, Gemini ping, R2 reachable. Used for deep monitoring, not page health. |
| Caddy `/healthz` (internal) | Caddy | `200 OK` while Caddy is up. |
| Postgres `pg_isready` | db | Used by Docker healthcheck + Better Stack readiness probe. |
| Redis `PING` | redis | Used by Docker healthcheck. |
| Celery beat heartbeat | beat | Writes a Redis key every 5 min. Worker checks staleness. |
| Worker queue depth | worker | Writes queue depth to Redis every 30s for Better Stack scrape. |

### 5.5 Metrics dashboards

Hosted on Better Stack + a simple Django admin page at `/admin/operations/metrics/`.

Key business metrics:

| Metric | Source | Refresh |
|---|---|---|
| Daily signups | `accounts.User.date_joined` | 1h |
| Verified realtors | `accounts.RealtorProfile.status='verified'` | 1h |
| Approved vendors | `accounts.VendorProfile.is_approved=True` | 1h |
| MAU (rolling 30 days) | `audit.AccessLog` distinct user_id | daily |
| Mod queue depth | `moderation.ModerationDecision.status='pending'` | 5m |
| Mod queue oldest age | min `created_at` of pending | 5m |
| AI spend today (USD) | `tools.ToolUsage.cost_usd` sum | 5m |
| Lead conversion rate | `marketplace.Lead` accepted / sent | daily |
| ARELLO calls today | `accounts.LicenseCheck` count | 1h |
| ARELLO error rate (24h) | LicenseCheck status | 5m |
| Gemini error rate (24h) | structlog events | 5m |
| 5xx rate (24h) | request log status | 1m |

### 5.6 Alerting thresholds

| Condition | Channel | SLA |
|---|---|---|
| 5xx rate >1% over 5 min | Page (SMS + call) | Respond in 15 min |
| /healthz/ down (>2 consecutive failures) | Page | 15 min |
| Mod queue depth >50 | Email | Same business day |
| Mod queue oldest age >24h | Email | Same business day |
| AI daily spend >150% of cap | Page | 1h (manual disable) |
| AI daily spend >100% of cap | Auto-disable AI tools + email | Automatic |
| ARELLO error rate >5% (24h) | Email | Same business day |
| Gemini error rate >5% (24h) | Email | Same business day |
| Postmark bounce rate >5% | Email | Same business day |
| New Sentry error type | Email | Triage in 24h |
| Spike: error count 5x baseline (10 min window) | Page | 15 min |
| Database disk >75% | Email | 7 days |
| Database disk >90% | Page | 4h |
| Redis memory >75% | Email | 7 days |
| Redis memory >90% | Page | 4h |

---

## 6. Routine Operations

### 6.1 Daily

- [ ] Check Sentry for new error types (5 min).
- [ ] Check Better Stack uptime + status page (1 min).
- [ ] Check mod queue depth + oldest age (1 min).
- [ ] Check AI daily spend vs cap (1 min).
- [ ] Skim Slack/email for user reports.

### 6.2 Weekly

- [ ] Review `audit.ActionLog` for the week — spot-check 10 random staff actions for plausibility (5 min).
- [ ] Review dependabot/renovate PRs. Merge minor + patch after CI passes; major bumps go through ADR.
- [ ] (Sprint 7+) Triage beta-tester feedback queue.
- [ ] Review error budget: 5xx rate trailing 7 days vs 1% target.

### 6.3 Monthly

- [ ] `pip-audit` + `npm audit` — open issues for any CVE Medium+.
- [ ] Verify secret rotation calendar — anything due this month?
- [ ] Backup restore drill — restore yesterday's prod backup into a dev Postgres, verify counts on `User`, `Post`, `Lead`. (See §6.3.1.)
- [ ] Lighthouse re-baseline on key routes — log scores in `docs/perf-history.md` (creates the file on first run).
- [ ] Review billing for Railway, Cloudflare, Postmark, Google AI, ARELLO. Anything anomalous?

#### 6.3.1 Backup restore drill

```bash
# 1. download yesterday's logical backup from Railway
#    (or pg_dump from prod if Railway snapshots aren't sufficient)

# 2. spin up a fresh Postgres locally
docker run --rm -d --name pg-restore -p 5440:5432 \
    -e POSTGRES_PASSWORD=test postgres:16-alpine

# 3. restore
psql -h localhost -p 5440 -U postgres -c "CREATE DATABASE yakima_restore;"
psql -h localhost -p 5440 -U postgres -d yakima_restore -f backup.sql

# 4. spot-check
psql -h localhost -p 5440 -U postgres -d yakima_restore -c "
  SELECT count(*) FROM accounts_user;
  SELECT count(*) FROM content_post;
  SELECT count(*) FROM marketplace_lead;
  SELECT max(created_at) FROM audit_actionlog;
"

# 5. tear down
docker stop pg-restore
```

Document the run in `docs/restore-drills.md` (creates the file on first run): date, backup age, counts, time taken.

### 6.4 Quarterly

- [ ] Threat model review — walk through STRIDE per surface; update [SECURITY-PLAYBOOK.md](./SECURITY-PLAYBOOK.md).
- [ ] ADR audit — list ADRs; mark any "Superseded" with the replacement; close stale ones.
- [ ] Dependency major-upgrade scan — Django minor, DRF, Next.js, Tailwind, Celery. Major bumps → spike branch + ADR.
- [ ] Sentry data retention review — drop sample rates if cost grows.
- [ ] Cost vs forecast review — adjust caps and budgets in this runbook.

### 6.5 Annual

- [ ] Penetration test (third-party). Findings → ticketed and triaged within 30 days.
- [ ] Threat model deep-dive — full re-walk by lead engineer + an outside reviewer.
- [ ] Attorney review of Privacy + Terms.
- [ ] DSAR drill — exercise the data-export path end-to-end on a test account.
- [ ] Incident runbook tabletop — pick a scenario from [SECURITY-PLAYBOOK.md](./SECURITY-PLAYBOOK.md), walk through it, time the response, fix gaps.

### 6.6 Common issues & fixes

#### 6.6.1 Celery tasks stuck

Symptoms: task stays in `STARTED` forever; queue depth grows.

```bash
# 1. inspect
.venv/Scripts/python.exe -m celery -A config inspect active
.venv/Scripts/python.exe -m celery -A config inspect stats

# 2. find the worker. if it's reachable, send SIGTERM (graceful) then SIGKILL.
docker compose restart worker

# 3. requeue the task by re-running its trigger (post_save signal, etc.)
#    or, if the task is idempotent and you have its args:
.venv/Scripts/python.exe manage.py shell_plus
>>> from apps.moderation.tasks import moderate_content
>>> moderate_content.delay(post_id=42)

# 4. scale workers if it's a sustained load issue
docker compose up -d --scale worker=2
# (or set CELERY_WORKER_CONCURRENCY in .env and restart)
```

For a hung beat-scheduled job, check `django_celery_beat.PeriodicTask.last_run_at` in the admin.

#### 6.6.2 Migration deadlock

Symptoms: `migrate` hangs; pg query log shows lock waits.

```sql
-- 1. find the blocker
SELECT
  blocked.pid AS blocked_pid,
  blocked.query AS blocked_query,
  blocking.pid AS blocking_pid,
  blocking.query AS blocking_query,
  blocked.wait_event_type, blocked.wait_event
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid = blocked.pid AND NOT bl.granted
JOIN pg_locks bg ON bg.locktype = bl.locktype
  AND bg.database IS NOT DISTINCT FROM bl.database
  AND bg.relation IS NOT DISTINCT FROM bl.relation
  AND bg.page IS NOT DISTINCT FROM bl.page
  AND bg.tuple IS NOT DISTINCT FROM bl.tuple
  AND bg.virtualxid IS NOT DISTINCT FROM bl.virtualxid
  AND bg.transactionid IS NOT DISTINCT FROM bl.transactionid
  AND bg.classid IS NOT DISTINCT FROM bl.classid
  AND bg.objid IS NOT DISTINCT FROM bl.objid
  AND bg.objsubid IS NOT DISTINCT FROM bl.objsubid
  AND bg.pid <> bl.pid
  AND bg.granted
JOIN pg_stat_activity blocking ON blocking.pid = bg.pid;

-- 2. kill the blocker (last resort)
SELECT pg_cancel_backend(<blocking_pid>);   -- polite
SELECT pg_terminate_backend(<blocking_pid>); -- forceful

-- 3. retry migration
```

Prefer canceling over terminating. Almost every deadlock here is caused by a long-running query during deploy — the fix is to schedule heavy migrations during low-traffic windows.

#### 6.6.3 Redis OOM

Symptoms: writes start failing with `OOM command not allowed`; memory usage stays high after eviction.

```bash
# 1. check memory + eviction
docker compose exec redis redis-cli INFO memory | grep used_memory_human
docker compose exec redis redis-cli INFO stats | grep evicted_keys

# 2. inspect what's hot
docker compose exec redis redis-cli --bigkeys

# 3. audit rate-limit keys (common offender on UGC spikes)
docker compose exec redis redis-cli --scan --pattern "rl:*" | head -20

# 4. if the bigkeys / pattern audit shows runaway data:
#    delete by pattern (carefully — match exactly)
docker compose exec redis redis-cli --scan --pattern "rl:bot-pattern:*" \
  | xargs -L 100 redis-cli DEL

# 5. last resort: FLUSHDB on the cache DB only (NOT the Celery DB)
#    Celery uses DB 0 by default; cache uses DB 1 (configured in .env).
docker compose exec redis redis-cli -n 1 FLUSHDB
```

`FLUSHDB` clears sessions on the cache DB if sessions are configured to use it. Users will be logged out. JWT-cookie auth means sessions are mostly cosmetic — the JWT itself remains valid until expiry — but staff Django sessions are real, and they will need to re-auth.

Maxmemory policy is `allkeys-lru`. Adjust `maxmemory` in compose if memory pressure is sustained.

#### 6.6.4 ARELLO 5xx

Symptoms: license verifications fail; `LicenseCheck` rows accumulate with `status=error`.

The ARELLO client wraps calls in a circuit breaker (`pybreaker`):

- Threshold: 5 failures in 60 seconds → open.
- Half-open after 60 seconds; one trial call.
- On success → closed.

While open: new verification requests queue (Celery retries with exponential backoff up to 10 attempts over 24h). Realtor sees the "verification pending" banner; member status is unchanged.

Manual unblock:

```bash
# 1. confirm ARELLO is back (curl a sandbox URL or check status page)

# 2. force the breaker closed via Django shell
.venv/Scripts/python.exe manage.py shell_plus
>>> from apps.accounts.services.arello import breaker
>>> breaker.close()

# 3. re-trigger queued verifications
>>> from apps.accounts.tasks import retry_pending_verifications
>>> retry_pending_verifications.delay()
```

If ARELLO is down for >24h: communicate via status page; consider granting interim "pending" badges visible only to staff.

#### 6.6.5 Gemini quota / spend exceeded

Symptoms: AI tool calls fail; `ToolUsage` rows show `error: quota_exceeded`.

Auto-behavior:

- `tools.services.spend_guard` checks `today_spend_usd` before every call.
- If `today_spend_usd > GEMINI_DAILY_SPEND_CAP_USD` → call refuses with a clean error to the user ("Daily AI tool limit reached. Resets at midnight UTC.").
- At 150% of cap → page on-call.

Manual disable:

```bash
# in Railway env vars
FEATURE_AI_TOOLS=False
# redeploy (~30s)
```

Investigate root cause: a single user spamming, a runaway agent loop, a Gemini pricing change. Walk `ToolUsage` grouped by user and by tool to find the source.

To raise the cap: update `GEMINI_DAILY_SPEND_CAP_USD` env var. Document the change in [SECURITY-PLAYBOOK.md §Cost incidents](./SECURITY-PLAYBOOK.md).

#### 6.6.6 Postmark bounces spike

Symptoms: Better Stack alert on bounce rate; Postmark dashboard shows hard bounces increasing.

```bash
# 1. open the Postmark suppression list
#    Postmark dashboard → Servers → Yakima Web → Suppressions

# 2. check the bounce reasons. common patterns:
#    - "Mailbox does not exist" → user typo on signup. Force re-verify email.
#    - "Hard bounce: spam complaint" → user marked us as spam. Suppress + investigate (was the email opt-in? was the content right?)
#    - "Soft bounce: mailbox full" → transient; let Postmark retry.

# 3. check our DKIM + SPF records
dig TXT _dmarc.yakimaweb.com
dig TXT yakimaweb._domainkey.yakimaweb.com
dig TXT yakimaweb.com   # SPF should include spf.mtasv.net

# 4. if DKIM/SPF broke (DNS edit, key rotation):
#    re-verify the sender domain in Postmark dashboard
```

If a single sender pattern is failing (e.g., all "Welcome" emails to `@gmail.com`): that's a content issue. Check Postmark's "Promotional" vs "Transactional" stream classification.

#### 6.6.7 Image upload failures

Symptoms: users see "Upload failed" on R2-backed flows (post images, vendor portfolio).

```bash
# 1. test R2 connectivity from the img-worker container
docker compose exec img-worker python -c "
import boto3, os
s = boto3.client('s3',
    endpoint_url=os.environ['AWS_S3_ENDPOINT_URL'],
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])
print(s.list_buckets())
"

# 2. check signed URL expiry (default 60 min)
#    If users paste an upload URL after the expiry, they'll get a 403 from R2.
#    Confirm the upload modal shows an error in that case.

# 3. inspect img-worker logs
docker compose logs img-worker --since 30m

# 4. if R2 is genuinely down: check Cloudflare status page.
#    Manual unblock isn't usually needed; uploads queue and retry.
```

R2 credentials: rotate quarterly. After rotation, restart `web` and `img-worker`.

---

## 7. Incident Handling

Full runbooks live in [SECURITY-PLAYBOOK.md](./SECURITY-PLAYBOOK.md). Quick triage:

| Severity | Definition | Response |
|---|---|---|
| SEV-1 | Site down OR data breach OR unauthorized access | Page on-call. Open incident channel. Stop deploys. Communicate within 30 min. |
| SEV-2 | Major feature broken (signup, mod queue, AI tools) OR partial outage | Page on-call. Communicate within 1h. |
| SEV-3 | Minor feature broken OR elevated error rate but recovering | Triage same business day. |
| SEV-4 | Cosmetic, single-user, or low-impact | Backlog. |

Always:

1. **Don't delete anything.** `audit.ActionLog` is append-only; preserve forensic trail.
2. **Open an incident channel.** Slack `#incident-YYYYMMDD-<short-tag>`.
3. **Update the status page.** Briefly. "We're investigating elevated error rates."
4. **Pull the audit trail.** Last 24h of `audit.ActionLog` + `audit.AccessLog` for any affected user.
5. **Post-incident review.** Within 5 business days. Blameless. Result is a doc + tracked action items.

---

## 8. On-call Playbook

V1 is solo: lead engineer is on-call 24/7. The structure below is documented now so adding a second person is a config change, not a process change.

| Aspect | V1 (solo) | V2+ (team) |
|---|---|---|
| Primary | Lead engineer | Rotation |
| Secondary | None | Backup engineer |
| Escalation | Founder (informal) | Engineering manager → CTO |
| Tooling | Better Stack → email + SMS | Add PagerDuty or Opsgenie |
| Handoff | N/A | Friday-to-Friday weekly rotation |
| Schedule | Always-on | 1 week primary, 1 week off |
| Compensation | N/A | Per-shift stipend |

While solo:

- Acknowledge alerts within 15 min during business hours, 30 min off-hours.
- Maintenance windows: Tuesday 02:00 – 04:00 PT for non-emergency work.
- "Do not disturb" exceptions: SEV-1 and SEV-2 only.
- If the on-call is unreachable for >1 hour during a SEV-1/2, the founder is the fallback contact.

---

## 9. Useful Commands Appendix

### 9.1 Django shell snippets

```python
# count active members
from apps.accounts.models import User
User.objects.filter(is_active=True).count()

# verified realtors
User.objects.filter(realtor_profile__status="verified").count()

# approved vendors
User.objects.filter(vendor_profile__is_approved=True).count()

# DAU last 7 days
from datetime import timedelta
from django.utils import timezone
from apps.audit.models import AccessLog
since = timezone.now() - timedelta(days=7)
AccessLog.objects.filter(created_at__gte=since).values("user_id").distinct().count()

# mod queue
from apps.moderation.models import ModerationDecision
ModerationDecision.objects.filter(status="pending").count()
ModerationDecision.objects.filter(status="pending").order_by("created_at").first().created_at

# AI spend today
from apps.tools.models import ToolUsage
from django.db.models import Sum
ToolUsage.objects.filter(created_at__date=timezone.now().date()).aggregate(Sum("cost_usd"))

# license re-verify a user
from apps.accounts.tasks import verify_license
verify_license.delay(user_id=123)

# force a moderation re-run
from apps.moderation.tasks import moderate_content
moderate_content.delay(post_id=42)
```

### 9.2 Postgres SQL snippets

```sql
-- table sizes (top 20)
SELECT relname AS table, pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- slow queries today
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
WHERE total_exec_time > 1000
ORDER BY total_exec_time DESC
LIMIT 20;

-- recent admin actions
SELECT actor_id, action, target_type, target_id, created_at
FROM audit_actionlog
WHERE created_at > now() - interval '24 hours'
ORDER BY created_at DESC;

-- license-check error rate last 24h
SELECT
  status,
  count(*),
  100.0 * count(*) / sum(count(*)) OVER () AS pct
FROM accounts_licensecheck
WHERE created_at > now() - interval '24 hours'
GROUP BY status;

-- mod decisions by reviewer this week
SELECT reviewer_id, action, count(*)
FROM moderation_moderationdecision
WHERE created_at > now() - interval '7 days'
GROUP BY reviewer_id, action
ORDER BY reviewer_id, action;

-- top vendors by leads this month
SELECT vp.user_id, count(*) AS leads
FROM marketplace_lead l
JOIN marketplace_service s ON s.id = l.service_id
JOIN accounts_vendorprofile vp ON vp.user_id = s.vendor_id
WHERE l.created_at > date_trunc('month', now())
GROUP BY vp.user_id
ORDER BY leads DESC
LIMIT 20;
```

### 9.3 Manage.py custom commands

| Command | Purpose |
|---|---|
| `seed_demo` | Load demo content (users, posts, services) for local UAT. |
| `reverify_all_active_realtors` | (defined in `apps/accounts/management/commands/`) Force re-run ARELLO on every verified realtor. Run quarterly. |
| `recompute_search_index` | Rebuild `tsvector` columns after a major data import. |
| `prune_audit_log_retention` | Per-policy archival of `AccessLog` older than the retention window. (`ActionLog` is never pruned.) |
| `mod_queue_health` | Print queue depth + oldest-age + recent throughput. |
| `cost_report --since=YYYY-MM-DD` | Roll up Gemini + ARELLO usage for the period. |
| `secret_rotation_status` | Print last-rotated dates from a `secret_rotation.json` checked in alongside this runbook. |

---

## 10. Glossary

| Term | Meaning |
|---|---|
| **ARELLO** | Association of Real Estate License Law Officials — third-party API used to verify WA real estate licenses. See ADR-0002. |
| **ActionLog** | Append-only audit table of staff writes. Source of truth for "who did what, when." |
| **AccessLog** | Per-request log of authenticated reads/writes. Used for DAU/MAU + forensic trails. |
| **Bundle** | Marketplace SKU combining multiple Packages at a discount. |
| **Caddy** | Reverse proxy in front of compose. Handles TLS + path routing. |
| **Celery** | Async task queue. Worker + beat scheduler. |
| **Circuit breaker** | `pybreaker` wrapping ARELLO + Gemini calls. Fails closed after N consecutive errors. |
| **Comp** | Comparable sale — used in real estate to price a listing. |
| **DOM** | Days on market. |
| **Description writer** | AI tool that drafts listing copy. See `apps/tools/services/description_writer.py`. |
| **Flair** | Forum thread classifier ("Question", "Market data", "For sale"). |
| **Furniture remover** | AI tool that removes furniture from listing photos. Ported from `virtual-staging-app`. |
| **Gemini** | Google's LLM. We use 2.5 Flash for moderation, 2.5 Pro for tools. See ADR-0003. |
| **Lead** | Buyer-to-vendor inquiry through the marketplace. |
| **LeadMessage** | Reply within a Lead thread. |
| **LicenseCheck** | Append-only row capturing each ARELLO call (request + raw response). |
| **ModeratableMixin** | Django model mixin that wires post-save signal → Celery moderation pipeline. Every UGC model inherits it. |
| **Mod console** | Internal tool for moderators. |
| **Op** | Operator role — staff with business actions in addition to mod actions. |
| **Operator dashboard** | Internal tool for ops. |
| **Package** | One vendor service tier (basic / standard / premium). |
| **Pipeline** | The 3-layer Gemini moderation pipeline: rule pre-check → Gemini classify → Gemini second-pass with injection guard. |
| **R2** | Cloudflare's object storage (S3-compatible). |
| **RealtorProfile** | Extended profile on `User` for verified realtors. |
| **Reply** | Forum reply to a thread or another reply. |
| **Service** | Marketplace listing by a Vendor (parent of Packages). |
| **Thread** | Forum top-level post. |
| **VendorProfile** | Extended profile on `User` for marketplace vendors. |
| **WA** | Washington (state). |

---

## 11. Phase Status

- [x] Phase 0: Research & Reference docs
- [x] Phase 1: Foundation
- [x] Phase 2: Content System (scaffold)
- [x] Phase 3: AI Lead Magnets (scaffold)
- [x] Phase 4: Forum (scaffold)
- [x] Phase 5: Marketplace (scaffold)
- [x] Phase 6: Control Surfaces (scaffold)
- [x] Phase 7: Social integration (scaffold)
- [x] Phase 8: Production polish (scaffold)

Per-phase plans: `.planning/phases/phase-N-<name>/PLAN.md`.
Master plan: `C:\Users\vladi\.claude\plans\create-a-local-real-tranquil-koala.md`.
Outstanding follow-ups by phase: `docs/SECURITY-FINAL.md`.

— *Yakima Real Estate Hub Engineering, 2026-05-03*
