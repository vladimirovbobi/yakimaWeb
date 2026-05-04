import { test, expect } from "./helpers/fixtures";

/**
 * Sprint 4 — Vendor onboarding wizard happy path.
 *
 * Logged-in user → 5 wizard steps → submission → pending badge.
 */

test.describe("vendor onboarding wizard (Sprint 4)", () => {
  test("walk through 5 steps and submit", async ({ vendorPage: page }) => {
    let wizardState: Record<string, unknown> = {
      current_step: "business",
      completed_steps: [],
      data: {},
    };

    // /api/v1/me/ — Next.js auth check
    await page.route("**/api/v1/me/", async (route) => {
      const method = route.request().method();
      if (method !== "GET") return route.continue();
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 99,
          email: "demo-vendor@yakimaweb.local",
          display_name: "Demo Vendor",
          is_realtor: false,
          is_vendor: true,
          is_staff: false,
        }),
      });
    });

    // /api/v1/me/vendor/ — read draft.
    await page.route("**/api/v1/me/vendor/", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          business_name: "Yakima Photo Co",
          tagline: "",
          website: "",
          contact_phone: "",
          about: "",
          status: "draft",
          current_step: wizardState.current_step,
          completed_steps: wizardState.completed_steps,
          wizard_state: wizardState,
        }),
      });
    });

    // Wizard step writes — accept & advance the local fake state.
    await page.route("**/api/v1/vendors/onboard/**", async (route) => {
      const url = route.request().url();
      const m = url.match(/onboard\/([a-z]+)\/?$/);
      const step = m?.[1] || "business";
      const next: Record<string, string> = {
        business: "categories",
        categories: "services",
        services: "gallery",
        gallery: "publish",
        publish: "publish",
      };
      const completed = new Set<string>(
        wizardState.completed_steps as string[],
      );
      completed.add(step);
      wizardState = {
        current_step: next[step] || step,
        completed_steps: Array.from(completed),
        data: { ...(wizardState.data || {}) },
      };
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          step,
          saved: true,
          wizard_state: wizardState,
          status: step === "publish" ? "draft" : "draft",
          submitted_at: step === "publish" ? new Date().toISOString() : null,
        }),
      });
    });

    // Categories tree
    await page.route("**/api/public/v1/services/categories/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: 1,
            slug: "photography",
            name: "Photography",
            depth: 1,
            icon: "",
            children: [
              {
                id: 2,
                slug: "photography-real-estate",
                name: "Real Estate Photography",
                depth: 2,
                icon: "",
                children: [],
              },
            ],
          },
        ]),
      });
    });

    // Notification polling shouldn't break the page
    await page.route("**/api/v1/me/notifications/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ count: 0, results: [] }),
      });
    });

    await page.goto("/dashboard/vendor/onboard");

    // Step 1: business
    await expect(page.getByRole("heading", { name: /your business/i }))
      .toBeVisible({ timeout: 8_000 });
    await page.getByLabel(/business name/i).fill("Yakima Photo Co");
    await page.getByLabel(/tagline/i).fill("Sharp listings, faster sales");
    await page.getByRole("button", { name: /continue/i }).click();

    // Step 2: categories
    await expect(page.getByRole("heading", { name: /pick your categories/i }))
      .toBeVisible();
    await page.getByRole("button", { name: /real estate photography/i }).click();
    await page.getByRole("button", { name: /^continue$/i }).click();

    // Step 3: services
    await expect(page.getByRole("heading", { name: /your services/i }))
      .toBeVisible();
    await page.getByLabel(/^title$/i).first().fill("Listing essentials");
    await page
      .getByPlaceholder(/what buyers get/i)
      .fill("Photo + drone + virtual tour for residential listings.");
    await page.getByRole("button", { name: /^continue$/i }).click();

    // Step 4: gallery
    await expect(page.getByRole("heading", { name: /your portfolio/i }))
      .toBeVisible();
    await page.getByRole("button", { name: /^continue$/i }).click();

    // Step 5: publish
    await expect(page.getByRole("heading", { name: /review & submit/i }))
      .toBeVisible();
    await page.locator('input[type="checkbox"]').check();
    await page.getByRole("button", { name: /submit for review/i }).click();

    await expect(page).toHaveURL(/just_submitted=1/);
    await expect(page.getByText(/under review|application/i)).toBeVisible();
  });
});
