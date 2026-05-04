import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 24: POST without X-CSRFToken header -> 403.
 *
 * Defaults to mocking — real backend exercise via E2E_USE_REAL_AUTH=1.
 */

test.describe("CSRF protection", () => {
  test("POST without X-CSRFToken header -> 403", async ({ page }) => {
    await mockLogin(page);

    if (process.env.E2E_USE_REAL_AUTH !== "1") {
      await page.route("**/api/v1/posts/comments/**", async (route) => {
        const headers = route.request().headers();
        if (
          route.request().method() === "POST" &&
          !headers["x-csrftoken"] &&
          !headers["x-csrf-token"]
        ) {
          await route.fulfill({
            status: 403,
            contentType: "application/problem+json",
            body: JSON.stringify({
              type: "https://yakimaweb.local/problems/csrf",
              title: "CSRF token missing",
              status: 403,
              code: "csrf_required",
            }),
          });
          return;
        }
        await route.continue();
      });
    }

    await page.goto("/");

    const status = await page.evaluate(async () => {
      const res = await fetch("/api/v1/posts/comments/", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ post_id: 1, body: "no csrf" }),
        credentials: "include",
      });
      return res.status;
    });

    expect(status).toBe(403);
  });

  test("POST with valid X-CSRFToken header succeeds (mocked)", async ({
    page,
  }) => {
    await mockLogin(page);

    await page.route("**/api/v1/posts/comments/**", async (route) => {
      const headers = route.request().headers();
      if (
        route.request().method() === "POST" &&
        (headers["x-csrftoken"] || headers["x-csrf-token"])
      ) {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: 1 }),
        });
        return;
      }
      await route.fulfill({ status: 403, body: "forbidden" });
    });

    await page.goto("/");

    const status = await page.evaluate(async () => {
      const res = await fetch("/api/v1/posts/comments/", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-csrftoken": "tok",
        },
        body: JSON.stringify({ post_id: 1, body: "ok" }),
      });
      return res.status;
    });

    expect(status).toBe(201);
  });
});
