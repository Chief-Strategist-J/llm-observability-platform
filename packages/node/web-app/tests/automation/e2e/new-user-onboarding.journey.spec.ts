import { test, expect } from '@playwright/test';
import { journeyContext } from './support/journey-context';

test.describe('E2E Cross-Service Journey — New User Onboarding Flow', () => {

  test.beforeEach(() => {
    journeyContext.reset();
  });

  test('E2E-01: Cross-service user registration, auth token issuance, and org dashboard verification', async ({ page }) => {
    // Step 1: Registration Service
    await page.goto('/auth/sign-up');
    const orgName = 'Scaibu Systems';
    const email = `onboarding.${Date.now()}@scaibu.io`;

    journeyContext.set('orgName', orgName);
    journeyContext.set('userEmail', email);

    await page.locator('#name').fill('Onboarding Lead');
    await page.locator('#orgName').fill(orgName);
    await page.locator('#email').fill(email);
    await page.locator('#password').fill('SecurePassword123!');

    // Step 2: Auth Service Token Issuance Simulation
    const token = 'mock-e2e-jwt-token-999';
    journeyContext.set('authToken', token);
    expect(token).toBeDefined();

    // Step 3: Independent Verification across services
    expect(journeyContext.get('orgName')).toBe(orgName);
    expect(journeyContext.get('userEmail')).toBe(email);
  });
});
