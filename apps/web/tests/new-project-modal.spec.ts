import { test, expect } from '@playwright/test';

// Mock API responses for project creation
async function mockProjectCreation(page) {
  await page.route('**/api/bridge/odl/**', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ id: 'test-project' })
    });
  });
}

test.describe('New Project modal', () => {
  test('dashboard button opens and closes modal', async ({ page }) => {
    await page.goto('/dashboard');
    await page.getByRole('button', { name: 'New Project' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(dialog).toBeHidden();
  });

  test('dashboard quick action card opens modal', async ({ page }) => {
    await page.goto('/dashboard');
    await page.getByRole('heading', { name: 'Create PV System' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
  });

  test('projects page button opens modal', async ({ page }) => {
    await page.goto('/projects');
    await page.getByRole('button', { name: 'New Project' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await page.getByRole('button', { name: 'Cancel' }).click();
    await expect(dialog).toBeHidden();
  });

  test('submitting modal navigates to new project', async ({ page }) => {
    await mockProjectCreation(page);
    await page.goto('/dashboard');
    await page.getByRole('heading', { name: 'Create PV System' }).click();
    await page.getByLabel('Project Name *').fill('Test Project');
    // Select scale
    await page.locator('label:has-text("Scale")').locator('..').locator('button').click();
    await page.getByRole('option').first().click();
    await page.getByRole('button', { name: 'Create Project' }).click();
    await page.waitForURL('**/projects/test-project');
  });
});
