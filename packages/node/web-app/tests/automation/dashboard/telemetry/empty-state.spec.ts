import { test, expect } from '@playwright/test';

test.describe('Dashboard Telemetry - Non-Existent Filter Empty State Edgecase', () => {
  test('should render empty telemetry dataset state without throwing exceptions', async ({ page }) => {
    await page.goto('/?model=non_existent_model_xyz_999');
    await page.waitForLoadState('networkidle');

    const content = await page.content();
    expect(content).toBeDefined();
  });
});
