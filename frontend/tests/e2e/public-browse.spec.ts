import { test, expect, Page } from "@playwright/test";

/**
 * Anonymous public-browse smoke tests.
 * Assumes seed data is loaded so blog posts, services, threads exist.
 * If a list is empty (no seed), the empty-state assertion passes instead.
 */

async function clickFirstOrSkip(
  page: Page,
  locator: ReturnType<Page["locator"]>,
  emptyText: RegExp,
): Promise<boolean> {
  const count = await locator.count();
  if (count === 0) {
    const emptyState = page.getByText(emptyText).first();
    await expect(emptyState).toBeVisible();
    return false;
  }
  await locator.first().click();
  return true;
}

test.describe("public browse: anonymous", () => {
  test("blog index -> detail", async ({ page }) => {
    await page.goto("/blog");
    await expect(
      page.getByRole("heading", { name: /blog|articles|insights/i }).first(),
    ).toBeVisible();

    const postLink = page.locator('a[href^="/blog/"]').filter({
      hasNotText: /^$/,
    });
    const navigated = await clickFirstOrSkip(
      page,
      postLink,
      /no posts|nothing yet|coming soon/i,
    );

    if (navigated) {
      await expect(page).toHaveURL(/\/blog\/[^/]+/);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("services index -> category -> detail", async ({ page }) => {
    await page.goto("/services");
    await expect(
      page.getByRole("heading", { name: /services|marketplace|find/i }).first(),
    ).toBeVisible();

    // Optional: click a category filter if present
    const categoryLink = page.locator('a[href^="/services/"]').filter({
      hasNotText: /^$/,
    });
    const navigated = await clickFirstOrSkip(
      page,
      categoryLink,
      /no services|nothing yet|coming soon/i,
    );

    if (navigated) {
      await expect(page).toHaveURL(/\/services\/[^/]+/);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("community index -> flair -> thread", async ({ page }) => {
    await page.goto("/community");
    await expect(
      page.getByRole("heading", { name: /community|forum|threads/i }).first(),
    ).toBeVisible();

    const flairLink = page.locator('a[href^="/community/"]').filter({
      hasNotText: /^$/,
    });
    const navigatedFlair = await clickFirstOrSkip(
      page,
      flairLink,
      /no threads|nothing yet|coming soon/i,
    );

    if (!navigatedFlair) return;

    await expect(page).toHaveURL(/\/community\/[^/]+/);
    const threadLink = page
      .locator('a[href^="/community/threads/"]')
      .filter({ hasNotText: /^$/ });
    const navigatedThread = await clickFirstOrSkip(
      page,
      threadLink,
      /no threads|nothing yet|coming soon/i,
    );

    if (navigatedThread) {
      await expect(page).toHaveURL(/\/community\/threads\/[^/]+/);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("tools landing shows lead magnets", async ({ page }) => {
    await page.goto("/tools");
    await expect(
      page.getByRole("heading", { name: /tools|ai tools|lead magnets/i }).first(),
    ).toBeVisible();
    await expect(
      page.getByText(/furniture remover|virtual staging/i).first(),
    ).toBeVisible();
    await expect(
      page.getByText(/description writer|listing description/i).first(),
    ).toBeVisible();
  });

  for (const path of ["/about", "/guidelines", "/privacy", "/terms"]) {
    test(`${path} renders with serif title`, async ({ page }) => {
      const res = await page.goto(path);
      expect(res?.status(), `status for ${path}`).toBeLessThan(400);

      const h1 = page.getByRole("heading", { level: 1 });
      await expect(h1).toBeVisible();

      // Cormorant Garamond is the serif font
      const fontFamily = await h1.evaluate(
        (el) => window.getComputedStyle(el).fontFamily,
      );
      expect(fontFamily.toLowerCase()).toMatch(/cormorant|serif/);
    });
  }
});
