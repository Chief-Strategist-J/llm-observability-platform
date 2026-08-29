# Automation Feature & Edge-Case Coverage Registry

> Single source of truth for Category A–K test coverage across endpoints, features, and user journeys.

## Feature-Level Coverage (Categories A–K)

| Endpoint / Feature | Category | Tag | Status | Scenario File / Path | Last Updated |
|---|---|---|---|---|---|
| `/auth/sign-up` | A (Happy Path) | `@happy-path` | Covered | `tests/automation/auth/sign-up/sign-up-valid.spec.ts` | 2026-08-29 |
| `/auth/sign-up` | B (Duplicate User) | `@duplicate` | Covered | `tests/automation/auth/sign-up/sign-up-duplicate-user.spec.ts` | 2026-08-29 |
| `/auth/sign-up` | C (Invalid Email) | `@invalid-rejected` | Covered | `tests/automation/auth/sign-up/sign-up-invalid-email.spec.ts` | 2026-08-29 |
| `/auth/sign-up` | F (Contract Boundary) | `@contract-boundary` | Covered | `tests/automation/auth/sign-up/sign-up-contract-boundary.spec.ts` | 2026-08-29 |
| `/auth/sign-up` | I (Concurrency) | `@concurrency` | Covered | `tests/automation/auth/sign-up/sign-up-concurrency.spec.ts` | 2026-08-29 |
| `/auth/sign-in` | A (Happy Path) | `@happy-path` | Covered | `tests/automation/auth/sign-in/sign-in-valid.spec.ts` | 2026-08-29 |
| `/auth/sign-in` | C (Invalid Password) | `@invalid-rejected` | Covered | `tests/automation/auth/sign-in/sign-in-invalid-pass.spec.ts` | 2026-08-29 |
| `/auth/sign-in` | G (Blocked User) | `@authz-boundary` | Covered | `tests/automation/auth/sign-in/sign-in-blocked-user.spec.ts` | 2026-08-29 |
| `/admin/*` | G (RBAC & IDOR Boundary) | `@authz-boundary` | Covered | `tests/automation/auth/rbac/authz-boundary-idor.spec.ts` | 2026-08-29 |
| HTTP Executor | H (Dependency Failure) | `@dependency-failure` | Covered | `tests/automation/api/dependency-failure.spec.ts` | 2026-08-29 |
| HTTP Executor | J (Resource Limits) | `@resource-limit` | Covered | `tests/automation/api/resource-limits.spec.ts` | 2026-08-29 |
| HTTP Executor | K (Observability Trace) | `@observability` | Covered | `tests/automation/api/observability-trace.spec.ts` | 2026-08-29 |
| `/` (Dashboard) | A (Filter Pipeline) | `@happy-path` | Covered | `tests/automation/dashboard/filters/filter-selection.spec.ts` | 2026-08-29 |
| `/` (Dashboard) | C (Corrupted Query Fallback) | `@invalid-rejected` | Covered | `tests/automation/dashboard/filters/filter-corrupted-url.spec.ts` | 2026-08-29 |
| `/` (Dashboard) | E (Empty State Result) | `@silent-failure-check` | Covered | `tests/automation/dashboard/telemetry/empty-state.spec.ts` | 2026-08-29 |

---

## End-to-End (E2E) Cross-Service Journeys Registry

| Journey | Services Involved | Tag | Status | Scenario File / Path | Last Updated |
|---|---|---|---|---|---|
| Registration -> Login -> Dashboard Sequential Flow | Registration Service, Auth Service, Org Dashboard | `@e2e @sequential-journey @critical` | Covered | `tests/automation/e2e/sequential-user-flow.journey.spec.ts` | 2026-08-29 |
| Admin User Suspension Flow | Admin API, User Management, Auth Guard | `@e2e @suspension-journey @critical` | Covered | `tests/automation/e2e/journeys/admin-user-suspension-flow.feature` | 2026-08-29 |
