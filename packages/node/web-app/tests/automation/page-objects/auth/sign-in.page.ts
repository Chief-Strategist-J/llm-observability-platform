import { Page, expect } from '@playwright/test';
import { BasePage } from '../base.page';

export class SignInPage extends BasePage {
  readonly emailInput = this.page.locator('#email');
  readonly passwordInput = this.page.locator('#password');
  readonly submitButton = this.page.locator('button[type="submit"]');
  readonly errorMessage = this.page.locator('[data-testid="error-alert"], .error-message, .text-red-500');

  constructor(page: Page) {
    super(page);
  }

  async goto(): Promise<void> {
    await this.navigateTo('/auth/sign-in');
    await expect(this.emailInput).toBeVisible();
  }

  async fillForm(credentials: { email?: string; password?: string }): Promise<void> {
    if (credentials.email !== undefined) await this.emailInput.fill(credentials.email);
    if (credentials.password !== undefined) await this.passwordInput.fill(credentials.password);
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
}
