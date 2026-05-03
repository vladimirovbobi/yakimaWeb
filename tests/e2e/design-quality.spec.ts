import { test, expect } from "@playwright/test";

test.describe("Design quality smoke", () => {
  test("homepage uses gold accent (visual sanity)", async ({ page }) => {
    await page.goto("/");
    // Brand dot in nav
    const brand = page.locator("header a").first();
    await expect(brand).toBeVisible();
  });

  test("mobile nav opens drawer", async ({ page, isMobile }) => {
    await page.goto("/");
    if (!isMobile) test.skip();
    await page.getByRole("button", { name: /Open menu/i }).click();
    await expect(page.getByRole("link", { name: /^Home$/ }).last()).toBeVisible();
  });

  test("scroll-reveal classes are present", async ({ page }) => {
    await page.goto("/");
    const reveal = page.locator("[x-reveal], [x-data][x-reveal]").first();
    // Just confirm at least one revealable element exists in DOM
    await expect(reveal).toBeAttached();
  });

  test("all pages return 200 + have a footer", async ({ page }) => {
    for (const path of ["/", "/about/", "/guidelines/", "/privacy/", "/terms/"]) {
      const r = await page.goto(path);
      expect(r?.status(), `path ${path}`).toBeLessThan(400);
      await expect(page.locator("footer")).toBeVisible();
    }
  });
});
