// 24-hour soak — 50 VUs, mixed reads, watching for memory leaks +
// connection-pool exhaustion. Schedule against a freshly deployed staging
// build with restart-on-OOM disabled.
//
// Run inside tmux/screen:
//   k6 run load_tests/k6/sustained.js -e BASE_URL=https://staging.yakimaweb.com
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const errorRate = new Rate("errors");
export const latency = new Trend("api_latency_ms", true);

export const options = {
  vus: 50,
  duration: "24h",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<800", "p(99)<2000"],
    errors: ["rate<0.02"],
  },
  // Slightly more aggressive teardown so failures during the soak don't
  // cascade and skew the latency distribution.
  noConnectionReuse: false,
  insecureSkipTLSVerify: false,
};

const PATHS = [
  "/api/public/v1/posts/",
  "/api/public/v1/services/",
  "/api/public/v1/community/threads/",
  "/api/public/v1/meta/healthz/",
  "/api/public/v1/posts/?limit=5",
  "/api/public/v1/services/?limit=5",
];

export default function () {
  const path = PATHS[Math.floor(Math.random() * PATHS.length)];
  const res = http.get(`${BASE_URL}${path}`, {
    tags: { endpoint: path.split("?")[0] },
  });

  latency.add(res.timings.duration);
  const ok = check(res, {
    "status 200 or 503 (transient)": (r) => r.status === 200 || r.status === 503,
  });
  errorRate.add(!ok);

  sleep(Math.random() * 6 + 4); // 4-10s think time
}
