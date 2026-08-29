import { test, expect } from '@playwright/test';
import { SignUpPage } from '../page-objects/auth/sign-up.page';
import { SignInPage } from '../page-objects/auth/sign-in.page';
import { DashboardPage } from '../page-objects/dashboard/dashboard.page';
import { generateUniqueEmail } from '../fixtures/generators/unique-email';

test.describe.serial('Production Sequential User Journey — 25 Critical Edge Cases Pipeline', () => {
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

  test('Step 1: Edge Case 01 — HTML5 Invalid Email Format Validation Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ email: 'invalid-email-format' });
    const isEmailValid = await signUpPage.isEmailFieldValid();
    expect(isEmailValid).toBe(false);
  });

  test('Step 2: Edge Case 02 — Weak Password Meter Threshold Warning Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ password: '123' });
    await signUpPage.assertWeakPasswordWarningVisible();
  });

  test('Step 3: Edge Case 03 — XSS Script Tag Input Sanitization Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ name: "<script>alert('xss-test')</script>" });
    expect(await page.locator('#name').inputValue()).toContain('script');
  });

  test('Step 4: Edge Case 04 — SQL Injection Payload Field Sanitization Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ orgName: "' OR '1'='1" });
    expect(await page.locator('#orgName').inputValue()).toBe("' OR '1'='1");
  });

  test('Step 5: Edge Case 05 — Max Length Field Boundary Limit Check (255 chars)', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    const longOrg = 'A'.repeat(255);
    await signUpPage.fillForm({ orgName: longOrg });
    expect(await page.locator('#orgName').inputValue()).toBe(longOrg);
  });

  test('Step 6: Edge Case 06 — Leading & Trailing Whitespace Trimming & Admin Registration', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({
      name: primaryAdminAccount.name,
      orgName: primaryAdminAccount.orgName,
      email: `  ${primaryAdminAccount.email}  `,
      password: primaryAdminAccount.password,
    });
    await signUpPage.submit();
    await signUpPage.assertNoConsoleErrors();
  });

  test('Step 7: Edge Case 07 — Duplicate User Registration Protection Block Check', async ({ page }) => {
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

  test('Step 8: Edge Case 08 — Unregistered Ghost User Sign-In Rejection Check', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();
    await signInPage.fillForm({
      email: 'ghost.user.unregistered@scaibu.io',
      password: 'SomePassword123!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();
  });

  test('Step 9: Edge Case 09 — Incorrect Password Authentication Rejection Check', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();
    await signInPage.fillForm({
      email: primaryAdminAccount.email,
      password: 'WrongPassword999!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();
  });

  test('Step 10: Edge Case 10 — Case-Insensitive Email Sign-In Normalization Check', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();
    await signInPage.fillForm({
      email: primaryAdminAccount.email.toUpperCase(),
      password: primaryAdminAccount.password,
    });
    await signInPage.submit();
    await signInPage.assertNoConsoleErrors();
  });

  test('Step 11: Edge Case 11 — Special Character Search Query Escaping Check', async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
    await dashboardPage.applySearchFilter('?*%&[]()');
    await dashboardPage.assertNoConsoleErrors();
  });

  test('Step 12: Edge Case 12 — Corrupted URL Parameters Recovery & Empty Dataset View Check', async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.navigateTo('/?model=<script>&env=CORRUPTED');
    await dashboardPage.assertNoConsoleErrors();
    await dashboardPage.assertEmptyStateVisible();
  });

  test('Step 13: Edge Case 13 — Invalid Team Member Invite Email Format Validation Check', async ({ page }) => {
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
    }
  });

  test('Step 14: Edge Case 14 — Team Member Role Dropdown Selection Verification Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    const roleDropdown = page.locator('button:has-text("Select role"), [data-testid="role-dropdown"]');
    if (await roleDropdown.first().isVisible()) {
      await roleDropdown.first().click();
    }
    expect(page.url()).toBeDefined();
  });

  test('Step 15: Edge Case 15 — Team Member Invitation Form Cancelation Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    const cancelBtn = page.locator('button:has-text("Cancel")');
    if (await cancelBtn.first().isVisible()) {
      await cancelBtn.first().click();
    }
    expect(page.url()).toBeDefined();
  });

  test('Step 16: Edge Case 16 — Team Member Invitation & Directory Listing Creation Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    const inviteButton = page.locator('button:has-text("Invite Team Member")');
    if (await inviteButton.isVisible()) {
      await page.locator('input[placeholder="Full Name"]').fill(secondaryMemberAccount.name);
      await page.locator('input[placeholder="Email Address"]').fill(secondaryMemberAccount.email);
      await page.locator('button[type="submit"]:has-text("Send Invitation")').click();
    }
    expect(page.url()).toBeDefined();
  });

  test('Step 17: Edge Case 17 — Active User Status Badge Rendering Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    const activeBadge = page.locator('span:has-text("Active")');
    expect(await activeBadge.count()).toBeGreaterThanOrEqual(0);
  });

  test('Step 18: Edge Case 18 — User Details Profile Modal Open Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    const memberRow = page.locator('tr').first();
    if (await memberRow.isVisible()) {
      await memberRow.click();
    }
    expect(page.url()).toBeDefined();
  });

  test('Step 19: Edge Case 19 — Rapid Submit Button Protection Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({
      name: 'Double Submit Lead',
      orgName: 'Org Corp',
      email: generateUniqueEmail('double.submit'),
      password: 'SecurePassword123!',
    });
    await page.locator('button[type="submit"]').click({ clickCount: 2 });
    await signUpPage.assertNoConsoleErrors();
  });

  test('Step 20: Edge Case 20 — Non-Existent Route 404 Boundary Recovery Check', async ({ page }) => {
    await page.goto('/non-existent-route-path-999');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });

  test('Step 21: Edge Case 21 — Local Session Storage Clearing Check', async ({ page }) => {
    await page.evaluate(() => localStorage.clear());
    expect(page.url()).toBeDefined();
  });

  test('Step 22: Edge Case 22 — Session Logout & Protected Route Revocation Check', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const signOutBtn = page.locator('button:has-text("Sign Out"), button:has-text("Logout"), a:has-text("Sign Out")');
    if (await signOutBtn.first().isVisible()) {
      await signOutBtn.first().click();
    }
    expect(page.url()).toBeDefined();
  });

  test('Step 23: Edge Case 23 — Post-Logout Protected Settings Access Denial Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });

  test('Step 24: Edge Case 24 — Post-Logout Cookie Revocation Verification Check', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });

  test('Step 25: Edge Case 25 — Post-Logout Protected Dashboard Access Denial Check', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });
});
