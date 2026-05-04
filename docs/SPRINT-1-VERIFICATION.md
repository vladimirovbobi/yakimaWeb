# Sprint 1 — Verification & Real-API Wiring Guide

Steps to verify Sprint 1 deliverables and wire real third-party API keys.

## What Sprint 1 shipped

- Welcoming homepage (question-driven hero, curated feed, no services revealed above the fold)
- SEO scaffolding: `lib/seo.ts`, `app/sitemap.ts`, `app/robots.ts`, Organization+WebSite JSON-LD in root layout, OG/Twitter defaults
- Per-page metadata templates ready for blog/community/vendor/service pages
- Extended seed pack: ~9 more org posts, 15 more realtor posts, 39 more forum threads, comments, replies, 21 more vendors, ~63 services, 5 cross-service bundles, ~150 leads, ~120 reviews
- Asset acquisition pipeline doc (`scripts/seed_assets/README.md`)
- Design drift audit confirming zero drift vs `1301-2nd-street-yakima` reference

## How to verify locally

### 1. Run the seed pipeline

```bash
docker compose up -d
docker compose --profile migrate run --rm migrate
docker compose exec api python manage.py createsuperuser  # if not already
docker compose exec api python manage.py seed_all
```

Expected output:

```
→ Categories
→ Forum flairs
→ Brokerages
→ Moderation action templates
→ Demo content (base)              org=3, blogs=5, threads=10, embeds=3
→ Demo marketplace (base)          services=5, packages=15, bundles=1, leads=3, reviews=3
→ Extended posts + threads + ...   org_posts=8, realtor_posts=15, threads=39, replies=~200, comments=~80
→ Extended marketplace             services=21, packages=63, bundles=5, leads=~150, reviews=~120
seed_all done.
```

### 2. Walk the public pages

Visit via Caddy at <http://localhost>:

- `/` — welcoming hero ("Where Yakima talks about home"), featured story card, mixed feed of posts + threads, verified-realtor strip, newsletter card, low-key realtor verify CTA at bottom. **No marketplace/services links above the fold.**
- `/blog` — paginated post index with filtering
- `/blog/{slug}` — individual posts with comments
- `/community` — forum thread index, sortable
- `/community/threads/{slug}` — thread detail with replies
- `/services` — vendor list with packages and prices
- `/services/{slug}` — service detail
- `/services/vendors/{slug}` — vendor profile
- `/about`, `/guidelines`, `/privacy`, `/terms`, `/videos`, `/tools` — static / static-ish pages

### 3. Check SEO scaffolding

```bash
curl http://localhost/sitemap.xml | head -40
curl http://localhost/robots.txt
curl -s http://localhost/ | grep -E '"@type":|og:|canonical|description'
```

Expected: sitemap has static + dynamic entries; robots disallows /api/, /dashboard/,
/admin/; HTML has Organization + WebSite JSON-LD, og:* meta tags, canonical link.

### 4. Lighthouse + axe-core

```bash
docker compose exec frontend npx lighthouse http://localhost/ --view --quiet --chrome-flags="--headless"
docker compose exec frontend npx @axe-core/cli http://localhost/
```

Targets: Lighthouse Performance/Accessibility/Best-Practices/SEO ≥ 90 on the
homepage. axe-core: zero serious or critical issues.

## How to wire real API keys

### ARELLO (license verification)

```bash
# In .env (root, never commit):
ARELLO_BASE_URL=https://services.arello.com
ARELLO_API_KEY=<real-key>

# Verify the wiring is real, not the mock:
docker compose exec api python manage.py shell -c "
from apps.accounts.services.arello import ArelloClient
c = ArelloClient()
print(c.verify_license('<real-license-number>', surname='<real-surname>'))
"
```

Expected: HTTP 200, real status code, `mocked=False` on the response object.
Mock fallback only activates when `ARELLO_API_KEY` is unset.

### Gemini (AI moderation + tools)

```bash
# In .env:
GEMINI_API_KEY=<real-key>
GEMINI_MODERATION_MODEL=gemini-2.5-flash
GEMINI_TOOL_MODEL=gemini-2.5-pro

# Verify real Gemini call:
docker compose exec api python manage.py shell -c "
from apps.moderation.services.ai_classifier import classify
print(classify('Test post for verification.', context={'kind': 'post'}))
"
```

Expected: real JSON response from Gemini with `{allowed, categories, severity, action}`.

### Postmark (transactional email)

```bash
# In .env:
POSTMARK_SERVER_TOKEN=<real-token>
DEFAULT_FROM_EMAIL=hello@yakimaweb.com
EMAIL_BACKEND=anymail.backends.postmark.EmailBackend

# Send test mail:
docker compose exec api python manage.py sendtestemail your.email@example.com
```

Expected: email arrives. Bounce report visible in Postmark dashboard.

### Cloudflare R2 (object storage)

```bash
# In .env:
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret>
AWS_S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_STORAGE_BUCKET_NAME=yakimaweb-prod
AWS_S3_CUSTOM_DOMAIN=cdn.yakimaweb.com

# Test upload:
docker compose exec api python manage.py shell -c "
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
path = default_storage.save('test.txt', ContentFile(b'hello'))
print('Saved to:', default_storage.url(path))
"
```

Expected: signed URL returned; file fetchable; CDN URL serves content.

### Sentry (error monitoring)

```bash
# In .env:
SENTRY_DSN=https://<key>@<org>.ingest.sentry.io/<project>
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.05
SENTRY_ENVIRONMENT=dev

# Trigger test event:
docker compose exec api python manage.py shell -c "
import sentry_sdk
sentry_sdk.capture_message('Sprint 1 verification test', level='info')
"
```

Expected: event in Sentry dashboard within 60s.

## Caddy routing for sitemap/robots

`/sitemap.xml` and `/robots.txt` must be served by **Next.js**, not Django.
Verify Caddy's reverse-proxy rules in `caddy/Caddyfile` match `/api/*` and
`/admin/*` to the api service and **everything else** to frontend (which
includes sitemap.xml and robots.txt routes). Test:

```bash
curl -sI http://localhost/sitemap.xml | grep -i "x-powered\|server"
```

Expected: served by Next.js, not gunicorn/uvicorn.

## Sprint 1 sign-off checklist

- [ ] `docker compose up -d` brings all 8 services up; `curl http://localhost/healthz` returns 200
- [ ] `seed_all` runs clean to completion; counts match expected output above
- [ ] Homepage renders with welcoming question hero and curated feed; no service prices/links above fold
- [ ] `/blog`, `/community`, `/services`, `/services/vendors/<slug>` all render with seed data
- [ ] `/sitemap.xml` returns ≥ 100 entries (static + posts + threads + vendors + services)
- [ ] `/robots.txt` disallows admin/dashboard/auth surfaces
- [ ] HTML source on `/` contains Organization + WebSite JSON-LD
- [ ] OG image renders correctly when sharing to Slack/Discord/Twitter
- [ ] Lighthouse score ≥ 90 on Performance, Accessibility, Best-Practices, SEO
- [ ] axe-core: zero serious/critical violations
- [ ] All 5 real-API integrations verified (or noted as deferred to Sprint 2 if keys aren't yet provisioned)
- [ ] `pytest`, `ruff check`, `ruff format --check`, `djlint templates/`, `npm --prefix frontend run lint`, `npm --prefix frontend run test:e2e -- --grep="homepage"` all green
- [ ] Sprint 1 commit pushed; `docs/STATE-OF-THE-PROJECT.md` updated
