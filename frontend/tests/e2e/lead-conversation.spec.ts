import { test, expect } from "./helpers/fixtures";

/**
 * Sprint 4 — Vendor lead conversation: send reply, mark won.
 */

test.describe("vendor lead conversation (Sprint 4)", () => {
  test("vendor opens lead, replies, marks won", async ({ vendorPage: page }) => {
    const leadId = 42;
    let leadStatus = "pending";
    type Message = {
      id: number;
      sender: { id: number; display_name: string };
      body: string;
      created_at: string;
    };
    const messages: Message[] = [
      {
        id: 1,
        sender: { id: 7, display_name: "Buyer" },
        body: "Hi, can you do a 1500 sqft listing on Friday?",
        created_at: new Date(Date.now() - 60_000).toISOString(),
      },
    ];

    await page.route("**/api/v1/me/", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 99,
          email: "demo-vendor@yakimaweb.local",
          display_name: "Demo Vendor",
          is_realtor: false,
          is_vendor: true,
          is_staff: false,
        }),
      });
    });

    await page.route("**/api/v1/me/notifications/**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ count: 0, results: [] }),
      });
    });

    await page.route(`**/api/v1/leads/${leadId}/`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: leadId,
          status: leadStatus,
          message: "Hi, can you do a 1500 sqft listing on Friday?",
          buyer: { id: 7, display_name: "Buyer", email: "buyer@example.com" },
          vendor: { id: 99, business_name: "Yakima Photo Co" },
          service: { id: 5, title: "Listing essentials" },
          package: null,
          bundle: null,
          created_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(
      `**/api/v1/leads/${leadId}/messages/**`,
      async (route) => {
        const method = route.request().method();
        if (method === "POST") {
          const body = JSON.parse(route.request().postData() || "{}");
          const msg: Message = {
            id: messages.length + 1,
            sender: { id: 99, display_name: "Demo Vendor" },
            body: body.body,
            created_at: new Date().toISOString(),
          };
          messages.push(msg);
          await route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify(msg),
          });
          return;
        }
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ results: messages, next: null, previous: null }),
        });
      },
    );

    await page.route(
      `**/api/v1/leads/${leadId}/status/`,
      async (route) => {
        const body = JSON.parse(route.request().postData() || "{}");
        leadStatus = body.status || leadStatus;
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: leadId,
            status: leadStatus,
            message: "—",
            buyer: { id: 7, display_name: "Buyer", email: "buyer@example.com" },
            vendor: { id: 99, business_name: "Yakima Photo Co" },
            service: { id: 5, title: "Listing essentials" },
            package: null,
            bundle: null,
            created_at: new Date().toISOString(),
          }),
        });
      },
    );

    // Block real EventSource — let the polling fallback engage.
    await page.route(`**/api/v1/streams/leads/${leadId}/messages/`, (route) =>
      route.fulfill({ status: 404, body: "" }),
    );

    await page.goto(`/dashboard/vendor/leads/${leadId}`);

    await expect(
      page.getByText(/can you do a 1500 sqft listing/i),
    ).toBeVisible({ timeout: 10_000 });

    // Send a reply
    await page
      .getByPlaceholder(/type your reply/i)
      .fill("Yes — Friday afternoon works.");
    await page.getByRole("button", { name: /^send$/i }).click();

    await expect(
      page.getByText(/yes — friday afternoon works\./i),
    ).toBeVisible();

    // Mark as won via dropdown
    const select = page.locator("select").first();
    await select.selectOption("won");
    await expect(
      page.getByText(/the buyer can now leave a review/i),
    ).toBeVisible();
  });
});
