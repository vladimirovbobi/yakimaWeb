import { test as base, expect, Page } from "@playwright/test";
import { loginAs, mockLogin, TEST_OPERATOR, TEST_USER, TEST_VENDOR } from "./auth";

type Fixtures = {
  anonPage: Page;
  authedPage: Page;
  vendorPage: Page;
  operatorPage: Page;
};

/**
 * Custom Playwright fixtures.
 *
 * - `anonPage` - explicit anonymous (cookies cleared, no extra setup)
 * - `authedPage` - logged-in member/realtor (real flow when seed user exists,
 *   else falls back to mocked cookies + /auth/me/ stub)
 * - `vendorPage` - logged-in vendor account
 * - `operatorPage` - logged-in operator/staff account
 *
 * Real-flow login can be forced via `E2E_USE_REAL_AUTH=1` env var.
 */
export const test = base.extend<Fixtures>({
  anonPage: async ({ page }, use) => {
    await page.context().clearCookies();
    await use(page);
  },

  authedPage: async ({ page }, use) => {
    await ensureAuth(page, TEST_USER.email, TEST_USER.password);
    await use(page);
  },

  vendorPage: async ({ page }, use) => {
    await ensureAuth(page, TEST_VENDOR.email, TEST_VENDOR.password, [
      "member",
      "vendor",
    ]);
    await use(page);
  },

  operatorPage: async ({ page }, use) => {
    await ensureAuth(page, TEST_OPERATOR.email, TEST_OPERATOR.password, [
      "member",
      "staff",
      "operator",
    ]);
    await use(page);
  },
});

async function ensureAuth(
  page: Page,
  email: string,
  password: string,
  roles: string[] = ["member", "realtor"],
): Promise<void> {
  if (process.env.E2E_USE_REAL_AUTH === "1") {
    await loginAs(page, email, password);
    return;
  }

  // Mocked: seed cookies + intercept /auth/me/
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
        roles,
      }),
    });
  });
}

export { expect, mockLogin };
