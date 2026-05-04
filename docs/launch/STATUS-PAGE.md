# Yakima Web — Status Page

Public status URL: https://status.yakimaweb.com (CNAME to Better Stack).

## Components to monitor

| Component | What is monitored | Probe |
|---|---|---|
| Homepage | https://yakimaweb.com/ | HTTP 200 + body contains "Central Washington" |
| Public API | /api/public/v1/meta/healthz/ | HTTP 200 + JSON `{"status":"ok"}` |
| Auth flow | /api/public/v1/auth/me/ (anonymous) | HTTP 200 with `is_authenticated:false` |
| Marketplace search | /api/public/v1/services/?limit=1 | HTTP 200, latency p95 < 800ms |
| Forum | /api/public/v1/community/threads/?limit=1 | HTTP 200 |
| AI tools — furniture remover | /api/v1/tools/furniture-remover/health/ | HTTP 200 + `gemini_reachable:true` |
| AI tools — description writer | /api/v1/tools/description-writer/health/ | HTTP 200 + `gemini_reachable:true` |
| Mod queue depth | Internal metric | Pages on >100 backlog older than 1h |

The two AI components are rolled into a single "AI tools" group on the public
page so a Gemini outage shows as one row, not two.

## Probe cadence

- Homepage + Public API: 30s.
- Auth + marketplace + forum: 60s.
- AI tools: 5m (Gemini calls cost real money; do not poll harder).
- Mod queue: 5m (read from Postgres via internal exporter).

## Component grouping

Public components (visible on status.yakimaweb.com):

- Web (Homepage)
- API (Public API + Auth)
- Marketplace
- Forum
- AI Tools

Operational components (private dashboard for on-call only):

- Postgres primary
- Redis
- Celery worker (`celery`)
- Celery worker (`images`)
- Celery beat
- Caddy
- Object storage (R2)
- Sentry ingestion

## Incident severity tiers

| Tier | Symptom | Response time | Public update |
|---|---|---|---|
| Sev-1 | Site down or data loss | 15 min | Within 30 min |
| Sev-2 | Major feature broken | 1 hour | Within 1 hour |
| Sev-3 | Degraded performance | 4 hours | Within 4 hours |
| Sev-4 | Single-user issue | Next business day | None |

## Status update template

```
[INVESTIGATING / IDENTIFIED / MONITORING / RESOLVED]

We are seeing [symptom]. [Affected component] is impacted.

Started: [time PT]
Last update: [time PT]
Next update: in [duration] or when status changes.

Workaround: [if any]
```

## Better Stack setup

- Project: yakimaweb-prod
- Status page: status.yakimaweb.com
- Heartbeats: 5m for homepage probe, 10m for Celery beat heartbeat
- Escalation: PagerDuty -> on-call phone -> founder phone

## DNS

```
status.yakimaweb.com.  3600  CNAME  status.betterstack.com.
```

## Maintenance windows

- Routine deploys: any time, blue/green via Railway.
- Heavy migration: Tuesday 2 AM PT, announce 24h ahead on status page.
- Scheduled downtime: never on a Tuesday or Thursday during business hours
  (Yakima Valley realtors host open houses on those days — don't break their
  workflow).
