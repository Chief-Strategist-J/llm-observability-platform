import { defineConfig, devices } from '@playwright/test';

const isHeaded = process.env.HEADED === 'true' || process.argv.includes('--headed');

export default defineConfig({
  testDir: './tests/automation',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: isHeaded ? 1 : 2,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'playwright-report/results.json' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:31400',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    headless: !isHeaded,
    launchOptions: {
      slowMo: isHeaded ? 400 : 0,
    },
  },
  webServer: {
    command: './scripts/app.sh web-app',
    url: 'http://localhost:31400',
    reuseExistingServer: true,
    timeout: 120 * 1000,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        browserName: 'chromium',
      },
    },
  ],
});
