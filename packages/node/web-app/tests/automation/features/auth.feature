Feature: Authentication & Organization Management BDD Automation
  As an Enterprise User of the LLM Observability Platform
  I want to securely register, sign in, and manage organization team members
  So that our team can track AI costs, latency, and quality SLOs securely

  @smoke @auth @registration @allure
  Scenario: User successfully signs up and registers a new organization
    Given the user navigates to the sign-up page "http://localhost:31400/auth/sign-up"
    When the user enters full name "Jaydeep", email "jaydeep@scaibu.io", organization "Scaibu", and password "SecurePassword123!"
    And the user clicks the "Register Organization" button
    Then the user should see the active organization workspace dashboard "http://localhost:31400"

  @auth @registration @edgecase @allure
  Scenario: Registration fails with weak password edgecase
    Given the user navigates to the sign-up page "http://localhost:31400/auth/sign-up"
    When the user enters password "123"
    Then the password meter should display weak strength indicator

  @auth @registration @edgecase @duplicate @allure
  Scenario: Registration fails for duplicate existing user email
    Given the user navigates to the sign-up page "http://localhost:31400/auth/sign-up"
    When the user attempts registration with existing email "existing.user@scaibu.io"
    Then an error message or validation alert should block submission

  @auth @registration @edgecase @invalid-email @allure
  Scenario: Registration triggers HTML5 validation for invalid email format
    Given the user navigates to the sign-up page "http://localhost:31400/auth/sign-up"
    When the user enters invalid email "invalid-email-no-at-sign"
    And the user clicks the "Register Organization" button
    Then the email input field should remain invalid

  @auth @login @allure
  Scenario: User signs in with valid credentials
    Given the user navigates to the sign-in page "http://localhost:31400/auth/sign-in"
    When the user enters email "admin@scaibu.io" and password "SecurePassword123!"
    And the user clicks the "Sign In" button
    Then the user should be redirected to the dashboard

  @auth @login @edgecase @allure
  Scenario: User login fails on wrong password
    Given the user navigates to the sign-in page "http://localhost:31400/auth/sign-in"
    When the user enters email "admin@scaibu.io" and password "WrongPassword999"
    And the user clicks the "Sign In" button
    Then the user should remain on the sign-in page

  @auth @login @edgecase @blocked @allure
  Scenario: Suspended or blocked user login is rejected
    Given the user navigates to the sign-in page "http://localhost:31400/auth/sign-in"
    When the user enters email "blocked.user@scaibu.io" and password "SecurePassword123!"
    And the user clicks the "Sign In" button
    Then the user should remain on the sign-in page

  @auth @rbac @allure
  Scenario: Admin user manages team member RBAC permissions
    Given an authenticated Admin user is on the organization settings page "http://localhost:31400/settings/org"
    When the Admin user clicks "Invite Team Member"
    And enters invitee name "Sarah Engineer", email "sarah@scaibu.io", and role "Member"
    And clicks "Send Invitation"
    Then "Sarah Engineer" should appear in the Active Organization Members list with role "Member"
