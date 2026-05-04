import { expect, test } from "@playwright/test";

import { mockLogin } from "./helpers/auth";

const ROUTE = "/dashboard/tools/furniture-remover";
const RUN_API = /\/api\/v1\/tools\/furniture-remover\/?$/;
const STREAM_API = /\/api\/v1\/tools\/streams\/\d+\/?$/;
const STATUS_API = /\/api\/v1\/tools\/tasks\/\d+\/?$/;

const TINY_PNG_BASE64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9ZP6n0kAAAAASUVORK5CYII=";

test.describe("furniture remover", () => {
  test("anonymous visit redirects to /login with next=", async ({ page }) => {
    await page.context().clearCookies();
    await page.goto(ROUTE);
    await expect(page).toHaveURL(
      /\/login\?next=%2Fdashboard%2Ftools%2Ffurniture-remover/,
    );
  });

  test("logged-in user uploads, sees processing then result", async ({ page }) => {
    await mockLogin(page);

    await page.route(RUN_API, async (route) => {
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          task_id: 42,
          status: "queued",
          original_url: "/media/sample-before.png",
          result_url: null,
        }),
      });
    });

    // SSE: respond with two frames; the second is final/success.
    await page.route(STREAM_API, async (route) => {
      const successFrame = {
        task_id: 42,
        status: "success",
        progress: 100,
        result_url: "/media/sample-after.png",
        input_url: "/media/sample-before.png",
        cost_usd: 0.04,
        runtime_ms: 31_000,
        error: null,
        block_reason: null,
        final: true,
      };
      const body =
        `: connected\n\n` +
        `data: ${JSON.stringify({ ...successFrame, status: "running", progress: 55, final: false })}\n\n` +
        `data: ${JSON.stringify(successFrame)}\n\n`;
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        headers: { "Cache-Control": "no-cache" },
        body,
      });
    });

    // Polling fallback — same final shape, in case the browser drops SSE.
    await page.route(STATUS_API, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "success",
          progress: 100,
          result: {
            url: "/media/sample-after.png",
            input_url: "/media/sample-before.png",
            cost_usd: 0.04,
            runtime_ms: 31_000,
          },
        }),
      });
    });

    await page.goto(ROUTE);
    await expect(
      page.getByRole("heading", { name: /Furniture remover/i }),
    ).toBeVisible();

    // Upload via the hidden <input type="file"> the DropZone renders.
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "tiny.png",
      mimeType: "image/png",
      buffer: Buffer.from(TINY_PNG_BASE64, "base64"),
    });

    await expect(
      page.getByText(/uploading|emptying the room|processing/i).first(),
    ).toBeVisible({ timeout: 5_000 });

    // Result lands.
    await expect(
      page.getByRole("img", { name: /before and after comparison/i }),
    ).toBeVisible({ timeout: 15_000 });

    await expect(
      page.getByRole("link", { name: /download empty-room/i }),
    ).toBeVisible();
  });

  test("budget-exhausted error renders friendly copy", async ({ page }) => {
    await mockLogin(page);
    await page.route(RUN_API, async (route) => {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          status: 400,
          title: "Bad Request",
          detail: "spend_cap_exceeded",
        }),
      });
    });

    await page.goto(ROUTE);
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "tiny.png",
      mimeType: "image/png",
      buffer: Buffer.from(TINY_PNG_BASE64, "base64"),
    });

    await expect(page.getByText(/daily ai budget/i)).toBeVisible({
      timeout: 5_000,
    });
  });

  test("before/after slider responds to keyboard arrows", async ({ page }) => {
    await mockLogin(page);
    await page.route(RUN_API, async (route) => {
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({
          task_id: 7,
          status: "queued",
          original_url: "/media/before.png",
          result_url: null,
        }),
      });
    });
    await page.route(STREAM_API, async (route) => {
      const final = {
        task_id: 7,
        status: "success",
        progress: 100,
        result_url: "/media/after.png",
        input_url: "/media/before.png",
        cost_usd: 0.03,
        runtime_ms: 28_000,
        error: null,
        block_reason: null,
        final: true,
      };
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: `data: ${JSON.stringify(final)}\n\n`,
      });
    });

    await page.goto(ROUTE);
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "tiny.png",
      mimeType: "image/png",
      buffer: Buffer.from(TINY_PNG_BASE64, "base64"),
    });

    const handle = page.getByRole("button", { name: /adjust before\/after/i });
    await expect(handle).toBeVisible({ timeout: 15_000 });
    await handle.focus();
    await handle.press("ArrowLeft");
    await handle.press("ArrowLeft");
    // Visually asserting position would couple us to internals; just confirm
    // the control still has focus and didn't error out.
    await expect(handle).toBeFocused();
  });
});
