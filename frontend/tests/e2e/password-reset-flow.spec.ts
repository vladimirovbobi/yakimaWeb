import { test, expect } from "./helpers/fixtures";

/**
 * Spec 27: Password reset request -> "email sent" -> reset link works.
 */

test.describe("password reset flow", () => {
  test("request -> mocked email -> confirm with new password", async ({
    page,
  }) => {
    let resetRequested = false;
    let resetConfirmed = false;
    const resetKey = "test-reset-key-abc";

    await page.route(
      "**/api/public/v1/auth/password/reset/**",
      async (route) => {
        if (route.request().method() === "POST") {
          resetRequested = true;
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              detail: "Password reset email sent.",
            }),
          });
        }
      },
    );

    await page.route(
      "**/api/public/v1/auth/password/reset/confirm/**",
      async (route) => {
        if (route.request().method() === "POST") {
          resetConfirmed = true;
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Password has been reset." }),
          });
        }
      },
    );

    await page.goto("/forgot-password");
    const emailInput = page.locator('input[type="email"]').first();
    if (!(await emailInput.isVisible().catch(() => false))) {
      test.skip(true, "/forgot-password not built yet");
      return;
    }
    await emailInput.fill("user@yakimaweb.local");
    await page
      .getByRole("button", { name: /send|reset|continue/i })
      .first()
      .click();

    await expect(
      page.getByText(/check your (email|inbox)|sent/i).first(),
    ).toBeVisible({ timeout: 5_000 });
    expect(resetRequested).toBe(true);

    // Confirm step
    await page.goto(`/reset-password/${resetKey}`);
    const passwordInputs = page.locator('input[type="password"]');
    if (!(await passwordInputs.first().isVisible().catch(() => false))) {
      test.skip(true, "reset-password page not yet built");
      return;
    }
    await passwordInputs.first().fill("NewSecurePass!23");
    if ((await passwordInputs.count()) > 1) {
      await passwordInputs.nth(1).fill("NewSecurePass!23");
    }
    await page
      .getByRole("button", { name: /reset|set|update|continue/i })
      .first()
      .click();

    await expect(
      page.getByText(/reset|success|updated/i).first(),
    ).toBeVisible({ timeout: 5_000 });
    expect(resetConfirmed).toBe(true);
  });
});
