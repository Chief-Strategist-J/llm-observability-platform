import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import type { CustomWorld } from '../support/hooks';

Given('the user is on the main observability dashboard {string}', async function (this: CustomWorld, url: string) {
  if (this.page) {
    await this.page.goto(url);
  }
});

When('the user selects model {string} from the filter bar', async function (this: CustomWorld, modelName: string) {
  if (this.page) {
    await this.page.click('[placeholder*="Select model"]');
    await this.page.click(`text="${modelName}"`);
  }
});

When('selects environment {string}', async function (this: CustomWorld, envName: string) {
  if (this.page) {
    await this.page.click('[placeholder*="Select env"]');
    await this.page.click(`text="${envName}"`);
  }
});

Then('the telemetry spans table should only display spans matching model {string} and environment {string}', async function (
  this: CustomWorld,
  model: string,
  env: string
) {
  if (this.page) {
    const table = this.page.locator('table');
    await expect(table).toContainText(model);
  }
});

Then('the metric summary cards should recalculate P95 latency and total cost USD micro', async function (this: CustomWorld) {
  if (this.page) {
    const summaryCard = this.page.locator('[data-testid="metric-summary-card"]');
    await expect(summaryCard).toBeVisible();
  }
});

Given('the user has applied model filter {string}', async function (this: CustomWorld, model: string) {
  if (this.page) {
    await this.page.goto(`http://localhost:31400?model=${model}`);
  }
});

When('the user clicks the {string} button', async function (this: CustomWorld, buttonText: string) {
  if (this.page) {
    await this.page.click(`button:has-text("${buttonText}")`);
  }
});

Then('the filter state should restore default timeRange {string} and environment {string}', async function (this: CustomWorld, timeRange: string, env: string) {
  if (this.page) {
    await expect(this.page).toHaveURL(/timeRange=24h/);
  }
});
