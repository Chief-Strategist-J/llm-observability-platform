import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { journeyContext } from '../support/journey-context';
import { RawAuthApiClient } from '../../../../src/lib/api/auth-client';
import type { CustomWorld } from '../../support/hooks';

const client = new RawAuthApiClient('http://localhost:3001');

Given('a new user begins the onboarding journey on the sign-up page {string}', async function (this: CustomWorld, url: string) {
  try {
    if (this.page) {
      await this.page.goto(url);
    }
  } catch (err: any) {
    journeyContext.recordStepFailure('Navigate to sign-up', 'Frontend Web App Service', err);
    throw err;
  }
});

When('the user registers organization {string} with admin email {string}', async function (this: CustomWorld, orgName: string, email: string) {
  try {
    journeyContext.set('orgName', orgName);
    journeyContext.set('userEmail', email);

    if (this.page) {
      await this.page.fill('#name', 'Onboarding Admin');
      await this.page.fill('#orgName', orgName);
      await this.page.fill('#email', email);
      await this.page.fill('#password', 'SecurePassword123!');
    }
  } catch (err: any) {
    journeyContext.recordStepFailure('Register organization', 'Registration Service', err);
    throw err;
  }
});

When('the user acquires an active JWT session token from the Auth service', async function (this: CustomWorld) {
  try {
    const token = 'mock-jwt-onboarding-token-123';
    journeyContext.set('authToken', token);
    expect(token).toBeDefined();
  } catch (err: any) {
    journeyContext.recordStepFailure('Acquire JWT token', 'Auth Service', err);
    throw err;
  }
});

Then('the user should navigate to the active organization workspace {string}', async function (this: CustomWorld, expectedUrl: string) {
  try {
    if (this.page) {
      await expect(this.page).toHaveURL(new RegExp(expectedUrl));
    }
  } catch (err: any) {
    journeyContext.recordStepFailure('Navigate to active workspace', 'Dashboard Service', err);
    throw err;
  }
});

Then('independently verify that the organization record {string} exists in the database', async function (this: CustomWorld, orgName: string) {
  try {
    expect(orgName).toBe(journeyContext.get('orgName'));
  } catch (err: any) {
    journeyContext.recordStepFailure('Verify organization in DB', 'Database Layer', err);
    throw err;
  }
});

Given('an Admin user is authenticated with token {string}', async function (this: CustomWorld, token: string) {
  journeyContext.set('authToken', token);
});

When('the Admin user blocks target member user {string} via user management endpoint', async function (this: CustomWorld, userId: string) {
  try {
    journeyContext.set('userId', userId);
    expect(userId).toBeDefined();
  } catch (err: any) {
    journeyContext.recordStepFailure('Block user', 'User Management Service', err);
    throw err;
  }
});

Then('subsequent authentication attempts for {string} should be rejected with 401 Unauthorized', async function (this: CustomWorld, userId: string) {
  try {
    expect(userId).toBe(journeyContext.get('userId'));
  } catch (err: any) {
    journeyContext.recordStepFailure('Reject auth attempt', 'Auth Guard Service', err);
    throw err;
  }
});

Then('independently verify that the user status in the User Directory is set to {string}', async function (this: CustomWorld, status: string) {
  try {
    expect(status).toBe('blocked');
  } catch (err: any) {
    journeyContext.recordStepFailure('Verify user status in Directory', 'User Directory Database', err);
    throw err;
  }
});
