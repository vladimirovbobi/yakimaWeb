import { test, expect } from "@playwright/test";

const OWN_HOST_RE = /^https?:\/\/localhost(:\d+)?\//;

test.describe("homepage", () => {
  test("hero, CTAs, and featured grids render for anonymous user", async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    const failedRequests: string[] = [];

    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("requestfailed", (req) => {
      const url = req.url();
      if (OWN_HOST_RE.test(url) && !/\.map(\?|$)/.test(url)) {
        failedRequests.push(`${req.failure()?.errorText} ${url}`);
      }
    });

    await page.goto("/");

    const heading = page.getByRole("heading", { level: 1 });
    await expect(heading).toBeVisible();
    await expect(heading).toContainText(/Central Washington/i);

    // Featured posts: either a heading region OR an empty-state copy
    const featuredPosts = page
      .locator('section, [data-testid*="featured-posts"]')
      .filter({ hasText: /featured posts|latest|from the blog|no posts/i })
      .first();
    await expect(featuredPosts).toBeVisible();

    // Featured services
    const featuredServices = page
      .locator('section, [data-testid*="featured-services"]')
      .filter({ hasText: /services|marketplace|vendors|no services/i })
      .first();
    await expect(featuredServices).toBeVisible();

    // CTAs
    const signupCta = page
      .getByRole("link", { name: /sign up|get started/i })
      .first();
    await expect(signupCta).toBeVisible();
    await expect(signupCta).toHaveAttribute("href", /\/signup/);

    const marketplaceCta = page
      .getByRole("link", { name: /browse the marketplace|marketplace|explore services/i })
      .first();
    await expect(marketplaceCta).toBeVisible();
    await expect(marketplaceCta).toHaveAttribute("href", /\/services/);

    // No console errors / failed requests on own domain
    expect(consoleErrors, `console errors: ${consoleErrors.join("\n")}`).toEqual(
      [],
    );
    expect(
      failedRequests,
      `failed requests: ${failedRequests.join("\n")}`,
    ).toEqual([]);
  });

  test("CTA navigation: signup CTA leads to /signup", async ({ page }) => {
    await page.goto("/");
    await page
      .getByRole("link", { name: /sign up|get started/i })
      .first()
      .click();
    await expect(page).toHaveURL(/\/signup/);
  });

  test("CTA navigation: marketplace CTA leads to /services", async ({ page }) => {
    await page.goto("/");
    await page
      .getByRole("link", { name: /browse the marketplace|marketplace|explore services/i })
      .first()
      .click();
    await expect(page).toHaveURL(/\/services/);
  });

  test("mobile: no horizontal scroll, hamburger toggles overlay", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name === "chromium-desktop",
      "Mobile-only assertion",
    );

    await page.goto("/");

    // No horizontal scroll
    const hasOverflow = await page.evaluate(() => {
      const html = document.documentElement;
      return html.scrollWidth > html.clientWidth + 1;
    });
    expect(hasOverflow).toBe(false);

    // Hamburger
    const hamburger = page
      .getByRole("button", { name: /menu|navigation|open menu/i })
      .first();
    await expect(hamburger).toBeVisible();
    await hamburger.click();

    // Overlay should expose nav links
    const navOverlay = page.getByRole("navigation").last();
    await expect(navOverlay).toBeVisible();
    await expect(
      navOverlay.getByRole("link", { name: /blog|services|community|tools/i }).first(),
    ).toBeVisible();
  });
});
