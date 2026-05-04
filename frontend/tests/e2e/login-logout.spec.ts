import { test, expect } from "@playwright/test";
import { TEST_USER, assertLoggedOut } from "./helpers/auth";

/**
 * Login / logout flow.
 *
 * Default: stubs the auth endpoints so the test does not depend on a real DB.
 * Set E2E_USE_REAL_AUTH=1 to exercise the real Django flow against the seeded
 * TEST_USER.
 *
 * Backend assumption (real-auth mode): seed_all creates `demo-realtor@yakimaweb.local`
 * with email-verified status and password `TestPass123!`.
 */

const REAL = process.env.E2E_USE_REAL_AUTH === "1";

test.describe("login / logout", () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
  });

  test("good credentials -> /dashboard, httpOnly cookies set", async ({
    page,
  }) => {
    if (!REAL) {
      await page.route("**/api/public/v1/auth/login/**", async (route) => {
        if (route.request().method() !== "POST") return route.continue();

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          headers: {
            "Set-Cookie": [
              "yw_access=test-access-token; Path=/; HttpOnly; SameSite=Lax",
              "yw_refresh=test-refresh-token; Path=/; HttpOnly; SameSite=Lax",
            ].join(", "),
          },
          body: JSON.stringify({
            email: TEST_USER.email,
            is_authenticated: true,
            roles: ["member", "realtor"],
          }),
        });
      });

      await page.route("**/api/public/v1/auth/me/**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            email: TEST_USER.email,
            is_authenticated: true,
            roles: ["member", "realtor"],
          }),
        });
      });
    }

    await page.goto("/login");
    await page
      .locator('input[name="email"], input[type="email"]')
      .first()
      .fill(TEST_USER.email);
    await page
      .locator('input[name="password"], input[type="password"]')
      .first()
      .fill(TEST_USER.password);
    await page.getByRole("button", { name: /sign in|log in/i }).click();

    await page.waitForURL(/\/dashboard/, { timeout: 15_000 });
    await expect(page).toHaveURL(/\/dashboard/);

    // Cookies present
    const cookies = await page.context().cookies();
    const access = cookies.find((c) => c.name === "yw_access");
    const refresh = cookies.find((c) => c.name === "yw_refresh");
    expect(access, "yw_access cookie").toBeTruthy();
    expect(refresh, "yw_refresh cookie").toBeTruthy();
    expect(access!.httpOnly).toBe(true);
    expect(refresh!.httpOnly).toBe(true);

    // JS cannot read httpOnly cookies
    const jsCookies = await page.evaluate(() => document.cookie);
    expect(jsCookies).not.toContain("yw_access=");
    expect(jsCookies).not.toContain("yw_refresh=");
  });

  test("sign out clears cookies and lands on /", async ({ page }) => {
    // Seed a logged-in session
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

    if (!REAL) {
      await page.route("**/api/public/v1/auth/me/**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            email: TEST_USER.email,
            is_authenticated: true,
            roles: ["member"],
          }),
        });
      });
      await page.route("**/api/public/v1/auth/logout/**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          headers: {
            "Set-Cookie": [
              "yw_access=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0",
              "yw_refresh=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0",
            ].join(", "),
          },
          body: JSON.stringify({ detail: "Logged out." }),
        });
      });
    }

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/);

    const signOut = page
      .getByRole("button", { name: /sign out|log out/i })
      .or(page.getByRole("link", { name: /sign out|log out/i }))
      .first();
    await signOut.click();

    await page.waitForURL((url) => !url.pathname.startsWith("/dashboard"), {
      timeout: 10_000,
    });
    await assertLoggedOut(page);
  });

  test("bad credentials show RFC 7807 error UI", async ({ page }) => {
    if (!REAL) {
      await page.route("**/api/public/v1/auth/login/**", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        await route.fulfill({
          status: 400,
          contentType: "application/problem+json",
          body: JSON.stringify({
            type: "https://yakimaweb.local/problems/invalid-credentials",
            title: "Invalid credentials",
            status: 400,
            detail: "Email or password is incorrect.",
          }),
        });
      });
    }

    await page.goto("/login");
    await page
      .locator('input[name="email"], input[type="email"]')
      .first()
      .fill("nope@yakimaweb.local");
    await page
      .locator('input[name="password"], input[type="password"]')
      .first()
      .fill("WrongPass123!");
    await page.getByRole("button", { name: /sign in|log in/i }).click();

    await expect(
      page.getByText(/invalid credentials|incorrect|email or password/i).first(),
    ).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });
});
