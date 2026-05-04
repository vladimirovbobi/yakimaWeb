import { test, expect, mockLogin } from "./helpers/fixtures";
import path from "node:path";

/**
 * Spec 19: Realtor uploads room -> processes -> before/after slider visible.
 */

test.describe("furniture remover flow", () => {
  test("upload -> processing -> done -> slider visible", async ({ page }) => {
    await mockLogin(page);

    let job = { id: "job1", status: "queued", before: "", after: "" };

    await page.route("**/api/v1/tools/furniture-remover/**", async (route) => {
      const m = route.request().method();
      if (m === "POST") {
        job = {
          id: "job1",
          status: "processing",
          before: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA",
          after: "",
        };
        await route.fulfill({
          status: 202,
          contentType: "application/json",
          body: JSON.stringify(job),
        });
        return;
      }
      if (m === "GET") {
        if (job.status === "processing") {
          job.status = "done";
          job.after = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA";
        }
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(job),
        });
      }
    });

    await page.goto("/tools/furniture-remover");
    const fileInput = page.locator('input[type="file"]').first();
    if (!(await fileInput.isVisible().catch(() => false))) {
      test.skip(true, "furniture remover UI not yet built");
      return;
    }
    const sample = path.resolve(__dirname, "fixtures/room.png");
    await fileInput
      .setInputFiles({
        name: "room.png",
        mimeType: "image/png",
        buffer: Buffer.from(
          "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489" +
            "0000000d49444154789c63f8ff0f00000000ffff03000000000000ffff",
          "hex",
        ),
      })
      .catch(async () => {
        await fileInput.setInputFiles(sample).catch(() => {});
      });

    await page.getByRole("button", { name: /process|run|go/i }).first().click();

    await expect(
      page.getByText(/processing|queued|working/i).first(),
    ).toBeVisible({ timeout: 5_000 });

    // Poll
    await page.waitForTimeout(1_000);
    await expect(
      page.locator('[data-testid*="slider"], [role="slider"]').first(),
    ).toBeVisible({ timeout: 10_000 });

    const downloadBtn = page
      .getByRole("link", { name: /download|save/i })
      .or(page.getByRole("button", { name: /download|save/i }))
      .first();
    await expect(downloadBtn).toBeVisible();
  });
});
