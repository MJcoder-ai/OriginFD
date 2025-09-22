import { test, expect, Page, Route } from "@playwright/test";

// Mock API responses for project creation
async function mockProjectCreation(page: Page) {
  await page.route("**/projects/**", (route: Route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: "test-project" }),
    });
  });
}

test.describe("New Project modal", () => {
  test("dashboard button opens and closes modal", async ({ page }) => {
    await page.goto("/dashboard");
    await page.getByRole("button", { name: "New Project" }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).toBeHidden();
  });

  test("dashboard quick action card opens modal", async ({ page }) => {
    await page.goto("/dashboard");
    await page.getByRole("heading", { name: "Create PV System" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).click();
  });

  test("projects page button opens modal", async ({ page }) => {
    await page.goto("/projects");
    await page.getByRole("button", { name: "New Project" }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await page.getByRole("button", { name: "Cancel" }).click();
    await expect(dialog).toBeHidden();
  });

  test("submitting modal navigates to new project", async ({ page }) => {
    await mockProjectCreation(page);
    await page.goto("/dashboard");
    await page.getByRole("heading", { name: "Create PV System" }).click();
    await page.getByLabel("Project Name *").fill("Test Project");
    // Select scale
    await page
      .locator('label:has-text("Scale")')
      .locator("..")
      .locator("button")
      .click();
    await page.getByRole("option").first().click();
    await page.getByRole("button", { name: "Create Project" }).click();
    await page.waitForURL("**/projects/test-project");
  });

  test("sidebar navigation and theme toggle persists", async ({ page }) => {
    await page.goto("/dashboard");
    // Toggle theme to dark via header menu button
    await page.getByRole("button", { name: "Toggle theme" }).click();
    await page.getByRole("menuitem", { name: "Dark" }).click();
    // Navigate to projects page from sidebar link text
    await page.getByRole("link", { name: "Projects" }).click();
    await expect(page).toHaveURL(/.*\/projects$/);
    // Theme class should include dark
    const htmlClass = await page.locator("html").getAttribute("class");
    expect(htmlClass || "").toContain("dark");
  });

  test("open canvas and use layer toggle + zoom controls", async ({ page }) => {
    await page.goto(
      "/projects/proj_550e8400-e29b-41d4-a716-446655440001/canvases",
    );
    // Open LV or MV canvas card button
    await page.getByRole("button", { name: "Open Canvas" }).first().click();
    // Zoom in button should be present
    await page.getByTitle("Zoom In (Ctrl + +)").click();
    // Open keyboard shortcuts overlay
    await page.keyboard.press("?");
    await expect(page.getByText("Keyboard Shortcuts")).toBeVisible();
  });
});
