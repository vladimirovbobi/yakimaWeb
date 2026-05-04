import { test, expect } from "./helpers/fixtures";

const REAL = process.env.E2E_USE_REAL_AUTH === "1";

test.describe("forum: vote and reply", () => {
  test("upvote increments score; second click resets", async ({
    authedPage: page,
  }) => {
    await page.goto("/community");
    const threadLink = page.locator('a[href^="/community/threads/"]').first();
    if ((await threadLink.count()) === 0) {
      test.skip(true, "No seed threads");
      return;
    }
    await threadLink.click();
    await expect(page).toHaveURL(/\/community\/threads\/[^/]+/);

    const upvote = page
      .getByRole("button", { name: /upvote|vote up/i })
      .first();
    if ((await upvote.count()) === 0) {
      test.skip(true, "Vote control not exposed");
      return;
    }

    const scoreLocator = page
      .locator('[data-testid*="score"], [aria-label*="score" i]')
      .first();

    let initialScore = 0;
    if ((await scoreLocator.count()) > 0) {
      const txt = (await scoreLocator.innerText()).trim();
      initialScore = parseInt(txt, 10) || 0;
    }

    if (!REAL) {
      let voteState = 0;
      await page.route("**/api/public/v1/forum/**/vote/**", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        const body = (await route.request().postDataJSON()) as { value?: number };
        voteState = body?.value ?? 0;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            score: initialScore + voteState,
            user_vote: voteState,
          }),
        });
      });
    }

    await upvote.click();
    if ((await scoreLocator.count()) > 0) {
      await expect
        .poll(async () =>
          parseInt((await scoreLocator.innerText()).trim(), 10) || 0,
        )
        .toBe(initialScore + 1);
    }

    await upvote.click();
    if ((await scoreLocator.count()) > 0) {
      await expect
        .poll(async () =>
          parseInt((await scoreLocator.innerText()).trim(), 10) || 0,
        )
        .toBe(initialScore);
    }
  });

  test("authed user can post a reply", async ({ authedPage: page }) => {
    await page.goto("/community");
    const threadLink = page.locator('a[href^="/community/threads/"]').first();
    if ((await threadLink.count()) === 0) {
      test.skip(true, "No seed threads");
      return;
    }
    await threadLink.click();

    const replyInput = page
      .locator('textarea[name*="reply" i], textarea[name*="body" i], textarea')
      .first();
    if ((await replyInput.count()) === 0) {
      test.skip(true, "Reply form not yet built");
      return;
    }

    const body = `E2E reply ${Date.now()}`;

    if (!REAL) {
      await page.route("**/api/public/v1/forum/replies/**", async (route) => {
        if (route.request().method() !== "POST") return route.continue();
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 88888,
            body,
            moderation_status: "approved",
            created_at: new Date().toISOString(),
            author: { email: "demo-realtor@yakimaweb.local" },
          }),
        });
      });
    }

    await replyInput.fill(body);
    await page.getByRole("button", { name: /reply|post|submit/i }).first().click();

    await expect(
      page.getByText(body).or(page.getByText(/pending review/i)).first(),
    ).toBeVisible({ timeout: 10_000 });
  });
});
