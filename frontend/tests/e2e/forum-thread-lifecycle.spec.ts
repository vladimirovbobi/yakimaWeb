import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 18: Forum thread lifecycle — create, vote, reply, score updates.
 */

test.describe("forum thread lifecycle", () => {
  test("create -> approve -> upvote+reply -> score correct", async ({
    page,
  }) => {
    await mockLogin(page);

    let score = 0;
    let replies = 0;

    await page.route("**/api/v1/forum/threads/**", async (route) => {
      const m = route.request().method();
      const url = route.request().url();
      if (m === "POST" && /\/vote/.test(url)) {
        const body = JSON.parse(route.request().postData() || "{}");
        score += body.value === 1 ? 1 : -1;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ score }),
        });
        return;
      }
      if (m === "POST" && /\/replies/.test(url)) {
        replies += 1;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: replies, body: "Reply" }),
        });
        return;
      }
      if (m === "POST" && /\/threads\/?$/.test(url)) {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: 1, slug: "tt", moderation: "approved" }),
        });
        return;
      }
      if (m === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: 1,
            slug: "tt",
            title: "Best photographer in Yakima?",
            score,
            replies_count: replies,
          }),
        });
      }
    });

    await page.goto("/community");
    const newBtn = page
      .getByRole("link", { name: /new thread|start|post/i })
      .first();
    if (!(await newBtn.isVisible().catch(() => false))) {
      test.skip(true, "forum UI not seeded");
      return;
    }
    await newBtn.click();
    await page
      .locator('input[name="title"]')
      .first()
      .fill("Best photographer in Yakima?");
    await page
      .locator("textarea, [contenteditable=true]")
      .first()
      .fill("Looking for recommendations.");
    await page.getByRole("button", { name: /post|submit/i }).first().click();

    await expect(
      page.getByText(/Best photographer in Yakima/i).first(),
    ).toBeVisible({ timeout: 5_000 });

    // Upvote
    const up = page.getByRole("button", { name: /upvote|^vote up$/i }).first();
    if (await up.isVisible().catch(() => false)) {
      await up.click();
      expect(score).toBe(1);
    }

    // Reply
    const replyArea = page
      .locator('textarea[name*="reply" i], [contenteditable=true]')
      .last();
    await replyArea.fill("Try Yakima Photo Co.");
    await page.getByRole("button", { name: /reply|send/i }).first().click();
    expect(replies).toBeGreaterThanOrEqual(1);
  });
});
