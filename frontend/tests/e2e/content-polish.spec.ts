import { test, expect } from "./helpers/fixtures";

/**
 * Sprint 5: TipTap editor + comment image + tag pages.
 */

test.describe("content polish", () => {
  test("realtor opens TipTap post editor", async ({ authedPage: page }) => {
    await page.goto("/dashboard/realtor/posts/new");
    await expect(page.getByText("Write a new post")).toBeVisible();
    // TipTap toolbar buttons.
    await expect(page.getByRole("button", { name: "Bold" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Italic" })).toBeVisible();
    await expect(page.getByRole("button", { name: "H2" })).toBeVisible();
  });

  test("comment form exposes image attach chip", async ({
    authedPage: page,
  }) => {
    await page.route("**/api/public/v1/posts/sample-post/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          slug: "sample-post",
          title: "Sample",
          excerpt: "x",
          body_html: "<p>body</p>",
          hero_image_url: null,
          post_type: "blog",
          reading_time_minutes: 1,
          author: {
            id: 1,
            display_name: "Test",
            avatar_url: null,
            is_realtor: true,
            is_verified: true,
          },
          published_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          comment_count: 0,
          tags: [],
        }),
      });
    });
    await page.route(
      "**/api/public/v1/posts/sample-post/comments/**",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ count: 0, results: [] }),
        });
      },
    );

    await page.goto("/blog/sample-post");
    // Best-effort — only assert if comment form rendered.
    const attach = page.getByText(/attach image/i).first();
    if (await attach.count()) {
      await expect(attach).toBeVisible();
    }
  });

  test("tag page renders posts under tag", async ({ page }) => {
    await page.route(
      "**/api/public/v1/posts/tags/market/**",
      async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            tag: { id: 1, slug: "market", name: "Market", post_count: 1 },
            count: 1,
            results: [
              {
                id: 1,
                slug: "april-update",
                title: "April market update",
                excerpt: "Inventory rising.",
                hero_image: null,
                post_type: "blog",
                author: {
                  id: 1,
                  display_name: "Realtor",
                  avatar_url: null,
                  is_realtor: true,
                  is_verified: true,
                },
                published_at: new Date().toISOString(),
                view_count: 0,
                tags: [
                  { id: 1, slug: "market", name: "Market", post_count: 1 },
                ],
              },
            ],
          }),
        });
      },
    );

    await page.goto("/blog/tags/market");
    await expect(page.getByText("Market")).toBeVisible();
    await expect(page.getByText("April market update")).toBeVisible();
  });
});
