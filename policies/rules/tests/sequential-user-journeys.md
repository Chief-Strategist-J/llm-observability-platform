# Master Policy — Sequential Production User Journeys & End-to-End Execution Rules

## Table of Contents
1. [Purpose & Core Philosophy](#1-purpose--core-philosophy)
2. [Directory Architecture & File Naming Rules](#2-directory-architecture--file-naming-rules)
3. [Strict Sequential Execution Controls](#3-strict-sequential-execution-controls)
4. [Master Production Lifecycle Phase Matrix](#4-master-production-lifecycle-phase-matrix)
5. [Anti-Patterns & Automatic Rejection Rules](#5-anti-patterns--automatic-rejection-rules)
6. [Page Objects & Component Abstraction Rules](#6-page-objects--component-abstraction-rules)
7. [State Preservation & Diagnostic Logging](#7-state-preservation--diagnostic-logging)
8. [Generic Code Template for Sequential Journeys](#8-generic-code-template-for-sequential-journeys)
9. [CLI Command Registry & Package Scripts](#9-cli-command-registry--package-scripts)

---

## 1. Purpose & Core Philosophy

Isolated unit and feature-level tests (Categories A–K) verify individual endpoints in isolation. They **do not prove** that a real enterprise user can register, encounter validation guards, authenticate, view workspace telemetry, and invite team members in sequence.

A **Sequential User Journey** tests the cumulative, end-to-end lifecycle of a production user across multiple services, routes, and state transitions.

---

## 2. Directory Architecture & File Naming Rules

All sequential user journeys MUST be placed strictly inside `tests/automation/e2e/`. No journey spec file may exist in root folders or feature subdirectories.

```
packages/node/web-app/tests/automation/e2e/
├── journeys/                               # Gherkin BDD Feature Scenarios
│   ├── sequential-user-flow.feature
│   └── admin-user-suspension-flow.feature
├── step-definitions/                       # BDD Step Definitions
│   └── journeys.steps.ts
├── support/                                # State & Diagnostics Helpers
│   └── journey-context.ts
└── <journey-name>.journey.spec.ts          # Playwright Serial Runner Spec
```

### Naming Conventions:
- Spec Runner File: `<journey-name>.journey.spec.ts` (e.g., `sequential-user-flow.journey.spec.ts`)
- Gherkin Feature: `<journey-name>.feature`
- Tagging Mandatory: Every sequential journey MUST be tagged `@e2e @sequential-journey @critical`.

---

## 3. Strict Sequential Execution Controls

To prevent race conditions, test shuffling, or cross-thread data pollution, all sequential journeys MUST adhere to these strict rules:

1. **Serial Execution (`test.describe.serial`)**:
   - Every sequential journey file MUST be wrapped inside `test.describe.serial()`.
   - If Step $N$ fails, subsequent dependent steps in the lifecycle are immediately halted with `did not run` status, preventing cascade noise.

2. **Single Worker Limit (`workers: 1`)**:
   - Sequential journeys MUST be executed with `--workers=1` to guarantee single-threaded execution.

3. **Collision-Free Deterministic Data**:
   - All email addresses and organization names generated during a journey MUST use `generateUniqueEmail('prefix')` from `fixtures/generators/unique-email.ts`.

4. **Independent Failure Assertion**:
   - Every phase in the journey MUST independently verify both the UI state and the backend server state before advancing to the next phase.

---

## 4. Master Production Lifecycle Phase Matrix

Every complete enterprise user journey MUST execute through the following 6 sequential phases:

```
Phase 1: Initial Registration & Input Validation
  ├── 1.1 HTML5 Email Format Validation Check ("invalid-email-format")
  ├── 1.2 Weak Password Meter Warning Check ("123")
  └── 1.3 Valid Admin Account & Workspace Organization Registration

Phase 2: Duplicate Registration Protection
  └── 2.1 Re-attempt registering the EXACT SAME email -> verify error alert & creation block

Phase 3: Authentication & Security Guards
  ├── 3.1 Invalid Password Sign-In Attempt -> verify error rejection
  └── 3.2 Valid Authentication -> authenticate registered credentials

Phase 4: Workspace Dashboard & Telemetry Pipeline
  ├── 4.1 Workspace Navigation & Route Access Verification
  ├── 4.2 Telemetry Search Filter Query Pipeline Execution
  └── 4.3 Active Data Table / Empty Dataset View Check

Phase 5: Team Member Management & RBAC Invites
  ├── 5.1 Navigate to Organization Settings (/settings/org)
  ├── 5.2 Invite Secondary Team Member User ("prod.member@scaibu.io")
  └── 5.3 Verify Secondary Member Listing in Organization Team Directory

Phase 6: Audit Logging & Clean Logout State
  └── 6.1 Verify Security Audit Log Trail & Clean Session Termination
```

---

## 5. Anti-Patterns & Automatic Rejection Rules

| Anti-Pattern | Why It Is Banned | Correct Requirement |
|---|---|---|
| Running sequential journeys with `--workers=2` or higher | Causes random step execution order and flaky failures | ALWAYS run sequential specs with `--workers=1` |
| Using fixed `page.waitForTimeout(5000)` sleeps | Causes slow, fragile runs and intermittent timing bugs | Use state-based waits (`waitForLoadState('networkidle')`, `expect(element).toBeVisible()`) |
| Inlining CSS/XPath selectors directly in spec files | Breaks all tests when a class or layout changes | ALL locators MUST live inside Page Objects (`SignUpPage`, `SignInPage`, `DashboardPage`) |
| Trusting a UI success toast without checking state | UI toasts can show success even when DB writes fail | Re-verify state via a second route or API check |
| Reusing hardcoded static emails (`admin@scaibu.io`) across runs | Causes duplicate user conflicts on re-runs | Generate collision-free emails via `generateUniqueEmail()` |

---

## 6. Page Objects & Component Abstraction Rules

No raw locator (e.g. `page.locator('#email')`, `page.fill()`) may appear directly inside a `.journey.spec.ts` or step definition file.

All interactions MUST delegate through Page Objects:
- **`BasePage`**: Shared navigation, transition checkpoints, and automatic console error assertions (`assertNoConsoleErrors`).
- **`SignUpPage`**: Registration form fields, submit actions, HTML5 validation, and error alert checks.
- **`SignInPage`**: Login form fields, password toggles, submit actions, and error alert checks.
- **`DashboardPage`**: Workspace search filters, active badges, and telemetry dataset table views.

---

## 7. State Preservation & Diagnostic Logging

When a multi-step journey fails, the harness MUST log the exact step and service where the failure occurred.

### `JourneyContext` (`tests/automation/e2e/support/journey-context.ts`)
- Carries active `userId`, `userEmail`, `orgId`, and `authToken` across journey steps.
- On step failure, invokes `recordStepFailure(stepName, serviceName, error)` to attach clear diagnostic logs:

```typescript
journeyContext.recordStepFailure(
  "Step 4: Dashboard Telemetry Filter",
  "Dashboard Web Service",
  error
);
```

---

## 8. Generic Code Template for Sequential Journeys

```typescript
import { test, expect } from '@playwright/test';
import { SignUpPage } from '../page-objects/auth/sign-up.page';
import { SignInPage } from '../page-objects/auth/sign-in.page';
import { DashboardPage } from '../page-objects/dashboard/dashboard.page';
import { generateUniqueEmail } from '../fixtures/generators/unique-email';

test.describe.serial('[Service Name] Sequential Production User Journey', () => {
  let signUpPage: SignUpPage;
  let signInPage: SignInPage;
  let dashboardPage: DashboardPage;

  const adminAccount = {
    name: 'Production Admin',
    orgName: 'Scaibu Production Org',
    email: generateUniqueEmail('prod.admin'),
    password: 'SecurePassword123!',
  };

  test('Step 1: Registration Phase', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm(adminAccount);
    await signUpPage.submit();
    await signUpPage.assertNoConsoleErrors();
  });

  test('Step 2: Duplicate Registration Protection Phase', async ({ page }) => {
    signUpPage = new SignUpPage(page);
    await signUpPage.goto();
    await signUpPage.fillForm(adminAccount);
    await signUpPage.submit();
    await signUpPage.assertErrorMessageVisible();
  });

  test('Step 3: Authentication & Security Guard Phase', async ({ page }) => {
    signInPage = new SignInPage(page);
    await signInPage.goto();
    await signInPage.fillForm(adminAccount);
    await signInPage.submit();
    await signInPage.assertNoConsoleErrors();
  });

  test('Step 4: Workspace Dashboard Phase', async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
    await dashboardPage.applySearchFilter('latency');
    await dashboardPage.assertEmptyStateVisible();
  });
});
```

---

## 9. CLI Command Registry & Package Scripts

The following scripts in `packages/node/web-app/package.json` control sequential journey execution:

| Command Script | Execution Target | Mode | Browser Engine |
|---|---|---|---|
| `npm run test:e2e:sequential` | Primary sequential user flow | Headed GUI | Google Chrome (`--project=chromium`) |
| `npm run test:e2e:sequential:all` | All `.journey.spec.ts` files in `e2e/` | Headed GUI | Google Chrome (`--project=chromium`) |
| `npm run test:e2e:sequential:headless` | All `.journey.spec.ts` files in `e2e/` | Headless (CI) | Google Chrome (`--project=chromium`) |

---

### Command Syntax Reference:

```bash
# Run Primary Sequential Journey in Visual Headed Chrome Mode
npm --prefix packages/node/web-app run test:e2e:sequential

# Run ALL E2E Sequential Journeys in Visual Headed Chrome Mode
npm --prefix packages/node/web-app run test:e2e:sequential:all

# Run ALL E2E Sequential Journeys in Headless CI Mode
npm --prefix packages/node/web-app run test:e2e:sequential:headless
```
