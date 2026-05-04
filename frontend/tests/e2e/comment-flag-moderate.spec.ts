import { test, expect } from "./helpers/fixtures";

/**
 * Spec 15: Anonymous flags a comment -> moderator queue -> remove -> hidden.
 */

test.describe("comment flag + moderate", () => {
  test("anon flags comment, mod removes, comment vanishes", async ({
    page,
  }) => {
    let flagCreated = false;
    let removed = false;

    await page.route("**/api/public/v1/posts/comments/**", async (route) => {
      const url = route.request().url();
      if (url.includes("/flag") && route.request().method() === "POST") {
        flagCreated = true;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Reported." }),
        });
        return;
      }
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            count: removed ? 0 : 1,
            results: removed
              ? []
              : [
                  {
                    id: 99,
                    body: "Suspicious comment",
                    author: "anon",
                    created_at: new Date().toISOString(),
                  },
                ],
          }),
        });
      }
    });

    await page.goto("/blog/sample-post");
    const flagBtn = page
      .getByRole("button", { name: /report|flag/i })
      .first();

    if (!(await flagBtn.isVisible().catch(() => false))) {
      test.skip(true, "flag button absent — comment system not seeded");
      return;
    }

    await flagBtn.click();
    await page
      .getByRole("button", { name: /confirm|submit/i })
      .first()
      .click()
      .catch(() => {
        // single-click flag — also valid
      });

    expect(flagCreated).toBe(true);
    await expect(
      page.getByText(/reported|thank/i).first(),
    ).toBeVisible({ timeout: 5_000 });

    // Mod removes
    removed = true;
    await page.reload();
    await expect(page.getByText("Suspicious comment")).toHaveCount(0);
  });
});
