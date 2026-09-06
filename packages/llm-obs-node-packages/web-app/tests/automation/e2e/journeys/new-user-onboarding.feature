Feature: New User Onboarding Cross-Service Journey
  As a new enterprise user
  I want to register an organization, acquire an active session token, and configure organization team member permissions
  So that our team can track LLM costs and latency metrics immediately

  @e2e @onboarding-journey @critical @allure
  Scenario: End-to-end new user onboarding journey across Registration, Auth, and Org Dashboard services
    Given a new user begins the onboarding journey on the sign-up page "http://localhost:31400/auth/sign-up"
    When the user registers organization "Scaibu Systems" with admin email "onboarding@scaibu.io"
    And the user acquires an active JWT session token from the Auth service
    Then the user should navigate to the active organization workspace "http://localhost:31400"
    And independently verify that the organization record "Scaibu Systems" exists in the database
