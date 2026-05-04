// AI tool concurrency — 50 VUs running description-writer.
// Validates GEMINI_DAILY_SPEND_CAP_USD trips before billing rage.
//
// Set TOKENS to JWT for verified-realtor accounts.
import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Rate } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const TOKENS = (__ENV.TOKENS || "").split(",").filter(Boolean);

export const okRuns = new Counter("ai_runs_ok");
export const cappedRuns = new Counter("ai_runs_capped");
export const errorRate = new Rate("errors");

export const options = {
  vus: 50,
  duration: "10m",
  thresholds: {
    "http_req_duration{endpoint:description-writer}": ["p(95)<8000"],
    errors: ["rate<0.05"],
  },
};

const FACTS = [
  { beds: 3, baths: 2, city: "Selah", style: "ranch" },
  { beds: 4, baths: 3, city: "Yakima", style: "craftsman" },
  { beds: 2, baths: 1, city: "Naches", style: "cabin" },
  { beds: 5, baths: 4, city: "West Valley", style: "modern" },
];

function authHeaders() {
  const token = TOKENS[__VU % Math.max(TOKENS.length, 1)];
  return token
    ? { Authorization: `Bearer ${token}`, "x-csrftoken": "k6-csrf" }
    : { "x-csrftoken": "k6-csrf" };
}

export default function () {
  const facts = FACTS[Math.floor(Math.random() * FACTS.length)];
  const res = http.post(
    `${BASE_URL}/api/v1/tools/description-writer/`,
    JSON.stringify(facts),
    {
      headers: { "content-type": "application/json", ...authHeaders() },
      tags: { endpoint: "description-writer" },
      timeout: "30s",
    },
  );

  const ok = check(res, {
    "200, 202, or 429 spend cap": (r) =>
      r.status === 200 || r.status === 202 || r.status === 429,
  });

  if (res.status === 429) {
    cappedRuns.add(1);
  } else if (res.status === 200 || res.status === 202) {
    okRuns.add(1);
  }
  errorRate.add(!ok);

  sleep(Math.random() * 4 + 2); // 2-6s between runs per VU
}
