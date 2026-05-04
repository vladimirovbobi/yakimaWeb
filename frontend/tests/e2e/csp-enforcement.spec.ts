import { test, expect } from "@playwright/test";

test.describe("CSP enforcement", () => {
  test("homepage emits Content-Security-Policy with a nonce", async ({ page }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    const csp = response!.headers()["content-security-policy"];
    expect(csp, "CSP header must be set").toBeTruthy();
    expect(csp).toContain("script-src");
    expect(csp).toMatch(/'nonce-[A-Za-z0-9+/=]+'/);
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("base-uri 'self'");
    expect(csp).toContain("object-src 'none'");
  });

  test("inline JSON-LD scripts carry the same nonce", async ({ page }) => {
    const response = await page.goto("/");
    const csp = response!.headers()["content-security-policy"] || "";
    const match = csp.match(/'nonce-([A-Za-z0-9+/=]+)'/);
    expect(match, "nonce extractable from CSP").toBeTruthy();
    const headerNonce = match![1];

    const scriptNonces = await page.$$eval(
      'script[type="application/ld+json"]',
      (els) => els.map((e) => (e as HTMLScriptElement).nonce || ""),
    );

    expect(scriptNonces.length).toBeGreaterThan(0);
    for (const n of scriptNonces) {
      expect(n, "every JSON-LD script nonce matches CSP").toBe(headerNonce);
    }
  });

  test("no CSP violations in console on the homepage", async ({ page }) => {
    const violations: string[] = [];
    page.on("console", (msg) => {
      const text = msg.text();
      if (text.includes("Refused to") || text.toLowerCase().includes("content security policy")) {
        violations.push(text);
      }
    });
    page.on("pageerror", (e) => {
      if (e.message.toLowerCase().includes("content security policy")) {
        violations.push(e.message);
      }
    });
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    expect(violations, "no CSP violations").toEqual([]);
  });
});
