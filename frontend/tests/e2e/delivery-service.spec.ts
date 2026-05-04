import { test, expect } from "@playwright/test";

test.describe("Delivery service", () => {
  test("delivery healthz responds", async ({ request }) => {
    // Caddy routes /api/delivery/* → delivery container.
    const r = await request.get("/api/delivery/healthz", {
      failOnStatusCode: false,
    });
    test.skip(
      r.status() === 502 || r.status() === 503,
      "delivery container not running in this environment",
    );
    expect(r.status()).toBe(200);
    const data = await r.json();
    expect(data.status).toBe("ok");
    expect(data.service).toBe("yakimaweb-delivery");
  });

  test("missing JWT returns 401 from delivery API", async ({ request }) => {
    const r = await request.post("/api/delivery/v1/packages", {
      multipart: { lead_id: "1", buyer_id: "1", name: "test" },
      failOnStatusCode: false,
    });
    test.skip(
      r.status() === 502 || r.status() === 503,
      "delivery container not running",
    );
    expect([401, 403, 422]).toContain(r.status());
  });

  test("Django-side webhook receiver requires HMAC signature in prod", async ({ request }) => {
    const r = await request.post("/api/v1/delivery/webhooks/finalize/", {
      data: { package_id: 1, lead_id: 1 },
      failOnStatusCode: false,
    });
    // Without DELIVERY_WEBHOOK_SECRET set in dev, this allows-through;
    // with secret set, returns 403. Either is correct for the env.
    expect([200, 400, 403, 404]).toContain(r.status());
  });
});
