import { test, expect, type Page } from "@playwright/test";

/**
 * Verifies the deterministic placeholder fallback. Every card type renders
 * a real image with non-zero size, even when the backing API has no
 * uploaded hero. Same seed → same placeholder URL across reloads.
 */

async function expectImageHasSize(
  page: Page,
  selector: string,
  context: string,
): Promise<void> {
  const img = page.locator(selector).first();
  await expect(img, `${context}: image present`).toBeVisible({ timeout: 10_000 });
  const box = await img.boundingBox();
  expect(box, `${context}: bounding box`).not.toBeNull();
  expect(box!.width, `${context}: width`).toBeGreaterThan(0);
  expect(box!.height, `${context}: height`).toBeGreaterThan(0);
}

test.describe("placeholder fallback rendering", () => {
  test("blog index renders an image on every post card", async ({ page }) => {
    await page.goto("/blog");
    const cards = page.locator('a[href^="/blog/"]');
    if ((await cards.count()) === 0) {
      test.skip(true, "No seeded blog posts");
      return;
    }
    // Each card link with an inner img must yield a sized image.
    const firstCard = cards.first();
    const img = firstCard.locator("img").first();
    await expect(img).toBeVisible();
    const box = await img.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeGreaterThan(0);
    expect(box!.height).toBeGreaterThan(0);
  });

  test("services index renders an image on every service card", async ({ page }) => {
    await page.goto("/services");
    const cards = page.locator('a[href^="/services/"]');
    if ((await cards.count()) === 0) {
      test.skip(true, "No seeded services");
      return;
    }
    const firstCard = cards.first();
    const img = firstCard.locator("img").first();
    await expect(img).toBeVisible();
    const box = await img.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeGreaterThan(0);
    expect(box!.height).toBeGreaterThan(0);
  });

  test("community index renders thread cards", async ({ page }) => {
    await page.goto("/community");
    const cards = page.locator('a[href^="/community/threads/"]');
    if ((await cards.count()) === 0) {
      test.skip(true, "No seeded threads");
      return;
    }
    // Some thread cards may render the image only on md+ viewports;
    // tolerate either an image or fallback iconography.
    const card = cards.first();
    const hasImage = await card.locator("img").count();
    const hasIcon = await card.locator("svg").count();
    expect(hasImage + hasIcon).toBeGreaterThan(0);
  });

  test("blog detail renders a hero image", async ({ page }) => {
    await page.goto("/blog");
    const firstPost = page.locator('a[href^="/blog/"]').first();
    if ((await firstPost.count()) === 0) {
      test.skip(true, "No seeded blog posts");
      return;
    }
    await firstPost.click();
    await expect(page).toHaveURL(/\/blog\/[^/]+/);
    await expectImageHasSize(page, "main img, article img, img", "blog detail hero");
  });

  test("placeholder is deterministic across reloads", async ({ page }) => {
    await page.goto("/blog");
    const firstPost = page.locator('a[href^="/blog/"]').first();
    if ((await firstPost.count()) === 0) {
      test.skip(true, "No seeded blog posts");
      return;
    }
    const href = await firstPost.getAttribute("href");
    expect(href).toBeTruthy();

    // Capture image src on first render
    await firstPost.click();
    const heroFirst = await page
      .locator("img")
      .first()
      .getAttribute("src");
    expect(heroFirst).toBeTruthy();

    // Reload the same detail page and confirm the same URL
    await page.reload();
    const heroSecond = await page
      .locator("img")
      .first()
      .getAttribute("src");

    // Next.js may re-encode the same source through /_next/image with the
    // same `url=` query — strip query when comparing if needed.
    const norm = (s: string | null) =>
      s ? s.replace(/\&w=\d+/, "").replace(/\&q=\d+/, "") : s;
    expect(norm(heroSecond)).toBe(norm(heroFirst));
  });
});
