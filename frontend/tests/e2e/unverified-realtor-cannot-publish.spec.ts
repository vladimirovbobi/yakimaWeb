import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 25: Pending realtor -> /dashboard/realtor/posts/new redirects -> banner.
 */

test.describe("unverified realtor cannot publish", () => {
  test("pending status -> redirected -> banner shown", async ({ page }) => {
    await mockLogin(page);

    await page.route("**/api/public/v1/auth/me/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          email: "demo-realtor@yakimaweb.local",
          is_authenticated: true,
          roles: ["member", "realtor"],
          realtor_profile: { verification_status: "pending" },
        }),
      });
    });

    await page.goto("/dashboard/realtor/posts/new");

    // Either redirected back to dashboard, or page renders a banner
    await page.waitForLoadState("networkidle");
    const url = page.url();
    const onDashboard =
      /\/dashboard\/realtor\/?$/.test(url) ||
      /\/dashboard\/realtor(\?|$)/.test(url);

    if (!onDashboard) {
      // Page must render a clear banner
      await expect(
        page
          .getByText(/verification (pending|required)|cannot publish|verify/i)
          .first(),
      ).toBeVisible({ timeout: 5_000 });
    } else {
      await expect(
        page.getByText(/verification|pending|verify/i).first(),
      ).toBeVisible({ timeout: 5_000 });
    }
  });
});
