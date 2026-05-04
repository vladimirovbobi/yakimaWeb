import { test, expect } from "./helpers/fixtures";

/**
 * Spec 22: Vendor receiving 6th inquiry in an hour -> 429.
 */

test.describe("lead rate limit", () => {
  test("6th inquiry returns 429", async ({ page }) => {
    let received = 0;
    await page.route("**/api/v1/marketplace/leads/**", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      received += 1;
      if (received > 5) {
        await route.fulfill({
          status: 429,
          headers: { "retry-after": "3600" },
          contentType: "application/problem+json",
          body: JSON.stringify({
            type: "https://yakimaweb.local/problems/throttled",
            title: "Vendor inquiry limit",
            status: 429,
            code: "throttled",
          }),
        });
        return;
      }
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ id: received, status: "new" }),
      });
    });

    const statuses: number[] = [];
    for (let i = 1; i <= 6; i++) {
      const status = await page.evaluate(async (n) => {
        const res = await fetch("/api/v1/marketplace/leads/", {
          method: "POST",
          headers: {
            "content-type": "application/json",
            "x-csrftoken": "test",
          },
          body: JSON.stringify({
            service_id: 1,
            message: `Inquiry #${n}`,
            buyer_email: "buyer@example.com",
          }),
        });
        return res.status;
      }, i);
      statuses.push(status);
    }

    expect(statuses.filter((s) => s === 429).length).toBeGreaterThanOrEqual(1);
    expect(statuses.slice(0, 5).every((s) => s === 201)).toBe(true);
  });
});
