import { test, expect } from "@playwright/test";

/**
 * Signup + email verification flows.
 * Default: mocks the signup endpoint so tests don't require backend writes.
 * Set E2E_USE_REAL_AUTH=1 to exercise the real Django flow (unique email/run).
 */

const REAL = process.env.E2E_USE_REAL_AUTH === "1";

function uniqueEmail() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@yakimaweb.local`;
}

test.describe("signup", () => {
  test("happy path -> /verify-email-sent", async ({ page }) => {
    const email = uniqueEmail();

    if (!REAL) {
      await page.route(
        "**/api/public/v1/auth/registration/**",
        async (route) => {
          if (route.request().method() === "POST") {
            await route.fulfill({
              status: 201,
              contentType: "application/json",
              body: JSON.stringify({
                detail: "Verification e-mail sent.",
                email,
              }),
            });
            return;
          }
          await route.continue();
        },
      );
    }

    await page.goto("/signup");

    await page
      .locator('input[name="email"], input[type="email"]')
      .first()
      .fill(email);

    const passwordInputs = page.locator('input[type="password"]');
    await passwordInputs.first().fill("E2eTestPass!23");
    if ((await passwordInputs.count()) > 1) {
      await passwordInputs.nth(1).fill("E2eTestPass!23");
    }

    // Terms checkbox if present
    const terms = page.locator(
      'input[type="checkbox"][name*="terms" i], input[type="checkbox"][name*="agree" i]',
    );
    if ((await terms.count()) > 0) {
      await terms.first().check();
    }

    await page.getByRole("button", { name: /sign up|create account|register/i }).click();

    await page.waitForURL(/\/verify-email-sent/, { timeout: 10_000 });
    await expect(page.getByText(/check your (email|inbox)/i).first()).toBeVisible();
    await expect(page.getByText(email)).toBeVisible();
  });

  test("/verify-email/<bad-key> renders error state", async ({ page }) => {
    if (!REAL) {
      await page.route("**/api/public/v1/auth/registration/verify-email/**", async (route) => {
        await route.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({
            type: "https://yakimaweb.local/problems/invalid-key",
            title: "Invalid verification key",
            status: 400,
            detail: "The verification link is invalid or has expired.",
          }),
        });
      });
    }

    await page.goto("/verify-email/this-key-does-not-exist-1234");

    await expect(
      page
        .getByText(/invalid|expired|could not verify|something went wrong/i)
        .first(),
    ).toBeVisible();
  });
});
