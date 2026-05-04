import { test, expect } from "./helpers/fixtures";

/**
 * Sprint 5: Mod console v2 — keyboard-driven queue, escalate flow, investigate drawer.
 */

const QUEUE_ITEM = {
  id: 42,
  target_type: "comment",
  target_id: 7,
  target_excerpt: "Borderline content needing review.",
  target_full_url: "/blog/p/sample/",
  reason_flag: "spam",
  classifier_output: {
    allowed: false,
    categories: ["low_quality"],
    severity: 2,
  },
  severity: 2,
  created_at: new Date().toISOString(),
};

const TEMPLATES = [
  {
    slug: "removed_spam",
    label: "Removed - Spam",
    action: "remove",
    default_reason: "Removed: spam.",
  },
  {
    slug: "approved_no_change",
    label: "Approved - No change",
    action: "approve",
    default_reason: "Approved as-is.",
  },
];

test.describe("mod console v2", () => {
  test("operator opens queue, presses A, next item loads", async ({
    operatorPage: page,
  }) => {
    let decisionPosted = false;
    let nextCallCount = 0;

    await page.route("**/api/v1/mod/queue/next/**", async (route) => {
      nextCallCount += 1;
      if (nextCallCount === 1) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(QUEUE_ITEM),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ...QUEUE_ITEM,
            id: 43,
            target_excerpt: "Second item.",
          }),
        });
      }
    });

    await page.route("**/api/v1/mod/templates/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(TEMPLATES),
      });
    });

    await page.route("**/api/v1/mod/queue/?limit=1", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ count: 5, results: [] }),
      });
    });

    await page.route(
      "**/api/v1/mod/items/42/decision/**",
      async (route) => {
        decisionPosted = true;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            decision_id: 1,
            action: "approve",
            applied_at: new Date().toISOString(),
          }),
        });
      },
    );

    await page.goto("/dashboard/mod/queue");
    await expect(page.getByText("Borderline content needing review.")).toBeVisible();

    await page.keyboard.press("a");
    await page.waitForTimeout(500);
    expect(decisionPosted).toBe(true);
    await expect(page.getByText("Second item.")).toBeVisible();
  });

  test("pressing E opens escalation modal", async ({ operatorPage: page }) => {
    await page.route("**/api/v1/mod/queue/next/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(QUEUE_ITEM),
      });
    });
    await page.route("**/api/v1/mod/templates/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(TEMPLATES),
      });
    });
    await page.route("**/api/v1/mod/queue/?limit=1", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ count: 1, results: [] }),
      });
    });

    await page.goto("/dashboard/mod/queue");
    await expect(
      page.getByText("Borderline content needing review."),
    ).toBeVisible();
    await page.keyboard.press("e");
    await expect(page.getByText("Escalate to operators")).toBeVisible();
  });

  test("dashboard shows stats cards", async ({ operatorPage: page }) => {
    await page.route("**/api/v1/mod/stats/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items_reviewed_30d: 124,
          items_reviewed_7d: 18,
          agreement_rate: 0.94,
          reversal_rate: 0.03,
          avg_response_minutes: 8.2,
          current_streak: 12,
          queue_position: 1,
          timeseries_30d: [],
        }),
      });
    });
    await page.route("**/api/v1/mod/queue/?limit=1", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ count: 5, results: [] }),
      });
    });

    await page.goto("/dashboard/mod");
    await expect(page.getByText("124")).toBeVisible();
    await expect(page.getByText("94%")).toBeVisible();
  });
});
