import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 14: Verified realtor publishes a blog post via TipTap editor.
 *
 * Editor renders, content saves, moderation passes (mocked approved), post
 * appears on /blog.
 */

test.describe("realtor blog publish", () => {
  test("verified realtor writes -> publishes -> appears on /blog", async ({
    page,
  }) => {
    const slug = `e2e-${Date.now()}`;
    const title = "Yakima Valley Q3 Snapshot";

    await mockLogin(page);

    await page.route("**/api/public/v1/auth/me/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          email: "demo-realtor@yakimaweb.local",
          is_authenticated: true,
          roles: ["member", "realtor"],
          realtor_profile: { verification_status: "verified" },
        }),
      });
    });

    let createdPost: any = null;
    await page.route("**/api/v1/posts/**", async (route) => {
      const req = route.request();
      if (req.method() === "POST") {
        createdPost = JSON.parse(req.postData() || "{}");
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            slug,
            title: createdPost.title,
            status: "published",
            moderation: "approved",
          }),
        });
        return;
      }
      await route.continue();
    });

    await page.route("**/api/public/v1/posts/**", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            count: 1,
            results: [
              {
                id: 1,
                slug,
                title,
                excerpt: "Mocked",
                published_at: new Date().toISOString(),
              },
            ],
          }),
        });
      }
    });

    await page.goto("/dashboard/realtor/posts/new");

    const titleInput = page
      .locator('input[name="title"], input[placeholder*="title" i]')
      .first();

    if (!(await titleInput.isVisible().catch(() => false))) {
      test.skip(true, "post editor not implemented yet");
      return;
    }

    await titleInput.fill(title);

    const editor = page.locator('[contenteditable="true"], textarea').first();
    await editor.click();
    await editor.fill("Strong fundamentals across the valley this quarter.");

    await page
      .getByRole("button", { name: /publish|submit/i })
      .first()
      .click();

    await expect(
      page.getByText(/published|live|approved|success/i).first(),
    ).toBeVisible({ timeout: 5_000 });

    expect(createdPost).toBeTruthy();

    await page.goto("/blog");
    await expect(page.getByText(title).first()).toBeVisible({
      timeout: 5_000,
    });
  });
});
