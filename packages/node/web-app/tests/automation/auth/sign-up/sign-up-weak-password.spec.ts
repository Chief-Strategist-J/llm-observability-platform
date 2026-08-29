import { test } from '@playwright/test';
import { SignUpPage } from '../../page-objects/auth/sign-up.page';

test.describe('Category C / F — Weak Password Contract Boundary Automation', () => {
  test('should display weak password meter warning when entering short password', async ({ page }) => {
    const signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    await signUpPage.fillForm({ password: '123' });
    await signUpPage.assertWeakPasswordWarningVisible();
  });
});
