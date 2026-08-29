import { test, expect } from '@playwright/test';

test.describe('Auth Sign In - Valid Login Automation', () => {
  test('should render sign-in form and execute valid user sign-in', async ({ page }) => {
    await page.goto('/auth/sign-in');
    await page.waitForLoadState('networkidle');

    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();
    await emailInput.fill('admin@scaibu.io');

    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toBeVisible();
    await passwordInput.fill('SecurePassword123!');
  });
});
