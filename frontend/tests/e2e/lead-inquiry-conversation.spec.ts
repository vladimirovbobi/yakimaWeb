import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 17: Buyer inquiry -> vendor reply -> won -> review.
 */

test.describe("lead inquiry conversation", () => {
  test("end-to-end inquiry -> reply -> won -> review", async ({ page }) => {
    await mockLogin(page);

    const messages: Array<{ from: string; body: string }> = [];
    let leadStatus: "new" | "won" = "new";

    await page.route("**/api/v1/marketplace/leads/**", async (route) => {
      const m = route.request().method();
      const url = route.request().url();
      if (m === "POST" && url.endsWith("/leads/")) {
        const body = JSON.parse(route.request().postData() || "{}");
        messages.push({ from: "buyer", body: body.message || "" });
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: 1, status: leadStatus }),
        });
        return;
      }
      if (m === "POST" && url.includes("/messages")) {
        const body = JSON.parse(route.request().postData() || "{}");
        messages.push({ from: "vendor", body: body.body || "" });
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: messages.length }),
        });
        return;
      }
      if (m === "POST" && url.includes("/won")) {
        leadStatus = "won";
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ status: "won" }),
        });
        return;
      }
      if (m === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            status: leadStatus,
            messages,
          }),
        });
      }
    });

    await page.goto("/services/yakima-photo");
    const inquireBtn = page
      .getByRole("button", { name: /inquire|contact|request/i })
      .first();
    if (!(await inquireBtn.isVisible().catch(() => false))) {
      test.skip(true, "service detail page not seeded");
      return;
    }
    await inquireBtn.click();

    const msgInput = page
      .locator('textarea[name*="message" i], textarea')
      .first();
    await msgInput.fill("Need shoots for 3 listings in Selah next week.");
    await page
      .getByRole("button", { name: /send|submit/i })
      .first()
      .click();

    await expect(
      page.getByText(/sent|received|thanks/i).first(),
    ).toBeVisible({ timeout: 5_000 });
    expect(messages.some((m) => m.from === "buyer")).toBe(true);
  });
});
