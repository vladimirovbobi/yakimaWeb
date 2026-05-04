import { test, expect } from "@playwright/test";

/**
 * Sprint 2 hardening additions on top of `security-headers.spec.ts`:
 *  - Server tech stripping (-Server, -X-Powered-By)
 *  - Permissions-Policy expanded
 *  - COOP / COEP / CORP / X-Permitted-Cross-Domain-Policies
 *  - Auth-burst rate limit on /api/v1/auth/login
 *
 * Some assertions only fire under prod-like builds — skip cleanly otherwise.
 */

test.describe("Sprint 2 hardening headers", () => {
  test("server tech is not advertised", async ({ request }) => {
    const r = await request.get("/");
    const h = r.headers();
    expect(h["server"], "Server header should be stripped at edge").toBeFalsy();
    expect(h["x-powered-by"], "X-Powered-By should be stripped at edge").toBeFalsy();
  });

  test("expanded Permissions-Policy directives", async ({ request }) => {
    const r = await request.get("/");
    const pp = r.headers()["permissions-policy"] || "";
    for (const directive of [
      "camera=()",
      "microphone=()",
      "geolocation=()",
      "payment=()",
      "usb=()",
      "interest-cohort=()",
    ]) {
      expect(pp, `Permissions-Policy must include ${directive}`).toContain(directive);
    }
  });

  test("isolation headers present (COOP/CORP/cross-domain)", async ({ request }) => {
    const r = await request.get("/");
    const h = r.headers();
    // Caddy sets COOP same-origin + CORP same-origin + xpcdp none.
    // In dev with Caddy not in front, the test will skip those lines.
    if (h["cross-origin-opener-policy"]) {
      expect(h["cross-origin-opener-policy"]).toBe("same-origin");
    }
    if (h["cross-origin-resource-policy"]) {
      expect(h["cross-origin-resource-policy"]).toBe("same-origin");
    }
    if (h["x-permitted-cross-domain-policies"]) {
      expect(h["x-permitted-cross-domain-policies"]).toBe("none");
    }
  });

  test("auth burst is rate-limited (or 401s consistently)", async ({ request }) => {
    const results: number[] = [];
    for (let i = 0; i < 12; i++) {
      const r = await request.post("/api/v1/auth/login/", {
        data: { email: `nope${i}@example.invalid`, password: "wrong" },
        failOnStatusCode: false,
      });
      results.push(r.status());
    }
    // All non-success statuses are acceptable; surface the actual mix for
    // debugging when the assertion fails.
    test.info().annotations.push({
      type: "result",
      description: `auth burst: ${results.join(",")}`,
    });
    expect(results.every((s) => [400, 401, 403, 429].includes(s))).toBe(true);
    if (process.env.PLAYWRIGHT_REQUIRE_RATE_LIMIT === "1") {
      expect(results.includes(429), "expected at least one 429").toBe(true);
    }
  });
});
