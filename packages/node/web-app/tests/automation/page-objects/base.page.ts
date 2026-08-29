import { Page, expect } from '@playwright/test';

export abstract class BasePage {
  protected consoleErrors: string[] = [];

  constructor(protected page: Page) {
    this.page.on('console', (msg) => {
      if (msg.type() === 'error') {
        this.consoleErrors.push(msg.text());
      }
    });
  }

  async navigateTo(path: string): Promise<void> {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  async waitForElementVisible(selector: string, timeout = 5000): Promise<void> {
    const element = this.page.locator(selector);
    await expect(element).toBeVisible({ timeout });
  }

  async assertNoConsoleErrors(): Promise<void> {
    const criticalErrors = this.consoleErrors.filter(
      (err) => !err.includes('Favicon') && !err.includes('download the React DevTools')
    );
    expect(criticalErrors).toHaveLength(0);
  }

  async waitForPageTransition(expectedUrlPattern: RegExp | string): Promise<void> {
    await this.page.waitForURL(expectedUrlPattern);
    await this.page.waitForLoadState('domcontentloaded');
  }
}
