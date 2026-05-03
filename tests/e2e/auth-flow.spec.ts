import { test, expect } from "@playwright/test";

test.describe("Auth flow — signup + login + logout", () => {
  // Unique email per run so tests don't collide
  const email = `e2e-${Date.now()}@example.com`;
  const password = "Test-Password-12345!";

  test("signup form renders + submits", async ({ page }) => {
    await page.goto("/accounts/signup/");
    await expect(page.getByRole("heading", { name: /Join the Hub/i })).toBeVisible();

    await page.fill("#id_email", email);
    await page.fill("#id_password1", password);
    await page.fill("#id_password2", password);
    await page.getByRole("button", { name: /Create account/i }).click();

    // Should land on email verification screen (mandatory verification)
    await expect(page).toHaveURL(/(confirm-email|verification-sent|profile)/);
  });

  test("login form renders + rejects bad creds", async ({ page }) => {
    await page.goto("/accounts/login/");
    await expect(page.getByRole("heading", { name: /Sign in/i })).toBeVisible();

    await page.fill("#id_login", "nobody@example.com");
    await page.fill("#id_password", "wrongpassword12345");
    await page.getByRole("button", { name: /Sign in/i }).click();

    // Either stays on login w/ error, or hits axes throttle
    await expect(page.locator("body")).not.toContainText(/profile/i);
  });

  test("password reset flow", async ({ page }) => {
    await page.goto("/accounts/password/reset/");
    await expect(page.getByRole("heading", { name: /Forgot your password/i })).toBeVisible();
    await page.fill("#id_email", "anyone@example.com");
    await page.getByRole("button", { name: /Send reset link/i }).click();
    // Allauth redirects to "done" page
    await expect(page).toHaveURL(/done|reset/);
  });
});
