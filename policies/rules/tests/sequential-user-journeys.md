# Sequential Production User Journeys — Execution & Structure Policy

## 1. Purpose

Sequential test journeys verify real-world, multi-step production user lifecycles in exact linear order. Unlike isolated feature-level tests (Categories A–K), sequential journeys prove that state carries forward correctly across user registration, security error handling, authentication, dashboard telemetry, and team member management.

---

## 2. Directory Placement & Naming Conventions

- **Spec Runner Location**: `tests/automation/e2e/<journey-name>.journey.spec.ts`
- **Gherkin Feature Location**: `tests/automation/e2e/journeys/<journey-name>.feature`
- **Step Definitions Location**: `tests/automation/e2e/step-definitions/journeys.steps.ts`
- **Journey Context State Location**: `tests/automation/e2e/support/journey-context.ts`

---

## 3. Strict Linear Execution Rules

1. **Serial Execution Directive**:
   - Every sequential test spec file MUST use `test.describe.serial()` to guarantee steps execute strictly 1-by-1 in linear sequence.
   - If Step $N$ fails, subsequent dependent steps in the lifecycle are safely skipped rather than producing misleading false failures.

2. **Single Worker Constraint**:
   - Sequential journeys MUST be executed with `--workers=1` to prevent parallel thread shuffling.

3. **Deterministic Data Generation**:
   - Use `generateUniqueEmail('prefix')` from `fixtures/generators/unique-email.ts` to ensure collision-free email addresses per execution run.

---

## 4. Standard Production Lifecycle Phases (Mandatory Sequence)

Every primary user journey MUST cover the following 5 production lifecycle phases in order:

```
Phase 1: Registration Phase
  ├── 1.1 Input Edge Cases (Invalid Email Format, Short Password Meter)
  └── 1.2 Admin Account & Organization Creation

Phase 2: Duplicate Registration Protection Phase
  └── 2.1 Re-attempt registering the EXACT SAME email -> verify error alert & blocking

Phase 3: Authentication & Security Guard Phase
  ├── 3.1 Incorrect Password Attempt -> verify rejection
  └── 3.2 Valid Authentication -> authenticate registered credentials

Phase 4: Workspace Dashboard Phase
  ├── 4.1 Telemetry Search & Filter Query Pipeline
  └── 4.2 Empty / Active Dataset View Verification

Phase 5: Team Member Management Phase
  ├── 5.1 Navigate to Organization Team Settings (/settings/org)
  ├── 5.2 Invite / Add Secondary Team Member User
  └── 5.3 Verify Secondary Member Listing in Organization Directory
```

---

## 5. Page Objects Layer Abstraction

- **Zero Inline Selectors**: No DOM locators or CSS/XPath strings may appear directly inside a spec file or step definition.
- **Page Object Delegation**: All UI interactions MUST delegate through Page Objects (`SignUpPage`, `SignInPage`, `DashboardPage`, `BasePage`).
- **Transition Checkpoints**: Every step transition MUST verify visibility of target elements or page URLs before performing subsequent actions.

---

## 6. Execution Commands

- **Visual Chrome Mode (Headed Desktop GUI)**:
  ```bash
  npm --prefix packages/node/web-app run test:e2e:sequential
  ```

- **Headless Mode (CI Pipeline)**:
  ```bash
  npx playwright test tests/automation/e2e/sequential-user-flow.journey.spec.ts --workers=1 --project=chromium
  ```

---

## 7. Registry & Governance Rules

- Every sequential journey MUST be registered in `tests/automation/FEATURE_REGISTRY.md` under the **End-to-End (E2E) Cross-Service Journeys Registry** table.
