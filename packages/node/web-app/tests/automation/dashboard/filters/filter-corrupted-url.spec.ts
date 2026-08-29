import { test, expect } from '@playwright/test';

test.describe('Dashboard Filters - Corrupted URL Graceful Fallback Edgecase', () => {
  test('should handle corrupted URL search params gracefully without crashing UI', async ({ page }) => {
    await page.goto('/?timeRange=invalid_time_range_999&environment=hacked_env');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    expect(bodyText).not.toContain('Application error');
    expect(bodyText).not.toContain('Unhandled Runtime Error');
  });
});
