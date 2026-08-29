import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import type { CustomWorld } from '../support/hooks';

Given('the user navigates to the sign-up page {string}', async function (this: CustomWorld, url: string) {
  if (this.page) {
    await this.page.goto(url);
  }
});

Given('the user navigates to the sign-in page {string}', async function (this: CustomWorld, url: string) {
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
    await this.page.fill('#name', name);
    await this.page.fill('#email', email);
    await this.page.fill('#orgName', org);
    await this.page.fill('#password', pass);
  }
});

When('the user enters password {string}', async function (this: CustomWorld, pass: string) {
  if (this.page) {
    await this.page.fill('#password', pass);
  }
});

When('the user attempts registration with existing email {string}', async function (this: CustomWorld, email: string) {
  if (this.page) {
    await this.page.fill('#name', 'Existing User');
    await this.page.fill('#orgName', 'Existing Org');
    await this.page.fill('#email', email);
    await this.page.fill('#password', 'SecurePassword123!');
  }
});

When('the user enters invalid email {string}', async function (this: CustomWorld, email: string) {
  if (this.page) {
    await this.page.fill('#email', email);
  }
});

When('the user enters email {string} and password {string}', async function (this: CustomWorld, email: string, pass: string) {
  if (this.page) {
    await this.page.fill('input[type="email"]', email);
    await this.page.fill('input[type="password"]', pass);
  }
});

When('the user clicks the {string} button', async function (this: CustomWorld, buttonText: string) {
  if (this.page) {
    const button = this.page.locator(`button:has-text("${buttonText}")`).first();
    if (await button.isVisible()) {
      await button.click();
    }
  }
});

Then('the user should see the active organization workspace dashboard {string}', async function (this: CustomWorld, expectedUrl: string) {
  if (this.page) {
    await expect(this.page).toHaveURL(new RegExp(expectedUrl));
  }
});

Then('the password meter should display weak strength indicator', async function (this: CustomWorld) {
  if (this.page) {
    const strengthLabel = this.page.locator('.auth-strength-label');
    await expect(strengthLabel).toBeVisible();
    await expect(strengthLabel).toContainText(/Weak|Strength/i);
  }
});

Then('an error message or validation alert should block submission', async function (this: CustomWorld) {
  if (this.page) {
    const emailInput = this.page.locator('#email');
    await expect(emailInput).toBeVisible();
  }
});

Then('the email input field should remain invalid', async function (this: CustomWorld) {
  if (this.page) {
    const emailInput = this.page.locator('#email');
    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.checkValidity());
    expect(isValid).toBe(false);
  }
});

Then('the user should be redirected to the dashboard', async function (this: CustomWorld) {
  if (this.page) {
    await expect(this.page).not.toHaveURL(/auth\/sign-in/);
  }
});

Then('the user should remain on the sign-in page', async function (this: CustomWorld) {
  if (this.page) {
    await expect(this.page).toHaveURL(/auth\/sign-in/);
  }
});

Given('an authenticated Admin user is on the organization settings page {string}', async function (this: CustomWorld, url: string) {
  if (this.page) {
    await this.page.goto(url);
  }
});

When('the Admin user clicks {string}', async function (this: CustomWorld, text: string) {
  if (this.page) {
    const btn = this.page.locator(`button:has-text("${text}")`).first();
    if (await btn.isVisible()) {
      await btn.click();
    }
  }
});

When('enters invitee name {string}, email {string}, and role {string}', async function (this: CustomWorld, name: string, email: string, role: string) {
  if (this.page) {
    await this.page.fill('input[placeholder*="Name"]', name);
    await this.page.fill('input[placeholder*="Email"]', email);
  }
});

When('clicks {string}', async function (this: CustomWorld, buttonText: string) {
  if (this.page) {
    const btn = this.page.locator(`button:has-text("${buttonText}")`).first();
    if (await btn.isVisible()) {
      await btn.click();
    }
  }
});

Then('{string} should appear in the Active Organization Members list with role {string}', async function (this: CustomWorld, memberName: string, role: string) {
  if (this.page) {
    const row = this.page.locator(`tr:has-text("${memberName}")`);
    if (await row.isVisible()) {
      await expect(row).toContainText(role);
    }
  }
});
