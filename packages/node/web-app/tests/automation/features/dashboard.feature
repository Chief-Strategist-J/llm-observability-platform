Feature: Observability Dashboard Filtering & Performance Telemetry
  As an Engineer monitoring LLM deployments
  I want to filter telemetry spans by model, environment, and date range
  So that I can analyze p95 latency, quality scores, and micro-USD cost metrics

  @smoke @dashboard @allure
  Scenario: Filter telemetry metrics by model and environment
    Given the user is on the main observability dashboard "http://localhost:31400"
    When the user selects model "gpt-4o" from the filter bar
    And selects environment "production"
    Then the telemetry spans table should only display spans matching model "gpt-4o" and environment "production"
    And the metric summary cards should recalculate P95 latency and total cost USD micro

  @dashboard @allure
  Scenario: Reset filters to default state
    Given the user has applied model filter "claude-3-opus"
    When the user clicks the "Reset Filters" button
    Then the filter state should restore default timeRange "24h" and environment "all"
