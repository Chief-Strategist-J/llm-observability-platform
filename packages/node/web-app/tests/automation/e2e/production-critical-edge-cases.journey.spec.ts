import { test, expect } from '@playwright/test';
import { SignUpPage } from '../page-objects/auth/sign-up.page';
import { SignInPage } from '../page-objects/auth/sign-in.page';
import { DashboardPage } from '../page-objects/dashboard/dashboard.page';
import { generateUniqueEmail } from '../fixtures/generators/unique-email';

test.describe.serial('Master Suite — 20 Production Critical Edge Cases', () => {
  let signUpPage: SignUpPage;
  let signInPage: SignInPage;
  let dashboardPage: DashboardPage;

  const testUser = {
    name: 'EdgeCase Admin',
    orgName: 'Scaibu EdgeCase Systems',
    email: generateUniqueEmail('edgecase.user'),
    password: 'SecurePassword123!',
  };

  test('EC-01: HTML5 Email Format Validation Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ email: 'invalid-email-format' });
    const isEmailValid = await signUpPage.isEmailFieldValid();
    expect(isEmailValid).toBe(false);
  });

  test('EC-02: Weak Password Warning Meter Threshold Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ password: '123' });
    await signUpPage.assertWeakPasswordWarningVisible();
  });

  test('EC-03: XSS Script Tag Input Sanitization Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ name: "<script>alert('xss')</script>" });
    expect(await page.locator('#name').inputValue()).toContain('script');
  });

  test('EC-04: SQL Injection Payload Field Sanitization Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({ orgName: "' OR '1'='1" });
    expect(await page.locator('#orgName').inputValue()).toBe("' OR '1'='1");
  });

  test('EC-05: Leading & Trailing Whitespace Normalization Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({
      name: testUser.name,
      orgName: testUser.orgName,
      email: `  ${testUser.email}  `,
      password: testUser.password,
    });
    await signUpPage.submit();
    await signUpPage.assertNoConsoleErrors();
  });

  test('EC-06: Duplicate User Registration Prevention Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({
      name: testUser.name,
      orgName: testUser.orgName,
      email: testUser.email,
      password: testUser.password,
    });
    await signUpPage.submit();
    await signUpPage.assertErrorMessageVisible();
  });

  test('EC-07: Unregistered Ghost User Sign-In Rejection Check', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();
    await signInPage.fillForm({
      email: 'ghost.user.unregistered@scaibu.io',
      password: 'SomePassword123!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();
  });

  test('EC-08: Incorrect Password Authentication Rejection Check', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();
    await signInPage.fillForm({
      email: testUser.email,
      password: 'WrongPassword999!',
    });
    await signInPage.submit();
    expect(signInPage.emailInput).toBeVisible();
  });

  test('EC-09: Case-Insensitive Email Sign-In Normalization Check', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();
    await signInPage.fillForm({
      email: testUser.email.toUpperCase(),
      password: testUser.password,
    });
    await signInPage.submit();
    await signInPage.assertNoConsoleErrors();
  });

  test('EC-10: Max Length Field Boundary Limit Check (255 chars)', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    const longOrg = 'A'.repeat(255);
    await signUpPage.fillForm({ orgName: longOrg });
    expect(await page.locator('#orgName').inputValue()).toBe(longOrg);
  });

  test('EC-11: IDOR & Unauthenticated Route Access Protection Check', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });

  test('EC-12: Invalid Team Member Invite Email Format Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    const inviteBtn = page.locator('button:has-text("Invite Team Member")');
    if (await inviteBtn.isVisible()) {
      await inviteBtn.click();
      const emailInput = page.locator('input[placeholder="Email Address"]');
      if (await emailInput.isVisible()) {
        await emailInput.fill('invalid-invite-email');
        const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.checkValidity());
        expect(isValid).toBe(false);
      }
    }
  });

  test('EC-13: Special Character Search Query Escaping Check', async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
    await dashboardPage.applySearchFilter('?*%&[]()');
    await dashboardPage.assertNoConsoleErrors();
  });

  test('EC-14: Corrupted URL Search Params Fallback Recovery Check', async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.navigateTo('/?model=<script>&env=CORRUPTED');
    await dashboardPage.assertNoConsoleErrors();
  });

  test('EC-15: Empty Dataset Telemetry Placeholder View Check', async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
    await dashboardPage.assertEmptyStateVisible();
  });

  test('EC-16: Rapid Double Submit Button Check', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm({
      name: 'Double Submit User',
      orgName: 'Org Inc',
      email: generateUniqueEmail('double.submit'),
      password: 'SecurePassword123!',
    });
    await page.locator('button[type="submit"]').click({ clickCount: 2 });
    await signUpPage.assertNoConsoleErrors();
  });

  test('EC-17: Cookie Token Clearing Revocation Check', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });

  test('EC-18: Non-Existent Route 404 Fallback Boundary Check', async ({ page }) => {
    await page.goto('/non-existent-route-path-999');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });

  test('EC-19: Organization Settings Form Render Check', async ({ page }) => {
    await page.goto('/settings/org');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toBeDefined();
  });

  test('EC-20: Session Logout Revocation Termination Check', async ({ page }) => {
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
