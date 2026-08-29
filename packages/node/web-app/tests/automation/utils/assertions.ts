import { Page, expect } from '@playwright/test';

export async function assertCleanConsoleLogs(page: Page): Promise<void> {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  const criticalErrors = errors.filter(
    (err) => !err.includes('Favicon') && !err.includes('download the React DevTools')
  );

  expect(criticalErrors).toHaveLength(0);
}
