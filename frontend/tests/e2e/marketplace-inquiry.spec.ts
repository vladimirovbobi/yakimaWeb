import { test, expect } from "./helpers/fixtures";

const REAL = process.env.E2E_USE_REAL_AUTH === "1";

test.describe("marketplace inquiry", () => {
  test("authed user submits an inquiry; success state appears", async ({
    authedPage: page,
  }) => {
    await page.goto("/services");
    const serviceLink = page.locator('a[href^="/services/"]').first();
    if ((await serviceLink.count()) === 0) {
      test.skip(true, "No seed services");
      return;
    }
    await serviceLink.click();
    await expect(page).toHaveURL(/\/services\/[^/]+/);

    const sendBtn = page
      .getByRole("button", { name: /send inquiry|contact vendor|inquire/i })
      .first();
    const inquiryLink = page
      .getByRole("link", { name: /send inquiry|contact vendor|inquire/i })
      .first();

    if ((await sendBtn.count()) > 0) {
      await sendBtn.click();
    } else if ((await inquiryLink.count()) > 0) {
      await inquiryLink.click();
    } else {
      test.skip(true, "No inquiry CTA on this build");
      return;
    }

    // Fill the form (selectors are best-effort; rely on name attrs first)
    const name = page.locator('input[name="name"], input[name*="name" i]').first();
    if ((await name.count()) > 0) await name.fill("E2E Buyer");

    const emailInput = page
      .locator('input[name="email"], input[type="email"]')
      .first();
    if ((await emailInput.count()) > 0) await emailInput.fill("buyer@yakimaweb.local");

    const phone = page
      .locator('input[name="phone"], input[type="tel"]')
      .first();
    if ((await phone.count()) > 0) await phone.fill("509-555-0100");

    const message = page
      .locator('textarea[name="message"], textarea[name*="message" i], textarea')
      .first();
    if ((await message.count()) > 0)
      await message.fill("Interested in your standard package.");

    const packageSelect = page
      .locator('select[name*="package" i], [role="combobox"]')
      .first();
    if ((await packageSelect.count()) > 0) {
      const tag = await packageSelect.evaluate((el) => el.tagName.toLowerCase());
      if (tag === "select") {
        const options = await packageSelect
          .locator("option")
          .filter({ hasNotText: /^\s*$/ })
          .all();
        if (options.length > 1) {
          await packageSelect.selectOption({ index: 1 });
        }
      }
    }

    if (!REAL) {
      await page.route("**/api/public/v1/marketplace/leads/**", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 12345,
            status: "new",
            created_at: new Date().toISOString(),
          }),
        });
      });
    }

    await page
      .getByRole("button", { name: /send|submit|inquire/i })
      .first()
      .click();

    await expect(
      page
        .getByText(/thanks|received|sent|we'll be in touch|inquiry submitted/i)
        .first(),
    ).toBeVisible({ timeout: 10_000 });
  });
});
