// Forum burst — 100 VUs voting + replying on a single thread for 5 min.
// Stresses VoteThrottle + atomic upsert + write contention.
//
// Pre-seed staging with: a thread @ slug=k6-burst-thread, 100 disposable users.
// Set TOKENS env to a comma-separated list of JWT access tokens.
import http from "k6/http";
import { check, group, sleep } from "k6";
import { Rate } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const THREAD_SLUG = __ENV.THREAD_SLUG || "k6-burst-thread";
const TOKENS = (__ENV.TOKENS || "").split(",").filter(Boolean);

export const errorRate = new Rate("errors");
export const throttleRate = new Rate("throttled_429");

export const options = {
  vus: 100,
  duration: "5m",
  thresholds: {
    http_req_failed: ["rate<0.02"],
    "http_req_duration{action:vote}": ["p(95)<400"],
    "http_req_duration{action:reply}": ["p(95)<800"],
    throttled_429: ["rate<0.30"], // throttle should fire some
  },
};

function authHeaders() {
  const token = TOKENS[__VU % Math.max(TOKENS.length, 1)];
  return token
    ? { Authorization: `Bearer ${token}`, "x-csrftoken": "k6-csrf" }
    : { "x-csrftoken": "k6-csrf" };
}

export default function () {
  const baseUrl = `${BASE_URL}/api/v1/forum/threads/${THREAD_SLUG}`;

  // 70% vote, 30% reply
  const isVote = Math.random() < 0.7;

  if (isVote) {
    group("vote", () => {
      const value = Math.random() < 0.6 ? 1 : -1;
      const res = http.post(
        `${baseUrl}/vote/`,
        JSON.stringify({ value }),
        {
          headers: { "content-type": "application/json", ...authHeaders() },
          tags: { action: "vote" },
        },
      );
      const ok = check(res, {
        "ok or throttled": (r) => r.status === 200 || r.status === 429,
      });
      errorRate.add(!ok);
      if (res.status === 429) throttleRate.add(true);
      else throttleRate.add(false);
    });
  } else {
    group("reply", () => {
      const res = http.post(
        `${baseUrl}/replies/`,
        JSON.stringify({ body: `k6-reply-${__VU}-${__ITER}` }),
        {
          headers: { "content-type": "application/json", ...authHeaders() },
          tags: { action: "reply" },
        },
      );
      const ok = check(res, {
        "created or throttled": (r) => r.status === 201 || r.status === 429,
      });
      errorRate.add(!ok);
      if (res.status === 429) throttleRate.add(true);
      else throttleRate.add(false);
    });
  }

  sleep(Math.random() * 0.5 + 0.2);
}
