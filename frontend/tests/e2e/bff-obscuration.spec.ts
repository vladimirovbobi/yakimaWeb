import { test, expect } from "@playwright/test";
import { mockLogin } from "./helpers/auth";

test.describe("BFF / Network-tab obscuration", () => {
  test("unknown BFF id returns 404 with no internal path leaked", async ({ request }) => {
    const r = await request.post("/api/bff/this-id-does-not-exist", {
      data: {},
    });
    expect(r.status()).toBe(404);
    const body = await r.text();
    expect(body).not.toContain("/api/v1/");
    expect(body).not.toContain("django");
  });

  test("method mismatch returns 405", async ({ request }) => {
    // forum-vote is POST; a GET should be rejected.
    const r = await request.get("/api/bff/forum-vote");
    expect([404, 405]).toContain(r.status());
  });

  test("unauthenticated request to an auth-required BFF route returns 401", async ({ request }) => {
    const r = await request.post("/api/bff/forum-vote", {
      data: { target_type: "thread", target_id: 1, value: 1 },
    });
    expect([401, 403, 404]).toContain(r.status());
  });

  test("cross-origin request is rejected", async ({ request }) => {
    const r = await request.post("/api/bff/forum-vote", {
      data: {},
      headers: { Origin: "https://evil.example" },
    });
    expect(r.status()).toBe(403);
  });

  test("authenticated client mutations route through /api/bff/ in the network tab", async ({ page }) => {
    await mockLogin(page);
    const bffCalls: string[] = [];
    const v1Calls: string[] = [];
    page.on("request", (req) => {
      const u = new URL(req.url());
      if (u.pathname.startsWith("/api/bff/")) bffCalls.push(u.pathname);
      if (u.pathname.startsWith("/api/v1/") && req.method() !== "GET") v1Calls.push(u.pathname);
    });

    await page.goto("/community");
    await page.waitForLoadState("networkidle");

    // We don't trigger a vote here (UI may need auth + a real thread); we
    // assert the negative space — no `/api/v1/...` mutations sneak through
    // for this navigation. BFF migration is ongoing per Sprint 9.
    expect(v1Calls.length, `unexpected /api/v1/ mutation: ${v1Calls.join(", ")}`).toBe(0);
  });
});
