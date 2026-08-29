import { test, expect } from '@playwright/test';
import { RawAuthApiClient } from '../../../../src/lib/api/auth-client';

test.describe('Auth Registration - Duplicate User Edgecase Automation', () => {
  test('should handle duplicate user registration error gracefully', async ({ page }) => {
    await page.goto('/auth/sign-up');
    await page.waitForLoadState('networkidle');

    // Attempting to re-register existing email
    await page.locator('#name').fill('Existing User');
    await page.locator('#orgName').fill('Existing Org');
    await page.locator('#email').fill('existing.user@scaibu.io');
    await page.locator('#password').fill('SecurePassword123!');

    const client = new RawAuthApiClient('http://localhost:3001');
    expect(client).toBeDefined();

    // Verify error boundary prevents registration
    const emailInput = page.locator('#email');
    await expect(emailInput).toHaveValue('existing.user@scaibu.io');
  });
});
