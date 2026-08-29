import { test, expect } from '@playwright/test';

test.describe('Auth Sign In - Blocked User Edgecase Automation', () => {
  test('should reject authentication attempt for suspended user', async ({ page }) => {
    await page.goto('/auth/sign-in');
    await page.waitForLoadState('networkidle');

    await page.locator('input[type="email"]').fill('blocked.user@scaibu.io');
    await page.locator('input[type="password"]').fill('SecurePassword123!');

    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();

    // Verify user remains on sign-in page
    await expect(page).toHaveURL(/auth\/sign-in/);
  });
});
