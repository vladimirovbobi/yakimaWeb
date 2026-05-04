# Operations Runbook — Yakima Real Estate Hub

> Source of truth for "how do I…" questions during operations.
> Update whenever a procedure changes.

---

## Local development

### Prerequisites
- Python 3.12+
- Node 22+
- Docker + Docker Compose
- uv (`pip install uv`)

### First-time setup
```bash
cd C:\Users\vladi\OneDrive\Desktop\Projects\yakimaWeb
cp .env.example .env
# edit .env — at minimum set DJANGO_SECRET_KEY (50 random chars)

# Python deps
uv venv
uv pip install -e .
uv pip install --group dev

# JS deps + bundle
npm install
npm run build

# Postgres + Redis
docker compose up -d db redis

# Migrations + superuser
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver

# In a separate terminal: Celery worker
celery -A config worker --loglevel=info

# In a third terminal (optional): Celery beat
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Site at http://localhost:8000.

### Common commands
```bash
pytest                     # all tests
pytest apps/accounts       # one app
pytest -k arello           # filter
ruff check . && ruff format .
djlint templates/
npm run dev                # vite watch mode
npx playwright test        # e2e (server must be running)
npx playwright test --ui   # interactive
```

---

## Deploy to Railway

### First-time
1. Create Railway project + Postgres add-on + Redis add-on.
2. Push image to GHCR or let Railway build from Dockerfile.
3. Set env vars from `.env.example` — production values.
4. Connect GitHub repo + enable auto-deploy on `main`.

### Required env vars in Railway
- `DJANGO_SETTINGS_MODULE=config.settings.prod`
- `DJANGO_SECRET_KEY` (rotate annually)
- `DJANGO_ALLOWED_HOSTS=yakimaweb.com,*.up.railway.app`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://yakimaweb.com`
- `DATABASE_URL` (Railway-injected)
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `POSTMARK_SERVER_TOKEN`, `DEFAULT_FROM_EMAIL`
- `GEMINI_API_KEY`
- `ARELLO_API_KEY`, `ARELLO_BASE_URL=https://lvws.arello.com` (prod, not sandbox)
- `USE_S3=True` + R2 credentials
- `SENTRY_DSN`
- `ADMIN_IP_ALLOWLIST` (your office + Tailscale IPs only)

### Roll back
```bash
railway service:rollback --service web --to <deployment-id>
```

---

## Operational procedures

### Grant operator role to a user
```bash
python manage.py shell
>>> from apps.accounts.models import User, Role
>>> u = User.objects.get(email="ops@example.com")
>>> u.role = Role.STAFF
>>> u.is_staff = True
>>> u.save()
# Then enroll TOTP — the next admin login will force the QR setup.
```

### Suspend a user (interim — moderator console arrives in Phase 6)
Via Django admin → Users → toggle `is_active=False`. Action auto-logged to `audit.ActionLog`.

### Force re-verify all realtor licenses
```bash
python manage.py shell
>>> from apps.accounts.tasks import reverify_all_active_realtors
>>> reverify_all_active_realtors.delay()
```

### Investigate a moderation decision
Via Django admin → Moderation → ModerationDecision. Search by `input_hash`.
Append-only — no one can delete.

### Replay moderation pipeline against a sample
```bash
python manage.py shell
>>> from apps.moderation.services.pipeline import moderate
>>> moderate("test content here")
```

### Add a new prompt-injection attack to the fixture set
1. Edit `apps/moderation/tests/fixtures/prompt_injection_attacks.json`
2. Add `{"name": "<descriptive-name>", "content": "<the attack>"}`
3. Run `pytest apps/moderation/tests/test_injection_guard.py`
4. If pre-flag rate drops below 60%, tighten patterns in `injection_guard.INJECTION_PATTERNS`
5. Commit

---

## Incident response

### Suspected security breach
1. **Don't panic.** Don't delete anything.
2. Email security@yakimaweb.com — log incident with timestamp + observed behavior.
3. Pull last 24h of `audit.ActionLog` + `audit.AccessLog` via admin.
4. If credentials suspected compromised: rotate `DJANGO_SECRET_KEY`, force all sessions to re-auth (`python manage.py changepassword <user>`), rotate ARELLO + Gemini API keys.
5. If user data exposed: privacy@yakimaweb.com to lead notifications under WA RCW 19.255.

### ARELLO down
- Verifications queue automatically (Celery retry).
- Operator dashboard (Phase 6) will show backlog.
- Manual override: admin → RealtorProfile → flip status (logged to ActionLog).

### Gemini moderation throwing > 5% errors
1. Check `apps/moderation/services/ai_classifier.py` logs.
2. Fall-back: temporarily flip moderation to "queue all" via env var (TODO Phase 2).
3. Monitor `moderation.ModerationDecision` audit log for anomalies.

### Production smoke test (after each deploy)
1. `curl -f https://yakimaweb.com/healthz` → `ok`
2. Open `/`, `/about/`, `/guidelines/` — 200, no errors in console.
3. Hit `/accounts/signup/` → form renders.
4. Hit `/admin/` from allowed IP → 200 + 2FA prompt.
5. Hit `/admin/` from non-allowed IP → 403.

---

## Cost monitoring

| Service | Budget | Where to check |
|---|---|---|
| Railway compute | $50–100/mo | Railway dashboard |
| Cloudflare R2 + CDN | $20/mo | CF dashboard |
| Postmark email | $25/mo | Postmark dashboard |
| ARELLO API | $300/mo | ARELLO invoice |
| Gemini API | < $50/mo (P1) | Google Cloud Console + GEMINI_DAILY_SPEND_CAP_USD |
| Sentry | free tier | Sentry dashboard |

Alert thresholds (configure in vendor dashboards):
- Railway > $150/mo → page ops
- Gemini > daily cap → auto-disable AI tools (Phase 3 will wire this)
- ARELLO 429 rate > 5% → check API key + quota

---

## Secret rotation schedule

| Secret | Rotate every | Where set | Notes |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | annually + on staff offboarding | Railway env | All sessions invalidated on rotation |
| `ARELLO_API_KEY` | annually + on incident | Railway env + ARELLO portal | Rotate via support email |
| `GEMINI_API_KEY` | quarterly | Google Cloud Console | Multiple keys per project; rotate one at a time, validate, retire old |
| `POSTMARK_SERVER_TOKEN` | annually | Postmark dashboard | Note the previous token retains send capability for 24h after rotation |
| `AWS_SECRET_ACCESS_KEY` (R2) | quarterly | Cloudflare R2 dashboard | Use scoped credentials |
| Database password | annually | Railway add-on console | Triggers rolling restart |
| `SENTRY_DSN` | only on incident | Sentry org settings | Rotate after any leak |

## Phase status

- [x] Phase 0: Research & Reference docs
- [x] Phase 1: Foundation — DONE
- [x] Phase 2: Content System — scaffold + tests
- [x] Phase 3: AI Lead Magnets — description writer wired, furniture remover stub
- [x] Phase 4: Forum — full Reddit-shape scaffold + voting tests
- [x] Phase 5: Marketplace — full data model + service/lead UI + tests
- [x] Phase 6: Control Surfaces — operator dashboard + mod queue
- [x] Phase 7: Social Integration — SocialEmbed + YouTube/Instagram resolver
- [x] Phase 8: Production Polish — sitemap + robots + final security review

**Final state**: 86 tests passing, prod `check --deploy` clean, all migrations applied,
9 apps live. See `docs/SECURITY-FINAL.md` for outstanding follow-ups by phase.

See `.planning/phases/phase-N-<name>/PLAN.md` for each phase's detailed plan.
Master plan: `C:\Users\vladi\.claude\plans\create-a-local-real-tranquil-koala.md`
