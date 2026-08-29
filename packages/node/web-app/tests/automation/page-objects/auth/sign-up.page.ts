import { Page, expect } from '@playwright/test';
import { BasePage } from '../base.page';

export class SignUpPage extends BasePage {
  readonly nameInput = this.page.locator('#name');
  readonly orgNameInput = this.page.locator('#orgName');
  readonly emailInput = this.page.locator('#email');
  readonly passwordInput = this.page.locator('#password');
  readonly submitButton = this.page.locator('button[type="submit"]');
  readonly errorMessage = this.page.locator('.auth-error-alert, [data-testid="error-alert"], .error-message');
  readonly weakPasswordWarning = this.page.locator('.auth-strength-label, [data-testid="password-meter-warning"]');

  constructor(page: Page) {
    super(page);
  }

  async goto(): Promise<void> {
    await this.navigateTo('/auth/sign-up');
    await expect(this.nameInput).toBeVisible();
  }

  async fillForm(details: { name?: string; orgName?: string; email?: string; password?: string }): Promise<void> {
    if (details.name !== undefined) await this.nameInput.fill(details.name);
    if (details.orgName !== undefined) await this.orgNameInput.fill(details.orgName);
    if (details.email !== undefined) await this.emailInput.fill(details.email);
    if (details.password !== undefined) await this.passwordInput.fill(details.password);
  }

  async submit(): Promise<void> {
    await expect(this.submitButton).toBeEnabled();
    await this.submitButton.click();
  }

  async assertErrorMessageVisible(expectedTextPattern?: RegExp | string): Promise<void> {
    await expect(this.errorMessage.first()).toBeVisible();
    if (expectedTextPattern) {
      await expect(this.errorMessage.first()).toContainText(expectedTextPattern);
    }
  }

  async assertWeakPasswordWarningVisible(): Promise<void> {
    await expect(this.weakPasswordWarning.first()).toBeVisible();
    await expect(this.weakPasswordWarning.first()).toContainText(/Weak|Strength/i);
  }

  async isEmailFieldValid(): Promise<boolean> {
    return await this.emailInput.evaluate((el: HTMLInputElement) => el.checkValidity());
  }
}
