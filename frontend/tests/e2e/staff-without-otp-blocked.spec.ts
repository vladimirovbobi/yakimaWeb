import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 26: Staff without OTP -> /dashboard/ops -> 403 until OTP verified.
 */

test.describe("staff without OTP blocked", () => {
  test("staff w/o otp -> 403 -> OTP step required", async ({ page }) => {
    await mockLogin(page, "demo-operator@yakimaweb.local");

    await page.route("**/api/public/v1/auth/me/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          email: "demo-operator@yakimaweb.local",
          is_authenticated: true,
          roles: ["member", "staff", "operator"],
          otp_verified: false,
        }),
      });
    });

    await page.route("**/api/v1/ops/**", async (route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/problem+json",
        body: JSON.stringify({
          type: "https://yakimaweb.local/problems/otp-required",
          title: "OTP required",
          status: 403,
          code: "otp_required",
        }),
      });
    });

    await page.goto("/dashboard/ops");

    // Either redirected to /2fa/verify or sees OTP banner
    await page.waitForLoadState("networkidle");
    const url = page.url();
    const isOtpFlow =
      /\/2fa\/?/.test(url) ||
      /\/login\/?/.test(url);

    if (!isOtpFlow) {
      await expect(
        page.getByText(/two-factor|otp|verify identity|second step/i).first(),
      ).toBeVisible({ timeout: 5_000 });
    }
  });
});
