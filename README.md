# Yakima Real Estate Hub

Central Washington's home for verified realtors, trusted local services, and a real
community for buying and selling. Built with Django + HTMX + Alpine + Tailwind +
Postgres + Redis + Celery + Gemini.

## Status

**Phase 1 (Foundation) — in progress.** See [`docs/RUNBOOK.md`](docs/RUNBOOK.md)
for ops procedures and [`C:\Users\vladi\.claude\plans\create-a-local-real-tranquil-koala.md`](file:///C:/Users/vladi/.claude/plans/create-a-local-real-tranquil-koala.md)
for the master plan.

## Stack

- **Backend** — Django 5.1, Postgres 16, Redis 7, Celery + Beat
- **Frontend** — Tailwind 3.4, Alpine.js 3, Motion One, HTMX 2, Lenis
- **AI** — Google Gemini (2.5 Flash for moderation, 2.5 Pro for tools)
- **Auth** — django-allauth (email-only) + django-otp (TOTP for staff) + django-axes
- **License verification** — ARELLO API
- **Storage / CDN** — Cloudflare R2 + CDN
- **Email** — Postmark via Anymail
- **Hosting** — Railway (Phase 1) or Fly.io
- **Monitoring** — Sentry + Cloudflare logs

## Quick start

```bash
cp .env.example .env
# fill DJANGO_SECRET_KEY at minimum

uv venv && uv pip install -e . --group dev
npm install && npm run build

docker compose up -d db redis
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://localhost:8000>.

## Project layout

```
yakimaWeb/
├── apps/
│   ├── core/         shared models, base views, marketing pages
│   ├── accounts/     User, RealtorProfile, VendorProfile, ARELLO client, verify flow
│   ├── moderation/   ModeratableMixin + 3-layer Gemini pipeline + injection guard + adversarial fixtures
│   ├── audit/        ActionLog + AccessLog + signals + middleware
│   └── admin_tools/  IP allowlist + role decorators + 2FA
├── config/           settings/{base,dev,prod}, urls, celery, wsgi/asgi
├── templates/        base.html, _components/, account/, accounts/, core/
├── static/src/       Tailwind + Alpine + Motion + HTMX entry
├── docs/
│   ├── adr/          architectural decision records
│   ├── research/     vrov-new design audit, ARELLO notes, marketplace patterns, guidelines, moderation
│   └── RUNBOOK.md    operations manual
├── tests/e2e/        Playwright critical-path tests
└── .planning/phases/ per-phase detailed plans
```

## Documentation

- [Master plan](file:///C:/Users/vladi/.claude/plans/create-a-local-real-tranquil-koala.md)
- [`.planning/phases/phase-1-foundation/PLAN.md`](.planning/phases/phase-1-foundation/PLAN.md) — current phase
- [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — ops procedures
- [`docs/research/design-system-reference.md`](docs/research/design-system-reference.md) — design tokens + patterns
- [`docs/research/ai-moderation-prompt-injection.md`](docs/research/ai-moderation-prompt-injection.md) — moderation pipeline spec
- [`docs/research/arello-api-notes.md`](docs/research/arello-api-notes.md) — license verification API
- [`docs/research/platform-guidelines-v1.md`](docs/research/platform-guidelines-v1.md) — community standards
- [`docs/research/marketplace-patterns/`](docs/research/marketplace-patterns/) — Fiverr + eBay UX teardowns

## License

Proprietary. © 2026 Yakima Real Estate Hub.
