Automation & Playwright BDD Tests — Execution Policy Rules

1. Directory Structure Rules:
   - All test suites must be separated by test type at the root of `tests/`: `tests/unit/`, `tests/integration/`, `tests/performance/`, and `tests/automation/`.
   - Feature-domain subdirectories must be maintained inside `tests/automation/` (`auth/sign-up/`, `auth/sign-in/`, `auth/rbac/`, `dashboard/filters/`, `dashboard/telemetry/`).
   - Every individual test spec file must be independently executable (e.g. `npx playwright test tests/automation/auth/sign-up/sign-up-duplicate-user.spec.ts`).

2. Browser Engine & Execution Rules:
   - All Playwright automation tests MUST default to Google Chrome / Chromium engine (`--project=chromium`).
   - For live visual demonstration / presentation mode, execute via headed Chrome (`npm --prefix packages/node/web-app run test:e2e:headed`).
   - For headless automated CI runs, execute via `npm --prefix packages/node/web-app run test:e2e`.

3. Artifact Capture Policy (Only on Failure):
   - `screenshot`: Must be configured to `'only-on-failure'`.
   - `video`: Must be configured to `'retain-on-failure'`.
   - `trace`: Must be configured to `'retain-on-failure'`.
   - Screenshots and traces are automatically attached to Allure and HTML reports upon assertion failure.

4. Behavior Driven Development (BDD) Rules:
   - Gherkin feature scenarios must live under `tests/automation/features/` with tags (`@registration`, `@login`, `@edgecase`, `@rbac`).
   - Step definitions must live under `tests/automation/step-definitions/`.
   - Cucumber Playwright hooks in `tests/automation/support/hooks.ts` must capture a full-page PNG screenshot automatically on scenario failure.

5. Critical Edge Cases Governance:
   - Every feature area must cover happy paths AND critical edge cases:
     - Auth Registration: duplicate existing user email, weak password meter/length constraints, malformed email format HTML5 validation.
     - Auth Sign-In: incorrect password rejection, suspended/blocked user login rejection.
     - RBAC: unauthorized route access prevention and redirection.
     - Dashboard Filters: malformed/corrupted URL query string graceful fallback without UI crash (`EC-FE2-03`).
