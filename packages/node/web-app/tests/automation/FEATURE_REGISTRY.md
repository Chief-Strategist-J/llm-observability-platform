# Automation Feature & Edge-Case Coverage Registry

> Single source of truth for Category A–K test coverage across endpoints, features, and user journeys.

| Endpoint / Feature | Category | Tag | Status | Scenario File / Path | Last Updated |
|---|---|---|---|---|---|
| `/auth/sign-up` | A (Happy Path) | `@happy-path` | Covered | `tests/automation/auth/sign-up/sign-up-valid.spec.ts` | 2026-08-29 |
| `/auth/sign-up` | B (Duplicate User) | `@duplicate` | Covered | `tests/automation/auth/sign-up/sign-up-duplicate-user.spec.ts` | 2026-08-29 |
| `/auth/sign-up` | C (Invalid Email) | `@invalid-rejected` | Covered | `tests/automation/auth/sign-up/sign-up-invalid-email.spec.ts` | 2026-08-29 |
| `/auth/sign-up` | F (Weak Password) | `@contract-boundary` | Covered | `tests/automation/auth/sign-up/sign-up-weak-password.spec.ts` | 2026-08-29 |
| `/auth/sign-in` | A (Happy Path) | `@happy-path` | Covered | `tests/automation/auth/sign-in/sign-in-valid.spec.ts` | 2026-08-29 |
| `/auth/sign-in` | C (Invalid Password) | `@invalid-rejected` | Covered | `tests/automation/auth/sign-in/sign-in-invalid-pass.spec.ts` | 2026-08-29 |
| `/auth/sign-in` | G (Blocked User) | `@authz-boundary` | Covered | `tests/automation/auth/sign-in/sign-in-blocked-user.spec.ts` | 2026-08-29 |
| `/admin/*` | G (RBAC Route Guard) | `@authz-boundary` | Covered | `tests/automation/auth/rbac/route-access.spec.ts` | 2026-08-29 |
| `/` (Dashboard) | A (Filter Pipeline) | `@happy-path` | Covered | `tests/automation/dashboard/filters/filter-selection.spec.ts` | 2026-08-29 |
| `/` (Dashboard) | C (Corrupted Query Fallback) | `@invalid-rejected` | Covered | `tests/automation/dashboard/filters/filter-corrupted-url.spec.ts` | 2026-08-29 |
| `/` (Dashboard) | E (Empty State Result) | `@silent-failure-check` | Covered | `tests/automation/dashboard/telemetry/empty-state.spec.ts` | 2026-08-29 |
