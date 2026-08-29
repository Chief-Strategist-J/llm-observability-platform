# Automation Sequential Journeys & Production Edge-Cases Registry

> Single source of truth for End-to-End Sequential User Journeys and 20 Critical Production Edge Cases across microservices, authentication, and workspace telemetry.

## End-to-End (E2E) Sequential Journeys & Critical Edge Cases Registry

| Test Suite / Journey | Target Domain & Microservices | Tag | Status | Spec File Path | Last Updated |
|---|---|---|---|---|---|
| Master Suite — 20 Production Critical Edge Cases | Auth, Security Input Sanitization, IDOR Boundaries, URL Recovery, Team Invites | `@e2e @edgecases @critical` | Covered | `tests/automation/e2e/production-critical-edge-cases.journey.spec.ts` | 2026-08-29 |
| Production Sequential User Journey | Registration Service, Auth Guard, Dashboard Telemetry, Org Team Settings | `@e2e @sequential-journey @critical` | Covered | `tests/automation/e2e/sequential-user-flow.journey.spec.ts` | 2026-08-29 |
| New User Onboarding Cross-Service Flow | Sign-Up API, Auth Token Issuance, Database Verification | `@e2e @onboarding-journey @critical` | Covered | `tests/automation/e2e/new-user-onboarding.journey.spec.ts` | 2026-08-29 |
