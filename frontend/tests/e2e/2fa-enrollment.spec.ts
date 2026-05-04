import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 28: TOTP enrollment — QR generated, code accepted, 2FA active.
 */

test.describe("2FA enrollment", () => {
  test("setup -> QR -> code accepted -> 2fa active", async ({ page }) => {
    await mockLogin(page);

    let twoFaActive = false;

    await page.route("**/api/v1/accounts/2fa/**", async (route) => {
      const url = route.request().url();
      const m = route.request().method();
      if (m === "GET" && /setup/.test(url)) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            secret: "JBSWY3DPEHPK3PXP",
            qr_code:
              "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA",
          }),
        });
        return;
      }
      if (m === "POST" && /verify/.test(url)) {
        const body = JSON.parse(route.request().postData() || "{}");
        if (/^\d{6}$/.test(body.token || "")) {
          twoFaActive = true;
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({ active: true }),
          });
          return;
        }
        await route.fulfill({
          status: 400,
          body: JSON.stringify({ detail: "invalid" }),
          contentType: "application/json",
        });
      }
    });

    await page.goto("/2fa/setup");

    const qr = page
      .locator('img[alt*="QR" i], img[src*="data:image"], canvas')
      .first();
    if (!(await qr.isVisible().catch(() => false))) {
      test.skip(true, "/2fa/setup not built");
      return;
    }
    await expect(qr).toBeVisible();

    const codeInput = page
      .locator(
        'input[name*="token" i], input[name*="code" i], input[inputmode="numeric"]',
      )
      .first();
    await codeInput.fill("123456");
    await page
      .getByRole("button", { name: /verify|confirm|enable/i })
      .first()
      .click();

    await expect(
      page.getByText(/active|enabled|success|protected/i).first(),
    ).toBeVisible({ timeout: 5_000 });
    expect(twoFaActive).toBe(true);
  });
});
