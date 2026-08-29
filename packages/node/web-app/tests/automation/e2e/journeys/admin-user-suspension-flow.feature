Feature: Admin User Suspension Cross-Service Journey
  As an Organization Owner
  I want to block a compromised team member account and verify immediate access revocation
  So that unauthorized access to LLM telemetry metrics is prevented instantly

  @e2e @suspension-journey @critical @allure
  Scenario: End-to-end admin user suspension journey across Admin User API, Block Endpoint, and Auth Guard
    Given an Admin user is authenticated with token "token-admin-owner"
    When the Admin user blocks target member user "usr_comp_99" via user management endpoint
    Then subsequent authentication attempts for "usr_comp_99" should be rejected with 401 Unauthorized
    And independently verify that the user status in the User Directory is set to "blocked"
