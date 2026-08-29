import { test, expect } from '@playwright/test';

test.describe('Auth Registration - Invalid Email Edgecase Automation', () => {
  test('should trigger native HTML5 validation on malformed email format', async ({ page }) => {
    await page.goto('/auth/sign-up');
    await page.waitForLoadState('networkidle');

    const emailInput = page.locator('#email');
    await emailInput.fill('invalid-email-format-no-at-symbol');

    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();

    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.checkValidity());
    expect(isValid).toBe(false);
  });
});
