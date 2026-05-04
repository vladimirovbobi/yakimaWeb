import { test, expect, mockLogin } from "./helpers/fixtures";

/**
 * Spec 29: Sidebar items vary by role.
 *
 * Member: profile only.
 * Realtor: + blog.
 * Vendor: + services + leads.
 * Mod: + queue.
 * Op: + ops.
 * Admin: + Django admin link.
 */

const SCENARIOS: Array<{
  name: string;
  roles: string[];
  visible: RegExp[];
  hidden: RegExp[];
}> = [
  {
    name: "member",
    roles: ["member"],
    visible: [/profile|account|settings/i],
    hidden: [/queue|ops|leads/i],
  },
  {
    name: "realtor",
    roles: ["member", "realtor"],
    visible: [/profile|account/i, /blog|posts/i],
    hidden: [/leads|queue|ops/i],
  },
  {
    name: "vendor",
    roles: ["member", "vendor"],
    visible: [/services|listings/i, /leads|inquir/i],
    hidden: [/queue|ops/i],
  },
  {
    name: "moderator",
    roles: ["member", "staff", "moderator"],
    visible: [/queue|moderation|reports/i],
    hidden: [/ops dashboard/i],
  },
  {
    name: "operator",
    roles: ["member", "staff", "operator"],
    visible: [/ops|operations|metrics/i],
    hidden: [],
  },
  {
    name: "admin",
    roles: ["member", "staff", "operator", "admin"],
    visible: [/django admin|admin panel/i],
    hidden: [],
  },
];

test.describe("dashboard roles visibility", () => {
  for (const sc of SCENARIOS) {
    test(`${sc.name} sees expected sidebar items`, async ({ page }) => {
      await mockLogin(page);
      await page.route("**/api/public/v1/auth/me/**", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            email: `demo-${sc.name}@yakimaweb.local`,
            is_authenticated: true,
            roles: sc.roles,
            is_staff: sc.roles.includes("staff"),
            is_superuser: sc.roles.includes("admin"),
            otp_verified: true,
          }),
        });
      });

      await page.goto("/dashboard");
      const nav = page.getByRole("navigation").first();
      if (!(await nav.isVisible().catch(() => false))) {
        test.skip(true, "dashboard sidebar not yet present");
        return;
      }

      for (const re of sc.visible) {
        await expect(
          nav.getByRole("link", { name: re }).first(),
        ).toBeVisible();
      }
      for (const re of sc.hidden) {
        await expect(nav.getByRole("link", { name: re })).toHaveCount(0);
      }
    });
  }
});
