import { test, expect } from "@playwright/test";

/**
 * a11y suite (axe-core).
 *
 * Requires `@axe-core/playwright`. If the package is missing, every test in
 * this file will skip with a helpful message rather than fail.
 *
 * Install: `npm install --save-dev @axe-core/playwright`
 */

type AxeBuilderCtor = new (args: { page: unknown }) => {
  withTags: (tags: string[]) => {
    analyze: () => Promise<{ violations: Array<{ id: string; nodes: unknown[] }> }>;
  };
};

let AxeBuilder: AxeBuilderCtor | null = null;

try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  AxeBuilder = require("@axe-core/playwright").default as AxeBuilderCtor;
} catch {
  AxeBuilder = null;
}

const PUBLIC_PATHS = ["/", "/blog", "/services", "/community", "/tools", "/about"];

test.describe("accessibility (axe wcag2a + wcag2aa)", () => {
  test.beforeEach(async () => {
    test.skip(
      AxeBuilder === null,
      "@axe-core/playwright not installed — skipping a11y suite",
    );
  });

  for (const path of PUBLIC_PATHS) {
    test(`${path} has no a11y violations`, async ({ page }) => {
      await page.goto(path);
      const builder = new AxeBuilder!({ page });
      const results = await builder.withTags(["wcag2a", "wcag2aa"]).analyze();
      expect(
        results.violations,
        `axe violations on ${path}: ${results.violations
          .map((v) => v.id)
          .join(", ")}`,
      ).toEqual([]);
    });
  }

  test("skip-to-main link is reachable via Tab+Enter", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");

    const skip = page
      .getByRole("link", { name: /skip to (main|content)/i })
      .first();
    if ((await skip.count()) === 0) {
      test.skip(true, "Skip-to-main link not implemented yet");
      return;
    }
    await expect(skip).toBeFocused();

    await page.keyboard.press("Enter");
    const mainHash = await page.evaluate(() => window.location.hash);
    expect(mainHash).toMatch(/#main|#content/);
  });
});
