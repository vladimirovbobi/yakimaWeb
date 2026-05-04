import { test, expect } from "./helpers/fixtures";

/**
 * Logged-in user comments on a blog post.
 *
 * Network-mocked by default: the comment POST is intercepted and replies with
 * a pending-moderation comment. Set E2E_USE_REAL_AUTH=1 + ensure seed data is
 * present to drive the real API.
 */

const REAL = process.env.E2E_USE_REAL_AUTH === "1";

test.describe("blog comment flow", () => {
  test("authed user can submit a comment and see it as pending", async ({
    authedPage: page,
  }) => {
    await page.goto("/blog");
    const postLink = page.locator('a[href^="/blog/"]').first();
    if ((await postLink.count()) === 0) {
      test.skip(true, "No seed blog posts");
      return;
    }
    await postLink.click();
    await expect(page).toHaveURL(/\/blog\/[^/]+/);

    const commentInput = page
      .locator('textarea[name*="comment" i], textarea[name*="body" i], textarea')
      .first();
    if ((await commentInput.count()) === 0) {
      test.skip(true, "Comment form not yet built");
      return;
    }

    const body = `E2E comment ${Date.now()}`;

    if (!REAL) {
      await page.route("**/api/public/v1/comments/**", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 99999,
            body,
            moderation_status: "pending",
            created_at: new Date().toISOString(),
            author: { email: "demo-realtor@yakimaweb.local" },
          }),
        });
      });
    }

    await commentInput.fill(body);
    await page
      .getByRole("button", { name: /post|submit|reply|comment/i })
      .first()
      .click();

    // Either the comment shows up OR a pending-review pip appears
    await expect(
      page.getByText(body).or(page.getByText(/pending review|awaiting review/i)).first(),
    ).toBeVisible({ timeout: 10_000 });
  });
});
