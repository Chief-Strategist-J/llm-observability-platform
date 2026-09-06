import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import type { CustomWorld } from '../support/hooks';
import { SignUpPage } from '../page-objects/auth/sign-up.page';
import { SignInPage } from '../page-objects/auth/sign-in.page';
import { generateUniqueEmail } from '../fixtures/generators/unique-email';

let signUpPage: SignUpPage;
let signInPage: SignInPage;

Given('I am on the registration page', async function (this: CustomWorld) {
  if (this.page) {
    signUpPage = new SignUpPage(this.page);
    await signUpPage.goto();
  }
});

Given('I am on the sign-in page', async function (this: CustomWorld) {
  if (this.page) {
    signInPage = new SignInPage(this.page);
    await signInPage.goto();
  }
});

When('I fill in the registration form with valid unique details', async function (this: CustomWorld) {
  const uniqueEmail = generateUniqueEmail('signup');
  this.testData = { email: uniqueEmail };
  await signUpPage.fillForm({
    name: 'Automation Lead',
    orgName: 'Scaibu Enterprise',
    email: uniqueEmail,
    password: 'SecurePassword123!',
  });
});

When('I submit the registration form', async function () {
  await signUpPage.submit();
});

Then('I should see the registration success confirmation', async function (this: CustomWorld) {
  if (this.page) {
    await signUpPage.waitForPageTransition(/dashboard|auth/);
  }
});

Then('I should be able to sign in immediately using those credentials', async function (this: CustomWorld) {
  if (this.page && this.testData?.email) {
    signInPage = new SignInPage(this.page);
    await signInPage.goto();
    await signInPage.fillForm({
      email: this.testData.email,
      password: 'SecurePassword123!',
    });
    await signInPage.submit();
  }
});

When('I fill in registration form with a short password {string}', async function (this: CustomWorld, pass: string) {
  await signUpPage.fillForm({
    name: 'Weak Password User',
    orgName: 'Org Inc',
    email: generateUniqueEmail('weak'),
    password: pass,
  });
});

Then('I should see a weak password meter warning', async function () {
  await signUpPage.assertWeakPasswordWarningVisible();
});
