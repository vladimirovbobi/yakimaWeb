import { test, expect } from "@playwright/test";

/**
 * Security-headers invariants on the homepage.
 *
 * Some headers (HSTS) only apply over HTTPS; we skip those when the test runs
 * against http://localhost. CSP nonce check requires a production-like build;
 * we soft-skip if running in `next dev`.
 */

test("response headers on /", async ({ page, baseURL }) => {
  const response = await page.goto("/");
  expect(response, "response").not.toBeNull();
  const headers = response!.headers();

  // X-Frame-Options OR CSP frame-ancestors
  const xfo = headers["x-frame-options"];
  const csp = headers["content-security-policy"] || "";
  const frameProtected =
    /^DENY$/i.test(xfo || "") || /frame-ancestors\s+['"]?none['"]?/i.test(csp);
  expect(
    frameProtected,
    `expected X-Frame-Options DENY or CSP frame-ancestors none — got XFO=${xfo} CSP=${csp.slice(0, 200)}`,
  ).toBe(true);

  // X-Content-Type-Options
  expect(headers["x-content-type-options"]).toBe("nosniff");

  // Referrer-Policy
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");

  // HSTS only on HTTPS
  if (baseURL?.startsWith("https://")) {
    expect(headers["strict-transport-security"], "HSTS header").toBeTruthy();
  }

  // CSP nonce for script-src (only enforced if CSP header present)
  if (csp) {
    expect(csp, "script-src nonce").toMatch(/script-src[^;]*'nonce-[^']+'/);
  }
});

test("no source maps served in production build", async ({ page, baseURL }) => {
  test.skip(
    process.env.NODE_ENV !== "production",
    "source-map check only meaningful in production build",
  );

  const ctx = await page.context().request;
  const res = await ctx.get(`${baseURL}/_next/static/chunks/main.js.map`);
  expect(res.status(), "main.js.map should not be served").toBeGreaterThanOrEqual(
    400,
  );
});
