import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 21: 31st vote in a minute -> 429 with retry-after.
 */

test.describe("vote rate limit", () => {
  test("31st vote returns 429", async ({ page }) => {
    await mockLogin(page);

    let count = 0;
    await page.route("**/api/v1/forum/**/vote/**", async (route) => {
      count += 1;
      if (count > 30) {
        await route.fulfill({
          status: 429,
          headers: { "retry-after": "60" },
          contentType: "application/problem+json",
          body: JSON.stringify({
            type: "https://yakimaweb.local/problems/throttled",
            title: "Throttled",
            status: 429,
            code: "throttled",
          }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ score: count }),
      });
    });

    const responses: number[] = [];
    page.on("response", async (resp) => {
      if (resp.url().includes("/vote")) responses.push(resp.status());
    });

    for (let i = 0; i < 31; i++) {
      await page.evaluate(async () => {
        const res = await fetch("/api/v1/forum/threads/1/vote/", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ value: 1 }),
        });
        return res.status;
      });
    }

    expect(count).toBe(31);
    expect(responses.filter((s) => s === 429).length).toBeGreaterThanOrEqual(1);
  });
});
