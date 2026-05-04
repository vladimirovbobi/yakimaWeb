# Yakima Web load tests (k6)

These scripts validate that the Phase 1 stack hits its 10K MAU SLOs before
public launch. All scripts are idempotent against a staging deploy — never
point at production unless explicitly coordinated with on-call.

## Prereqs

- Install k6: <https://k6.io/docs/get-started/installation/>
- A staging deploy with seed data (run `manage.py seed_demo` against staging).
- For authenticated scripts: pre-mint JWT access tokens for k6 VUs and pass via
  the `TOKENS` env var. Throwaway accounts only.

## Scripts

| Script | What it validates |
|---|---|
| `baseline.js` | 1K concurrent VUs browsing public API (10 min). Hits the 10K MAU SLO. |
| `forum_burst.js` | 100 VUs voting + replying on one thread (5 min). Validates VoteThrottle + write contention. |
| `ai_tool.js` | 50 VUs running the description writer (10 min). Validates `GEMINI_DAILY_SPEND_CAP_USD`. |
| `sustained.js` | 50 VUs, 24-hour soak. Catches memory leaks + connection-pool exhaustion. |

## Running against staging

```bash
k6 run load_tests/k6/baseline.js \
  -e BASE_URL=https://staging.yakimaweb.com \
  --out json=results-baseline.json

k6 run load_tests/k6/forum_burst.js \
  -e BASE_URL=https://staging.yakimaweb.com \
  -e THREAD_SLUG=k6-burst-thread \
  -e TOKENS="$(cat tokens.txt | tr '\n' ',')" \
  --out json=results-forum.json

k6 run load_tests/k6/ai_tool.js \
  -e BASE_URL=https://staging.yakimaweb.com \
  -e TOKENS="$(cat tokens.txt | tr '\n' ',')" \
  --out json=results-ai.json

k6 run load_tests/k6/sustained.js \
  -e BASE_URL=https://staging.yakimaweb.com \
  --out json=results-soak.json
```

## Pass criteria

- p95 latency under the threshold declared in each script.
- HTTP error rate < 1 percent (transient 503s allowed during soak).
- 429s appear in `forum_burst` and `ai_tool` runs — not appearing means a
  throttle is misconfigured.
- 24-hour soak finishes without OOM kill and without resident memory growth
  > 30 percent over the run.

## Reading results

`k6 run --out json=...` writes one JSON object per metric sample. Pipe through
`jq` for ad-hoc analysis:

```bash
jq -r 'select(.type=="Point") | [.metric, .data.value] | @csv' results-baseline.json \
  | awk -F, '$1=="\"http_req_duration\"" { sum+=$2; n++ } END { print "avg ms:", sum/n }'
```

Better Stack ingests these JSON streams directly — wire the run into the
`load-test` log source for a flame graph + per-endpoint p95 chart.

## Production readiness checklist

- [ ] `baseline.js` passes against staging.
- [ ] `forum_burst.js` passes — throttle fires.
- [ ] `ai_tool.js` passes — spend cap fires.
- [ ] `sustained.js` runs for 24h without alerts.
- [ ] All four runs are linked from `docs/launch/LAUNCH-CHECKLIST.md` Day -3.
