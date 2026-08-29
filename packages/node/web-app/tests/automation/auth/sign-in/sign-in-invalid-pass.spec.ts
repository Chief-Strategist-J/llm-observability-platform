import { test, expect } from '@playwright/test';

test.describe('Auth Sign In - Invalid Password Edgecase Automation', () => {
  test('should validate form and block sign-in on wrong password', async ({ page }) => {
    await page.goto('/auth/sign-in');
    await page.waitForLoadState('networkidle');

    await page.locator('input[type="email"]').fill('admin@scaibu.io');
    await page.locator('input[type="password"]').fill('WrongPassword999');

    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();
    await expect(page).toHaveURL(/auth\/sign-in/);
  });
});
