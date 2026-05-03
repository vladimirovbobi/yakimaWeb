import { test, expect } from "@playwright/test";

test.describe("Public marketing pages", () => {
  test("homepage loads with brand + hero", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Yakima Real Estate Hub/);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByText(/honest version of local real estate/i)).toBeVisible();
  });

  test("nav links work", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "About" }).first().click();
    await expect(page).toHaveURL(/about/);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(/respects your time/i);
  });

  test("guidelines page renders all severity sections", async ({ page }) => {
    await page.goto("/guidelines/");
    await expect(page.getByText(/Severity 4/)).toBeVisible();
    await expect(page.getByText(/Severity 3/)).toBeVisible();
    await expect(page.getByText(/Severity 2/)).toBeVisible();
    await expect(page.getByText(/Severity 1/)).toBeVisible();
  });

  test("privacy + terms have placeholder notice", async ({ page }) => {
    await page.goto("/privacy/");
    await expect(page.getByText(/Placeholder draft pending attorney review/)).toBeVisible();
    await page.goto("/terms/");
    await expect(page.getByText(/Placeholder draft pending attorney review/)).toBeVisible();
  });

  test("healthz alive", async ({ page }) => {
    const r = await page.goto("/healthz");
    expect(r?.status()).toBe(200);
    await expect(page.locator("body")).toContainText("ok");
  });
});
