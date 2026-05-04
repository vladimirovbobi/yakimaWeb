import { test, expect, request } from "@playwright/test";

/**
 * SEO + meta-tag invariants for public surfaces.
 */

const PUBLIC_PATHS = [
  "/",
  "/blog",
  "/services",
  "/community",
  "/tools",
  "/about",
  "/guidelines",
  "/privacy",
  "/terms",
];

const seenTitles = new Map<string, string>();
const seenDescriptions = new Map<string, string>();

test.describe("SEO meta", () => {
  for (const path of PUBLIC_PATHS) {
    test(`${path}: unique title + meta description`, async ({ page }) => {
      await page.goto(path);

      const title = await page.title();
      expect(title.trim().length, `<title> on ${path}`).toBeGreaterThan(0);

      const desc = await page
        .locator('meta[name="description"]')
        .first()
        .getAttribute("content");
      expect(desc?.trim().length || 0, `meta description on ${path}`).toBeGreaterThan(
        0,
      );

      // Uniqueness across the suite
      const dupTitle = [...seenTitles.entries()].find(
        ([p, t]) => t === title && p !== path,
      );
      expect(
        dupTitle,
        `duplicate <title> "${title}" on ${path} and ${dupTitle?.[0]}`,
      ).toBeUndefined();

      const dupDesc = [...seenDescriptions.entries()].find(
        ([p, d]) => d === desc && p !== path,
      );
      expect(
        dupDesc,
        `duplicate description on ${path} and ${dupDesc?.[0]}`,
      ).toBeUndefined();

      seenTitles.set(path, title);
      seenDescriptions.set(path, desc || "");

      // Canonical
      const canonical = await page
        .locator('link[rel="canonical"]')
        .first()
        .getAttribute("href");
      expect(canonical, `canonical on ${path}`).toBeTruthy();
    });
  }

  test("blog post: OG tags + JSON-LD BlogPosting + canonical", async ({
    page,
  }) => {
    await page.goto("/blog");
    const postLink = page.locator('a[href^="/blog/"]').first();
    if ((await postLink.count()) === 0) {
      test.skip(true, "No seed blog posts");
      return;
    }
    await postLink.click();
    await expect(page).toHaveURL(/\/blog\/[^/]+/);

    const ogTitle = await page
      .locator('meta[property="og:title"]')
      .first()
      .getAttribute("content");
    const ogDesc = await page
      .locator('meta[property="og:description"]')
      .first()
      .getAttribute("content");
    const ogImage = await page
      .locator('meta[property="og:image"]')
      .first()
      .getAttribute("content");

    expect(ogTitle, "og:title").toBeTruthy();
    expect(ogDesc, "og:description").toBeTruthy();
    expect(ogImage, "og:image").toBeTruthy();

    const canonical = await page
      .locator('link[rel="canonical"]')
      .first()
      .getAttribute("href");
    expect(canonical, "canonical").toBeTruthy();

    // JSON-LD BlogPosting
    const jsonLd = await page
      .locator('script[type="application/ld+json"]')
      .allTextContents();
    const hasBlogPosting = jsonLd.some((s) => {
      try {
        const data = JSON.parse(s);
        const arr = Array.isArray(data) ? data : [data];
        return arr.some(
          (d) =>
            d?.["@type"] === "BlogPosting" ||
            d?.["@type"] === "Article" ||
            (Array.isArray(d?.["@type"]) &&
              d["@type"].some((t: string) =>
                ["BlogPosting", "Article"].includes(t),
              )),
        );
      } catch {
        return false;
      }
    });
    expect(hasBlogPosting, "JSON-LD BlogPosting/Article").toBe(true);
  });

  test("robots.txt and sitemap.xml return 200", async ({ baseURL }) => {
    const ctx = await request.newContext({ baseURL });
    try {
      const robots = await ctx.get("/robots.txt");
      expect(robots.status(), "/robots.txt").toBeLessThan(400);

      const sitemap = await ctx.get("/sitemap.xml");
      expect(sitemap.status(), "/sitemap.xml").toBeLessThan(400);
    } finally {
      await ctx.dispose();
    }
  });
});
