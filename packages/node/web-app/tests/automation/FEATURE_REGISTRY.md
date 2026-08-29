# Automation Sequential Journeys & Feature Coverage Registry

> Single source of truth for End-to-End Sequential User Journeys across microservices, authentication, and workspace telemetry.

## End-to-End (E2E) Sequential Journeys Registry

| Journey | Microservices & Routes Involved | Tag | Status | Scenario File / Path | Last Updated |
|---|---|---|---|---|---|
| Production Sequential User Journey (Registration -> Duplicate Protection -> Sign-In -> Workspace -> Team Invite) | Registration Service, Auth Guard, Dashboard Telemetry, Org Team Settings | `@e2e @sequential-journey @critical` | Covered | `tests/automation/e2e/sequential-user-flow.journey.spec.ts` | 2026-08-29 |
| New User Onboarding Cross-Service Flow | Sign-Up API, Auth Token Issuance, Database Verification | `@e2e @onboarding-journey @critical` | Covered | `tests/automation/e2e/new-user-onboarding.journey.spec.ts` | 2026-08-29 |
| Admin User Suspension Flow | Admin API, User Management, Auth Guard Revocation | `@e2e @suspension-journey @critical` | Covered | `tests/automation/e2e/journeys/admin-user-suspension-flow.feature` | 2026-08-29 |
