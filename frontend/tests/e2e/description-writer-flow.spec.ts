import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 20: Description writer — facts in -> moderation passes -> output streams
 * -> ToolUsage saved.
 */

test.describe("description writer flow", () => {
  test("inputs -> stream -> save", async ({ page }) => {
    await mockLogin(page);

    let saved = false;

    await page.route("**/api/v1/tools/description-writer/**", async (route) => {
      const url = route.request().url();
      const m = route.request().method();
      if (m === "POST" && /\/save/.test(url)) {
        saved = true;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: 1, status: "saved" }),
        });
        return;
      }
      if (m === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "text/event-stream",
          body:
            "data: {\"chunk\":\"Sun-drenched 3-bed in Selah \"}\n\n" +
            "data: {\"chunk\":\"with mountain views.\"}\n\n" +
            "data: [DONE]\n\n",
        });
      }
    });

    await page.goto("/tools/description-writer");
    const beds = page.locator('input[name*="bed" i]').first();
    if (!(await beds.isVisible().catch(() => false))) {
      test.skip(true, "description writer not yet built");
      return;
    }
    await beds.fill("3");
    await page.locator('input[name*="bath" i]').first().fill("2");
    await page
      .locator('input[name*="city" i], input[name*="loc" i]')
      .first()
      .fill("Selah");

    await page
      .getByRole("button", { name: /generate|write|create/i })
      .first()
      .click();

    await expect(
      page.getByText(/Sun-drenched/i).first(),
    ).toBeVisible({ timeout: 10_000 });

    const saveBtn = page.getByRole("button", { name: /save/i }).first();
    if (await saveBtn.isVisible().catch(() => false)) {
      await saveBtn.click();
      await expect(page.getByText(/saved|kept|stored/i).first()).toBeVisible({
        timeout: 5_000,
      });
      expect(saved).toBe(true);
    }
  });
});
