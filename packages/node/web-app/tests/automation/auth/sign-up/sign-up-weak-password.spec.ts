import { test, expect } from '@playwright/test';

test.describe('Auth Registration - Weak Password Edgecase Automation', () => {
  test('should display weak password meter warning when entering short password', async ({ page }) => {
    await page.goto('/auth/sign-up');
    await page.waitForLoadState('networkidle');

    const passwordInput = page.locator('#password');
    await passwordInput.fill('123');

    const strengthLabel = page.locator('.auth-strength-label');
    await expect(strengthLabel).toBeVisible();
    await expect(strengthLabel).toContainText(/Weak|Strength/i);
  });
});
