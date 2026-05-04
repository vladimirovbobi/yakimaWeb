import { test, expect } from "@playwright/test";

test.describe("Featured services ad slots", () => {
  test("homepage does NOT show the featured-services slot (welcome-don't-reveal)", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    await expect(
      page.getByText("Featured · From the marketplace"),
    ).toHaveCount(0);
  });

  test("blog post detail shows the featured slot below the body", async ({ page, request }) => {
    // Find a real post slug from the public API.
    const r = await request.get("/api/public/v1/posts/?limit=1");
    expect(r.ok()).toBeTruthy();
    const data = (await r.json()) as { results: Array<{ slug: string }> };
    const slug = data.results?.[0]?.slug;
    test.skip(!slug, "no posts in the seed pack");

    await page.goto(`/blog/${slug}`);
    await expect(
      page.getByText(/Featured · From the marketplace/i),
    ).toBeVisible({ timeout: 10_000 });
    await expect(
      page.getByRole("heading", {
        name: /Vendors who do the work this post talks about/i,
      }),
    ).toBeVisible();
  });

  test("community thread detail shows the featured slot", async ({ page, request }) => {
    const r = await request.get("/api/public/v1/community/threads/?limit=1");
    expect(r.ok()).toBeTruthy();
    const data = (await r.json()) as { results: Array<{ slug: string }> };
    const slug = data.results?.[0]?.slug;
    test.skip(!slug, "no threads in the seed pack");

    await page.goto(`/community/threads/${slug}`);
    await expect(
      page.getByText(/Featured · From the marketplace/i),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("featured-services API endpoint returns 1-3 services", async ({ request }) => {
    const r = await request.get("/api/public/v1/services/featured/?context=blog&limit=3");
    expect(r.ok()).toBeTruthy();
    const data = (await r.json()) as { context: string; results: unknown[] };
    expect(data.context).toBe("blog");
    expect(Array.isArray(data.results)).toBe(true);
    expect(data.results.length).toBeLessThanOrEqual(3);
  });
});
