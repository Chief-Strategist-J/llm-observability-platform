# Automation Sequential Journeys Registry

> Single source of truth for End-to-End Sequential User Journeys incorporating 20 Critical Production Edge Cases across microservices, authentication, and workspace telemetry.

## End-to-End (E2E) Sequential Journeys Registry

| Test Suite / Journey | Target Domain & Microservices | Tag | Status | Spec File Path | Last Updated |
|---|---|---|---|---|---|
| Production Sequential User Journey (20 Critical Edge Cases Pipeline) | Registration, Security Input Sanitization, Auth Guards, Workspace Telemetry, Team Settings | `@e2e @sequential-journey @critical` | Covered | `tests/automation/e2e/sequential-user-flow.journey.spec.ts` | 2026-08-29 |
| New User Onboarding Cross-Service Flow | Sign-Up API, Auth Token Issuance, Database Verification | `@e2e @onboarding-journey @critical` | Covered | `tests/automation/e2e/new-user-onboarding.journey.spec.ts` | 2026-08-29 |
