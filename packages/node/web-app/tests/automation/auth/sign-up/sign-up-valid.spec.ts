import { test, expect } from '@playwright/test';
import { SignUpPage } from '../../page-objects/auth/sign-up.page';
import { generateUniqueEmail } from '../../fixtures/generators/unique-email';

test.describe('Category A — Happy Path Registration Automation', () => {
  test('should successfully register new organization and admin user', async ({ page }) => {
    const signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    const uniqueEmail = generateUniqueEmail('signup.valid');
    await signUpPage.fillForm({
      name: 'Valid Admin User',
      orgName: 'Scaibu Enterprise',
      email: uniqueEmail,
      password: 'SecurePassword123!',
    });

    await signUpPage.submit();
    await signUpPage.assertNoConsoleErrors();
  });
});
