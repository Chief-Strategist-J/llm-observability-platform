import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import type { CustomWorld } from '../support/hooks';

Given('the user navigates to the sign-up page {string}', async function (this: CustomWorld, url: string) {
  if (this.page) {
    await this.page.goto(url);
  }
});

When('the user enters full name {string}, email {string}, organization {string}, and password {string}', async function (
  this: CustomWorld,
  name: string,
  email: string,
  org: string,
  pass: string
) {
  if (this.page) {
    await this.page.fill('input[placeholder*="Name"]', name);
    await this.page.fill('input[type="email"]', email);
    await this.page.fill('input[placeholder*="Organization"]', org);
    await this.page.fill('input[type="password"]', pass);
  }
});

When('the user clicks the {string} button', async function (this: CustomWorld, buttonText: string) {
  if (this.page) {
    await this.page.click(`button:has-text("${buttonText}")`);
  }
});

Then('the user should see the active organization workspace dashboard {string}', async function (this: CustomWorld, expectedUrl: string) {
  if (this.page) {
    await expect(this.page).toHaveURL(new RegExp(expectedUrl));
  }
});

Then('the user profile role should display {string}', async function (this: CustomWorld, expectedRole: string) {
  if (this.page) {
    const roleBadge = this.page.locator(`text=${expectedRole}`);
    await expect(roleBadge).toBeVisible();
  }
});

Given('an authenticated Admin user is on the organization settings page {string}', async function (this: CustomWorld, url: string) {
  if (this.page) {
    await this.page.goto(url);
  }
});

When('the Admin user clicks {string}', async function (this: CustomWorld, text: string) {
  if (this.page) {
    await this.page.click(`button:has-text("${text}")`);
  }
});

When('enters invitee name {string}, email {string}, and role {string}', async function (this: CustomWorld, name: string, email: string, role: string) {
  if (this.page) {
    await this.page.fill('input[placeholder="Full Name"]', name);
    await this.page.fill('input[placeholder="Email Address"]', email);
  }
});

When('clicks {string}', async function (this: CustomWorld, buttonText: string) {
  if (this.page) {
    await this.page.click(`button:has-text("${buttonText}")`);
  }
});

Then('{string} should appear in the Active Organization Members list with role {string}', async function (this: CustomWorld, memberName: string, role: string) {
  if (this.page) {
    const row = this.page.locator(`tr:has-text("${memberName}")`);
    await expect(row).toBeVisible();
    await expect(row).toContainText(role);
  }
});
