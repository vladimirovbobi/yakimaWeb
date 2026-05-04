import { test, expect } from "@playwright/test";

test.describe("SEO scaffolding", () => {
  test("/sitemap.xml is served by Next.js with at least the static routes", async ({ request }) => {
    const r = await request.get("/sitemap.xml");
    expect(r.status()).toBe(200);
    const xml = await r.text();
    expect(xml).toContain("<urlset");
    // Static routes from app/sitemap.ts
    for (const path of ["/", "/about", "/blog", "/community", "/services", "/tools"]) {
      expect(xml).toContain(`</loc>`);
      expect(xml).toContain(path);
    }
  });

  test("/robots.txt disallows admin + dashboard surfaces", async ({ request }) => {
    const r = await request.get("/robots.txt");
    expect(r.status()).toBe(200);
    const txt = await r.text();
    for (const path of [
      "/api/",
      "/admin/",
      "/dashboard/",
      "/account/",
      "/realtor/",
      "/vendor/",
      "/mod/",
      "/ops/",
    ]) {
      expect(txt).toContain(`Disallow: ${path}`);
    }
    expect(txt).toContain("Sitemap: ");
  });

  test("homepage emits Organization + WebSite JSON-LD", async ({ page }) => {
    await page.goto("/");
    const ldBlocks = await page.$$eval(
      'script[type="application/ld+json"]',
      (els) => els.map((e) => e.textContent || ""),
    );
    const joined = ldBlocks.join("\n");
    expect(joined).toContain('"@type":"Organization"');
    expect(joined).toContain('"@type":"WebSite"');
  });

  test("homepage Open Graph + Twitter meta present", async ({ page }) => {
    await page.goto("/");
    const ogTitle = await page.locator('meta[property="og:title"]').getAttribute("content");
    const ogType  = await page.locator('meta[property="og:type"]').getAttribute("content");
    const twCard  = await page.locator('meta[name="twitter:card"]').getAttribute("content");
    expect(ogTitle, "og:title").toBeTruthy();
    expect(ogType, "og:type").toBe("website");
    expect(twCard, "twitter:card").toBe("summary_large_image");
  });
});
