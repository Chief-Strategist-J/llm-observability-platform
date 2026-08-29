Feature: Authentication & Organization Management BDD Automation
  As an Enterprise User of the LLM Observability Platform
  I want to securely register, sign in, and manage organization team members
  So that our team can track AI costs, latency, and quality SLOs securely

  @smoke @auth @allure
  Scenario: User successfully signs up and registers a new organization
    Given the user navigates to the sign-up page "http://localhost:31400/auth/sign-up"
    When the user enters full name "Jaydeep", email "jaydeep@scaibu.io", organization "Scaibu", and password "SecurePassword123!"
    And the user clicks the "Create Organization & Register" button
    Then the user should see the active organization workspace dashboard "http://localhost:31400"
    And the user profile role should display "Owner"

  @auth @rbac @allure
  Scenario: Admin user manages team member RBAC permissions
    Given an authenticated Admin user is on the organization settings page "http://localhost:31400/settings/org"
    When the Admin user clicks "Invite Team Member"
    And enters invitee name "Sarah Engineer", email "sarah@scaibu.io", and role "Member"
    And clicks "Send Invitation"
    Then "Sarah Engineer" should appear in the Active Organization Members list with role "Member"
