import { test, expect } from '@playwright/test';
import { SignInPage } from '../../page-objects/auth/sign-in.page';

test.describe('Category C — Sign-In Incorrect Password Automation', () => {
  test('should validate form and block sign-in on wrong password', async ({ page }) => {
    const signInPage = new SignInPage(page);
    await signInPage.goto();

    await signInPage.fillForm({
      email: 'admin@scaibu.io',
      password: 'WrongPassword999!',
    });

    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();
  });
});
