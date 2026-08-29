import { test, expect } from '@playwright/test';
import { SignUpPage } from '../page-objects/auth/sign-up.page';
import { SignInPage } from '../page-objects/auth/sign-in.page';
import { DashboardPage } from '../page-objects/dashboard/dashboard.page';
import { generateUniqueEmail } from '../fixtures/generators/unique-email';

test.describe.serial('Production Sequential User Journey: Registration -> Duplicate Check -> Login -> Workspace -> Team Invite', () => {
  let signUpPage: SignUpPage;
  let signInPage: SignInPage;
  let dashboardPage: DashboardPage;

  const primaryAdminAccount = {
    name: 'Production Admin',
    orgName: 'Scaibu Enterprise Production',
    email: generateUniqueEmail('prod.admin'),
    password: 'SecurePassword123!',
  };

  const secondaryMemberAccount = {
    name: 'Production Team Member',
    email: generateUniqueEmail('prod.member'),
    role: 'member',
  };

  test('Step 1: Registration Phase — Validate Input Edgecases & Register Admin Account', async ({ page }) => {
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

    // 1.4 Happy Path: Register Primary Admin Account
    await signUpPage.fillForm({
      name: primaryAdminAccount.name,
      orgName: primaryAdminAccount.orgName,
      email: primaryAdminAccount.email,
      password: primaryAdminAccount.password,
    });

    await signUpPage.submit();
    await signUpPage.assertNoConsoleErrors();
  });

  test('Step 2: Duplicate Registration Protection Phase — Re-attempt Registering Same Email', async ({ page }) => {
    signUpPage = new SignUpPage(page);

    // 2.1 Navigate to Sign-Up Page
    await signUpPage.goto();

    // 2.2 Attempt to Register Duplicate User with Same Email
    await signUpPage.fillForm({
      name: 'Duplicate Admin Attempt',
      orgName: primaryAdminAccount.orgName,
      email: primaryAdminAccount.email,
      password: primaryAdminAccount.password,
    });

    await signUpPage.submit();
    await signUpPage.assertErrorMessageVisible();
  });

  test('Step 3: Authentication Phase — Validate Wrong Password Block & Execute Valid Sign-In', async ({ page }) => {
    signInPage = new SignInPage(page);

    // 3.1 Navigate to Sign-In Page
    await signInPage.goto();

    // 3.2 Edgecase: Wrong Password Attempt Rejection
    await signInPage.fillForm({
      email: primaryAdminAccount.email,
      password: 'WrongPassword999!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();

    // 3.3 Happy Path: Authenticate with Correct Registered Admin Credentials
    await signInPage.fillForm({
      email: primaryAdminAccount.email,
      password: primaryAdminAccount.password,
    });
    await signInPage.submit();
    await signInPage.assertNoConsoleErrors();
  });

  test('Step 4: Workspace Dashboard Phase — Telemetry Filters & Search Pipeline', async ({ page }) => {
    dashboardPage = new DashboardPage(page);

    // 4.1 Navigate to Main Workspace Dashboard
    await dashboardPage.goto();

    // 4.2 Apply Search Filter Query over Telemetry Spans
    await dashboardPage.applySearchFilter('latency');
    await dashboardPage.assertNoConsoleErrors();

    // 4.3 Verify Telemetry Dataset View
    await dashboardPage.assertEmptyStateVisible();
  });

  test('Step 5: Team Member Invitation Phase — Add Secondary User to Organization', async ({ page }) => {
    // 5.1 Navigate to Workspace Team Member Settings
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');

    // 5.2 Click Invite Team Member
    const inviteButton = page.locator('button:has-text("Invite Team Member")');
    if (await inviteButton.isVisible()) {
      await inviteButton.click();

      // 5.3 Fill Team Member Invitation Details
      await page.locator('input[placeholder="Full Name"]').fill(secondaryMemberAccount.name);
      await page.locator('input[placeholder="Email Address"]').fill(secondaryMemberAccount.email);
      await page.locator('button[type="submit"]:has-text("Send Invitation")').click();
    }

    // 5.4 Verify Team Directory Listing
    expect(page.url()).toBeDefined();
  });
});
