import { test, expect } from '@playwright/test';
import { SignUpPage } from '../page-objects/auth/sign-up.page';
import { SignInPage } from '../page-objects/auth/sign-in.page';
import { DashboardPage } from '../page-objects/dashboard/dashboard.page';
import { generateUniqueEmail } from '../fixtures/generators/unique-email';

test.describe.serial('Sequential User Journey: Registration -> Login -> Dashboard', () => {
  let signUpPage: SignUpPage;
  let signInPage: SignInPage;
  let dashboardPage: DashboardPage;

  const sharedAccount = {
    name: 'Sequential User',
    orgName: 'Sequential Scaibu Inc',
    email: generateUniqueEmail('seq.journey'),
    password: 'SecurePassword123!',
  };

  test('Step 1: Registration Phase — Validate Edge Cases & Register New Account', async ({ page }) => {
    signUpPage = new SignUpPage(page);

    // 1.1 Navigate to Sign-Up Page
    await signUpPage.goto();

    // 1.2 Edgecase: Invalid Email Format HTML5 Validation
    await signUpPage.fillForm({ email: 'invalid-email-format' });
    const isEmailValid = await signUpPage.isEmailFieldValid();
    expect(isEmailValid).toBe(false);

    // 1.3 Edgecase: Weak Password Warning Meter
    await signUpPage.fillForm({ password: '123' });
    await signUpPage.assertWeakPasswordWarningVisible();

    // 1.4 Happy Path: Submit Valid Registration Form
    await signUpPage.fillForm({
      name: sharedAccount.name,
      orgName: sharedAccount.orgName,
      email: sharedAccount.email,
      password: sharedAccount.password,
    });

    await signUpPage.submit();
    await signUpPage.assertNoConsoleErrors();
  });

  test('Step 2: Sign-In Phase — Validate Auth Guards & Authenticate Account', async ({ page }) => {
    signInPage = new SignInPage(page);

    // 2.1 Navigate to Sign-In Page
    await signInPage.goto();

    // 2.2 Edgecase: Wrong Password Rejection
    await signInPage.fillForm({
      email: sharedAccount.email,
      password: 'WrongPassword999!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();

    // 2.3 Happy Path: Authenticate with Registered Credentials
    await signInPage.fillForm({
      email: sharedAccount.email,
      password: sharedAccount.password,
    });
    await signInPage.submit();
    await signInPage.assertNoConsoleErrors();
  });

  test('Step 3: Dashboard Phase — Workspace Filters & Telemetry Visualizations', async ({ page }) => {
    dashboardPage = new DashboardPage(page);

    // 3.1 Navigate to Workspace Dashboard
    await dashboardPage.goto();

    // 3.2 Apply Search Filter Query
    await dashboardPage.applySearchFilter('latency');
    await dashboardPage.assertNoConsoleErrors();

    // 3.3 Verify Telemetry Dataset View
    await dashboardPage.assertEmptyStateVisible();
  });
});
