import { test } from '@playwright/test';
import { SignInPage } from '../../page-objects/auth/sign-in.page';

test.describe('Category A — Sign-In Valid User Automation', () => {
  test('should render sign-in form and execute valid user sign-in', async ({ page }) => {
    const signInPage = new SignInPage(page);
    await signInPage.goto();

    await signInPage.fillForm({
      email: 'admin@scaibu.io',
      password: 'SecurePassword123!',
    });

    await signInPage.submit();
    await signInPage.assertNoConsoleErrors();
  });
});
