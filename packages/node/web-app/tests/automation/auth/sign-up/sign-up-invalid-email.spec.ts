import { test, expect } from '@playwright/test';
import { SignUpPage } from '../../page-objects/auth/sign-up.page';

test.describe('Category C / D — Invalid Email Validation Automation', () => {
  test('should trigger native HTML5 validation on malformed email format', async ({ page }) => {
    const signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    await signUpPage.fillForm({ email: 'not-a-valid-email' });
    const isValid = await signUpPage.isEmailFieldValid();
    expect(isValid).toBe(false);
  });
});
