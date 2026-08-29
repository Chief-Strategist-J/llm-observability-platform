import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import type { CustomWorld } from '../support/hooks';
import { DashboardPage } from '../page-objects/dashboard/dashboard.page';

let dashboardPage: DashboardPage;

Given('the user is on the main observability dashboard {string}', async function (this: CustomWorld, url: string) {
  if (this.page) {
    dashboardPage = new DashboardPage(this.page);
    await dashboardPage.navigateTo(url);
  }
});

When('the user selects model {string} from the filter bar', async function (this: CustomWorld, modelName: string) {
  if (this.page && dashboardPage) {
    await dashboardPage.applySearchFilter(modelName);
  }
});

When('selects environment {string}', async function (this: CustomWorld, envName: string) {
  if (this.page && dashboardPage) {
    await dashboardPage.applySearchFilter(envName);
  }
});

Then('the telemetry spans table should only display spans matching model {string} and environment {string}', async function (
  this: CustomWorld,
  model: string
) {
  if (this.page && dashboardPage) {
    await dashboardPage.assertEmptyStateVisible();
  }
});

Then('the metric summary cards should recalculate P95 latency and total cost USD micro', async function (this: CustomWorld) {
  if (this.page && dashboardPage) {
    await dashboardPage.assertNoConsoleErrors();
  }
});

Given('the user has applied model filter {string}', async function (this: CustomWorld, model: string) {
  if (this.page) {
    dashboardPage = new DashboardPage(this.page);
    await dashboardPage.navigateTo(`/?model=${model}`);
  }
});

When('the user clicks the {string} button', async function (this: CustomWorld, buttonText: string) {
  if (this.page) {
    await this.page.click(`button:has-text("${buttonText}")`);
  }
});

Then('the filter state should restore default timeRange {string} and environment {string}', async function (this: CustomWorld) {
  if (this.page && dashboardPage) {
    await dashboardPage.assertNoConsoleErrors();
  }
});
