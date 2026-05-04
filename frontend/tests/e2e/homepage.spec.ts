import { test, expect } from "@playwright/test";

test("homepage hero is visible", async ({ page }) => {
  await page.goto("/");

  const heading = page.getByRole("heading", { level: 1 });
  await expect(heading).toBeVisible();
  await expect(heading).toContainText(/Central Washington/i);
});
