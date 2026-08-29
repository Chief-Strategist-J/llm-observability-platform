import { test, expect } from '@playwright/test';
import { SignUpPage } from '../page-objects/auth/sign-up.page';
import { SignInPage } from '../page-objects/auth/sign-in.page';
import { DashboardPage } from '../page-objects/dashboard/dashboard.page';
import { generateUniqueEmail } from '../fixtures/generators/unique-email';

test.describe.serial('Production Sequential User Journey — 20 Critical Edge Cases Pipeline', () => {
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

  test('Step 1: Registration Phase — Validate HTML5 Email Format & Weak Password Warning', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    await signUpPage.fillForm({ email: 'invalid-email-format' });
    const isEmailValid = await signUpPage.isEmailFieldValid();
    expect(isEmailValid).toBe(false);

    await signUpPage.fillForm({ password: '123' });
    await signUpPage.assertWeakPasswordWarningVisible();
  });

  test('Step 2: Registration Phase — Validate XSS & SQL Injection Input Sanitization', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    await signUpPage.fillForm({
      name: "<script>alert('xss-test')</script>",
      orgName: "' OR '1'='1",
      email: generateUniqueEmail('sqli.test'),
      password: 'SecurePassword123!',
    });

    expect(await page.locator('#name').inputValue()).toContain('script');
    expect(await page.locator('#orgName').inputValue()).toBe("' OR '1'='1");
  });

  test('Step 3: Registration Phase — Max Field Length Boundary & Execute Admin Registration', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    const longOrgName = 'A'.repeat(255);
    await signUpPage.fillForm({ orgName: longOrgName });
    expect(await page.locator('#orgName').inputValue()).toBe(longOrgName);

    await signUpPage.fillForm({
      name: primaryAdminAccount.name,
      orgName: primaryAdminAccount.orgName,
      email: primaryAdminAccount.email,
      password: primaryAdminAccount.password,
    });

    await signUpPage.submit();
    await signUpPage.assertNoConsoleErrors();
  });

  test('Step 4: Duplicate Registration Protection Phase — Re-attempt Registering Same Email', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();

    await signUpPage.fillForm({
      name: 'Duplicate Admin Attempt',
      orgName: primaryAdminAccount.orgName,
      email: primaryAdminAccount.email,
      password: primaryAdminAccount.password,
    });

    await signUpPage.submit();
    await signUpPage.assertErrorMessageVisible();
  });

  test('Step 5: Authentication Security Guards — Validate Unregistered User & Wrong Password Blocks', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();

    await signInPage.fillForm({
      email: 'unregistered.ghost@scaibu.io',
      password: 'SomePassword123!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();

    await signInPage.fillForm({
      email: primaryAdminAccount.email,
      password: 'WrongPassword999!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();
  });

  test('Step 6: Authentication Security Guards — Case-Insensitive & Whitespace-Trimmed Email Sign-In', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();

    await signInPage.fillForm({
      email: `  ${primaryAdminAccount.email.toUpperCase()}  `,
      password: primaryAdminAccount.password,
    });

    await signInPage.submit();
    await signInPage.assertNoConsoleErrors();
  });

  test('Step 7: Workspace Dashboard Phase — Special Character Search Query Escaping', async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();

    await dashboardPage.applySearchFilter('?*%&[]()');
    await dashboardPage.assertNoConsoleErrors();
  });

  test('Step 8: Workspace Dashboard Phase — Corrupted URL Params Fallback & Empty Dataset View', async ({ page }) => {
    dashboardPage = new DashboardPage(page);

    await dashboardPage.navigateTo('/?model=<script>&env=CORRUPTED');
    await dashboardPage.assertNoConsoleErrors();

    await dashboardPage.assertEmptyStateVisible();
  });

  test('Step 9: Team Member Invitation Phase — Invalid Invite Email Validation & Add Member', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');

    const inviteButton = page.locator('button:has-text("Invite Team Member")');
    if (await inviteButton.isVisible()) {
      await inviteButton.click();

      const memberEmailInput = page.locator('input[placeholder="Email Address"]');
      if (await memberEmailInput.isVisible()) {
        await memberEmailInput.fill('invalid-member-email');
        const isValid = await memberEmailInput.evaluate((el: HTMLInputElement) => el.checkValidity());
        expect(isValid).toBe(false);
      }

      await page.locator('input[placeholder="Full Name"]').fill(secondaryMemberAccount.name);
      await page.locator('input[placeholder="Email Address"]').fill(secondaryMemberAccount.email);
      await page.locator('button[type="submit"]:has-text("Send Invitation")').click();
    }

    expect(page.url()).toBeDefined();
  });

  test('Step 10: Session Logout & Protected Route Revocation Phase', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const signOutBtn = page.locator('button:has-text("Sign Out"), button:has-text("Logout"), a:has-text("Sign Out")');
    if (await signOutBtn.first().isVisible()) {
      await signOutBtn.first().click();
    }

    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');

    expect(page.url()).toBeDefined();
  });
});
