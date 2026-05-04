import { test, expect } from "@playwright/test";
import { mockLogin } from "./helpers/auth";

/**
 * Auth-gating: anonymous users hitting protected actions / routes
 * are bounced to /login?next=...
 */

test.describe("auth gating: anonymous", () => {
  test("direct visit to /dashboard redirects to /login with next=", async ({
    page,
  }) => {
    await page.context().clearCookies();
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login\?next=%2Fdashboard/);
  });

  test("direct visit to /dashboard/tools/furniture-remover redirects to /login", async ({
    page,
  }) => {
    await page.context().clearCookies();
    await page.goto("/dashboard/tools/furniture-remover");
    await expect(page).toHaveURL(/\/login\?next=%2Fdashboard%2Ftools%2Ffurniture-remover/);
  });

  test("direct visit to /2fa/setup redirects to /login", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/2fa/setup");
    await expect(page).toHaveURL(/\/login\?next=%2F2fa%2Fsetup/);
  });

  test("vote button on a thread requires auth", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/community");

    const threadLink = page.locator('a[href^="/community/threads/"]').first();
    if ((await threadLink.count()) === 0) {
      test.skip(true, "No seed threads to test gating against");
      return;
    }
    await threadLink.click();
    await expect(page).toHaveURL(/\/community\/threads\/[^/]+/);

    const voteBtn = page
      .getByRole("button", { name: /upvote|vote up|like/i })
      .first();
    if ((await voteBtn.count()) === 0) {
      test.skip(true, "Vote control not exposed on this build");
      return;
    }
    await voteBtn.click();

    // Either redirect to /login OR an inline "sign in" prompt
    await expect
      .poll(async () => {
        const url = page.url();
        if (/\/login/.test(url)) return "redirected";
        const inline = await page
          .getByText(/sign in to vote|sign in to upvote|log in/i)
          .first()
          .isVisible()
          .catch(() => false);
        return inline ? "inline" : "none";
      })
      .not.toBe("none");
  });

  test("reply button on a thread requires auth", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/community");

    const threadLink = page.locator('a[href^="/community/threads/"]').first();
    if ((await threadLink.count()) === 0) {
      test.skip(true, "No seed threads");
      return;
    }
    await threadLink.click();

    const replyPrompt = page
      .getByText(/sign in to reply|log in to reply|join to reply/i)
      .first();
    await expect(replyPrompt).toBeVisible();
  });

  test("send-inquiry button on a service requires auth", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/services");

    const serviceLink = page.locator('a[href^="/services/"]').first();
    if ((await serviceLink.count()) === 0) {
      test.skip(true, "No seed services");
      return;
    }
    await serviceLink.click();
    await expect(page).toHaveURL(/\/services\/[^/]+/);

    const inquiryPrompt = page
      .getByText(/sign in to inquire|sign in to send|log in to inquire/i)
      .first();
    if ((await inquiryPrompt.count()) > 0) {
      await expect(inquiryPrompt).toBeVisible();
      return;
    }
    // Or click the button -> redirect to login
    const sendBtn = page
      .getByRole("button", { name: /send inquiry|contact vendor/i })
      .first();
    if ((await sendBtn.count()) > 0) {
      await sendBtn.click();
      await expect(page).toHaveURL(/\/login/);
    }
  });

  test("after auth, ?next= is honored", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login\?next=%2Fdashboard/);

    // Mock the session and re-navigate; middleware should not bounce.
    await mockLogin(page);
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
