import { test, expect } from '@playwright/test';

test.describe('Auth Registration - Valid User Registration Automation', () => {
  test('should successfully register new organization and admin user', async ({ page }) => {
    await page.goto('/auth/sign-up');
    await page.waitForLoadState('networkidle');

    await page.locator('#name').fill('Jaydeep Engineer');
    await page.locator('#orgName').fill('Scaibu Platform');
    await page.locator('#email').fill(`jaydeep.${Date.now()}@scaibu.io`);
    await page.locator('#password').fill('SecurePassword123!');

    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();
  });
});
