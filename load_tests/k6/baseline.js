// Baseline browse test — 1K concurrent VUs, 10 min, mixed GET on public API.
// Approximates 10K MAU steady state.
//
// Run:
//   k6 run load_tests/k6/baseline.js -e BASE_URL=https://staging.yakimaweb.com
import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const errorRate = new Rate("errors");
export const apiLatency = new Trend("api_latency_ms", true);

export const options = {
  scenarios: {
    browse: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "1m", target: 250 },
        { duration: "1m", target: 500 },
        { duration: "1m", target: 1000 },
        { duration: "5m", target: 1000 },
        { duration: "1m", target: 500 },
        { duration: "1m", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"], // <1% errors
    http_req_duration: ["p(95)<500", "p(99)<1500"],
    errors: ["rate<0.02"],
  },
};

const ENDPOINTS = [
  { weight: 4, path: "/api/public/v1/posts/?limit=20" },
  { weight: 3, path: "/api/public/v1/services/?limit=20" },
  { weight: 2, path: "/api/public/v1/community/threads/?limit=20" },
  { weight: 1, path: "/api/public/v1/meta/healthz/" },
  { weight: 2, path: "/api/public/v1/posts/?category=market-update" },
  { weight: 1, path: "/api/public/v1/services/?category=photography" },
];

function pickEndpoint() {
  const total = ENDPOINTS.reduce((s, e) => s + e.weight, 0);
  let r = Math.random() * total;
  for (const e of ENDPOINTS) {
    if (r < e.weight) return e.path;
    r -= e.weight;
  }
  return ENDPOINTS[0].path;
}

export default function () {
  group("browse_mixed", () => {
    const path = pickEndpoint();
    const url = `${BASE_URL}${path}`;
    const res = http.get(url, {
      headers: { "user-agent": "k6/yakimaweb-baseline" },
      tags: { endpoint: path.split("?")[0] },
    });
    apiLatency.add(res.timings.duration);
    const ok = check(res, {
      "status 200": (r) => r.status === 200,
      "json body": (r) =>
        (r.headers["Content-Type"] || "").includes("application/json"),
    });
    errorRate.add(!ok);
  });
  sleep(Math.random() * 2 + 1); // 1-3s think time
}

export function handleSummary(data) {
  return { stdout: JSON.stringify(data, null, 2) };
}
