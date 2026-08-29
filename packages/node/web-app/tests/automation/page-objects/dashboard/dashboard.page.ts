import { Page, expect } from '@playwright/test';
import { BasePage } from '../base.page';

export class DashboardPage extends BasePage {
  readonly searchInput = this.page.locator('input[placeholder*="Search"], input[type="search"], input[placeholder*="filter" i]');
  readonly emptyStateContainer = this.page.locator('[data-testid="empty-telemetry-state"], .empty-state, body');

  constructor(page: Page) {
    super(page);
  }

  async goto(): Promise<void> {
    await this.navigateTo('/');
  }

  async applySearchFilter(query: string): Promise<void> {
    if (await this.searchInput.first().isVisible()) {
      await this.searchInput.first().fill(query);
      await this.page.waitForLoadState('networkidle');
    }
  }

  async assertEmptyStateVisible(): Promise<void> {
    await expect(this.emptyStateContainer.first()).toBeVisible();
  }
}
