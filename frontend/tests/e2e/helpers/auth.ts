import { Page, expect } from "@playwright/test";

export const TEST_USER = {
  email: process.env.E2E_TEST_USER_EMAIL || "demo-realtor@yakimaweb.local",
  password: process.env.E2E_TEST_USER_PASSWORD || "TestPass123!",
};

export const TEST_VENDOR = {
  email: process.env.E2E_VENDOR_EMAIL || "demo-vendor@yakimaweb.local",
  password: process.env.E2E_VENDOR_PASSWORD || "TestPass123!",
};

export const TEST_OPERATOR = {
  email: process.env.E2E_OPERATOR_EMAIL || "demo-operator@yakimaweb.local",
  password: process.env.E2E_OPERATOR_PASSWORD || "TestPass123!",
};

/**
 * Logs the user in via the real /login form.
 * Waits until the URL is no longer `/login`.
 */
export async function loginAs(
  page: Page,
  email: string,
  password: string,
): Promise<void> {
  await page.goto("/login");
  await page.locator('input[name="email"], input[type="email"]').first().fill(email);
  await page
    .locator('input[name="password"], input[type="password"]')
    .first()
    .fill(password);
  await page.getByRole("button", { name: /sign in|log in|continue/i }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), {
    timeout: 15_000,
  });
}

/**
 * Mocks the login endpoint and seeds the auth cookie. Use when the test must
 * not depend on backend seed data.
 */
export async function mockLogin(page: Page, email = TEST_USER.email): Promise<void> {
  await page.context().addCookies([
    {
      name: "yw_access",
      value: "test-access-token",
      domain: "localhost",
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
    },
    {
      name: "yw_refresh",
      value: "test-refresh-token",
      domain: "localhost",
      path: "/",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);

  await page.route("**/api/public/v1/auth/me/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        email,
        is_authenticated: true,
        roles: ["member", "realtor"],
      }),
    });
  });
}

/**
 * Asserts the auth cookies are gone (logged-out state).
 */
export async function assertLoggedOut(page: Page): Promise<void> {
  const cookies = await page.context().cookies();
  expect(cookies.find((c) => c.name === "yw_access")).toBeUndefined();
  expect(cookies.find((c) => c.name === "yw_refresh")).toBeUndefined();
}
