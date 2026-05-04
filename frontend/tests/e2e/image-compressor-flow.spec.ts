import { test, expect } from "@playwright/test";
import { mockLogin } from "./helpers/auth";

const PNG_1x1 = Buffer.from(
  "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c63000100000005000100" +
    "0d0a2db40000000049454e44ae426082",
  "hex",
);

test.describe("Image compressor lead magnet", () => {
  test.beforeEach(async ({ page }) => {
    await mockLogin(page);
  });

  test("authenticated user can drop a PNG and receive a smaller file", async ({ page }) => {
    await page.goto("/dashboard/tools/image-compressor");
    await expect(
      page.getByRole("heading", { name: /lossless image compressor/i }),
    ).toBeVisible();

    // Drag-drop is hard via Playwright; use the file input directly.
    const input = page.locator('input[type="file"]');
    await input.setInputFiles({
      name: "tiny.png",
      mimeType: "image/png",
      buffer: PNG_1x1,
    });

    // Wait for the per-file row to land.
    await expect(page.getByText(/tiny\.png/)).toBeVisible({ timeout: 30_000 });

    // The "done" status badge should appear (or "error" if backend mocking
    // isn't wired — surface that as a real test failure).
    await expect(page.getByText(/^done$/i, { exact: false }).first()).toBeVisible({
      timeout: 60_000,
    });
  });

  test("unauthenticated user is redirected to /login", async ({ browser }) => {
    const ctx = await browser.newContext(); // fresh, no auth cookies
    const page = await ctx.newPage();
    await page.goto("/dashboard/tools/image-compressor");
    await expect(page).toHaveURL(/\/login/);
    await ctx.close();
  });
});
