import { test, expect } from "@playwright/test";

test.describe("Redaction Overlay", () => {
  test("draws and saves redactions", async ({ page }) => {
    let requestBody: any = null;
    await page.route("**/api/media/redaction", async (route) => {
      requestBody = await route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ status: "ok" }),
      });
    });

    await page.goto("/media/redaction");

    const overlay = page.getByTestId("redaction-overlay");
    const box = await overlay.boundingBox();
    if (!box) throw new Error("overlay not found");

    await page.mouse.move(box.x + 10, box.y + 10);
    await page.mouse.down();
    await page.mouse.move(box.x + 100, box.y + 100);
    await page.mouse.up();

    await expect(page.getByTestId("redaction-box")).toBeVisible();
    await expect(page.getByTestId("privacy-banner")).toBeVisible();

    await Promise.all([
      page.waitForResponse("**/api/media/redaction"),
      page.getByRole("button", { name: "Save Redactions" }).click(),
    ]);

    expect(requestBody).not.toBeNull();
    expect(requestBody.doc_type).toBe("sld");
    expect(Array.isArray(requestBody.boxes)).toBeTruthy();
  });
});
