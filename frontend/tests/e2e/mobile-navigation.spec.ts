import { test, expect } from "@playwright/test";

/**
 * Mobile-only navigation tests. Skipped on the desktop project.
 */

test.describe("mobile navigation", () => {
  test.beforeEach(async ({}, testInfo) => {
    test.skip(
      testInfo.project.name === "chromium-desktop",
      "Mobile-only suite",
    );
  });

  test("hamburger opens overlay and routes to /services", async ({ page }) => {
    await page.goto("/");

    const hamburger = page
      .getByRole("button", { name: /menu|navigation|open menu/i })
      .first();
    await expect(hamburger).toBeVisible();
    await hamburger.click();

    const overlayNav = page.getByRole("navigation").last();
    await expect(overlayNav).toBeVisible();

    const marketplace = overlayNav
      .getByRole("link", { name: /marketplace|services/i })
      .first();
    await marketplace.click();

    await expect(page).toHaveURL(/\/services/);

    // No horizontal scroll on the destination page
    const overflow = await page.evaluate(() => {
      const html = document.documentElement;
      return html.scrollWidth > html.clientWidth + 1;
    });
    expect(overflow).toBe(false);
  });

  test("primary touch targets are >= 44x44 px", async ({ page }) => {
    await page.goto("/");

    const hamburger = page
      .getByRole("button", { name: /menu|navigation|open menu/i })
      .first();
    await expect(hamburger).toBeVisible();
    await hamburger.click();

    const overlayNav = page.getByRole("navigation").last();
    const links = await overlayNav.getByRole("link").all();
    const sample = links.slice(0, 5);

    expect(sample.length).toBeGreaterThan(0);

    for (const link of sample) {
      const box = await link.boundingBox();
      expect(box, "link bounding box").not.toBeNull();
      expect(box!.width).toBeGreaterThanOrEqual(44);
      expect(box!.height).toBeGreaterThanOrEqual(44);
    }
  });
});
