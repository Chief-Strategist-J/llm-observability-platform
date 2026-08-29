import { test } from '@playwright/test';
import { SignUpPage } from '../../page-objects/auth/sign-up.page';

test.describe('Category B — Duplicate User Registration Automation', () => {
  test('should handle duplicate user registration error gracefully', async ({ page }) => {
    const signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    await signUpPage.fillForm({
      name: 'Duplicate Admin User',
      orgName: 'Scaibu Enterprise',
      email: 'admin@scaibu.io',
      password: 'SecurePassword123!',
    });

    await signUpPage.submit();
    await signUpPage.assertErrorMessageVisible();
  });
});
