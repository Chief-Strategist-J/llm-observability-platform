# Master Test Automation Policy — Playwright + Cucumber BDD + Allure (Consolidated)

## Table of Contents
1. Purpose
2. Toolchain & Configuration Rules
3. Full Automation Folder Structure (UI + Microservice, single unified tree)
4. Definition of Done for a Test
5. Anti-Patterns — Automatic Rejection List
6. The Complete Test Case Taxonomy (A–K)
7. End-to-End (E2E) Journey Testing
8. Worked Examples (concrete + generic placeholder template)
9. Additive/Scalable Growth Rules
10. Feature Registry Rules
11. LLM Test-Generation Instruction Block (code-reading, adversarial)
12. Dynamic UI & Multi-Step Flow Reliability Rules
13. Diagnostic Checklist ("it runs but doesn't complete properly")
14. Per-Feature Checklist (fill out before writing any test)
15. Definition of "Feature Fully Covered"

---

## 1. Purpose

A test that runs and passes without verifying real behavior is **not a test** — it's a false signal.
Every rule in this document exists to stop that specific failure mode: an AI-generated or hand-written
suite that "just runs" without actually catching regressions, missing dynamic-UI interactions, or
stopping short of a real end-to-end journey. This is the single source of truth — there is no other
version of these rules. Anything not in this document is not policy.

---

## 2. Toolchain & Configuration Rules

- **Playwright** is the execution engine. Chromium is the default and required browser
  (`--project=chromium`) for all automation runs.
- **Cucumber** is the BDD layer. All scenarios are written in Gherkin (`.feature` files) and backed by
  step definitions. No test logic may live only in a step definition without a corresponding Gherkin
  scenario describing intent in plain language.
- **Allure** is the reporting layer. Every run (Playwright-native or Cucumber) publishes to the same
  Allure results directory so one report shows the full suite. Every category tag (A–K, see Section 6)
  must map to an Allure label/severity so the report can be filtered by category, not just by domain.
- **Artifact capture — only on failure, always:**
  - `screenshot`: only-on-failure
  - `video`: retain-on-failure
  - `trace`: retain-on-failure
  - Screenshots/traces auto-attach to Allure and HTML reports on assertion failure.
- **Execution modes:**
  - Headed Chrome: for live visual demonstration/presentation only.
  - Headless: for all CI/automated runs.
  - CI must fail the build (non-zero exit) on any failed test — a pipeline that reports failures but
    still goes green is a policy violation.
- **Environment isolation:** each environment (dev/staging/CI) has its own config file holding base URL,
  dependency base URLs, and test-only credentials. No environment value may be hardcoded inside a test or
  step definition.
- **Mock/stub configuration:** downstream dependencies used for failure-injection testing (Category H)
  must be mockable via configuration (a toggle or base-URL override) — never by editing the service's own
  code. A mock must be scoped to a single scenario without affecting others running in parallel.
- **Auth fixture configuration:** tokens/credentials per role/tenant (needed for Category G) are
  generated or retrieved through config-driven, test-only setup — never long-lived real credentials
  committed to the repo.
- **Idempotency key configuration:** if the system supports idempotency keys, config defines how a fresh
  unique key is generated per run and how a duplicate key is deliberately reused for Category I.
- **Correlation/trace ID propagation:** config defines how a correlation ID is injected on outbound test
  requests and where the harness looks for it in responses/logs (needed for Category K).
- **CI defaults:** dependency-failure (H) and resource/rate-limit (J) scenarios run against the mock
  layer in CI by default — never against real downstream services or real rate limits.
- **Secrets handling:** any real secret needed for staging/CI (API keys, signing keys) is injected via
  the CI secret store — never present in any file under `tests/automation/`.
- **Reporting is git-ignored, always regenerated.** If report artifacts are being committed to the repo,
  that is itself a structural violation.

**Rule:** none of the above requires touching an existing feature's test files. Configuration changes are
made once, centrally, and every existing and future feature benefits automatically.

---

## 3. Full Automation Folder Structure (Unified)

```
tests/
├── unit/
├── integration/
├── performance/
└── automation/
    │
    ├── features/                          # Gherkin — WHAT is tested, plain English, one endpoint/feature per folder
    │   └── <domain>/                       # e.g. auth, dashboard
    │       └── <endpoint-name>/            # e.g. sign-up, filters
    │           ├── <endpoint>-happy-path.feature              # A
    │           ├── <endpoint>-duplicate.feature                # B
    │           ├── <endpoint>-invalid-input.feature             # C
    │           ├── <endpoint>-false-positive.feature            # D
    │           ├── <endpoint>-silent-failure.feature             # E
    │           ├── <endpoint>-contract-boundary.feature          # F
    │           ├── <endpoint>-authz-boundary.feature             # G
    │           ├── <endpoint>-dependency-failure.feature         # H
    │           ├── <endpoint>-concurrency.feature                # I
    │           ├── <endpoint>-resource-limits.feature            # J
    │           └── <endpoint>-observability.feature              # K
    │
    ├── e2e/                                # sibling to features/, cross-service journeys only
    │   ├── journeys/
    │   │   ├── new-user-onboarding.feature
    │   │   ├── purchase-checkout-flow.feature
    │   │   └── admin-user-suspension-flow.feature
    │   ├── step-definitions/
    │   │   └── journeys.steps.ts
    │   └── support/
    │       └── journey-context.ts          # carries real state between steps across services
    │
    ├── step-definitions/                   # Glue code — HOW each Gherkin line executes
    │   └── <domain>/
    │       └── <endpoint>.steps.ts         # backs ALL category files for this endpoint
    │
    ├── page-objects/                       # UI abstraction — selectors live ONLY here, never in steps
    │   ├── <domain>/
    │   │   └── <feature>.page.ts
    │   └── base.page.ts                    # shared navigation/wait helpers
    │
    ├── api-clients/                        # Direct backend calls — required for server-side validation
    │   └── <domain>/                       # checks (C), authz checks (G), and silent-failure verification (E, I)
    │       └── <endpoint>.api.ts
    │
    ├── mocks/                              # Required for Category H — dependency failure injection
    │   └── <dependency-name>/
    │       ├── timeout.mock.ts
    │       ├── error-5xx.mock.ts
    │       └── malformed-response.mock.ts
    │
    ├── fixtures/                           # Deterministic, disposable test data
    │   ├── users/
    │   │   ├── valid-user.json
    │   │   ├── suspended-user.json
    │   │   └── weak-password-cases.json
    │   ├── auth/                           # Required for Category G — per-role/tenant tokens
    │   │   ├── tenant-a-user-token.json
    │   │   ├── tenant-b-user-token.json
    │   │   ├── expired-token.json
    │   │   └── wrong-role-token.json
    │   ├── idempotency/                    # Required for Category I
    │   │   └── sample-idempotency-keys.json
    │   └── generators/
    │       └── unique-email.ts             # collision-free data per run
    │
    ├── support/                            # Cucumber/Playwright wiring — the "engine room"
    │   ├── world.ts                        # custom World: browser/context/page per scenario
    │   ├── hooks.ts                        # Before/After — failure-only artifact capture
    │   ├── environment.ts                  # env/base-URL/credentials resolution
    │   └── correlation-id.ts               # required for Category K
    │
    ├── utils/                              # Pure helper functions — no test logic
    │   ├── assertions.ts                   # custom assertions (e.g. assertNoConsoleErrors)
    │   └── wait-conditions.ts              # named, reusable wait conditions — never raw timeouts
    │
    ├── config/
    │   ├── playwright.config.ts
    │   ├── cucumber.js
    │   └── environments/
    │       ├── dev.env
    │       ├── staging.env
    │       └── ci.env
    │
    ├── reports/                            # generated, git-ignored
    │   ├── allure-results/
    │   ├── html-report/
    │   └── artifacts/
    │       ├── screenshots/
    │       ├── videos/
    │       └── traces/
    │
    └── FEATURE_REGISTRY.md                 # single coverage source of truth, append-only
```

### Why each layer exists

- **`features/` vs `step-definitions/`**: a non-technical reader can understand exactly what's covered
  from `features/` alone. If test logic only lives in step files with thin `.feature` files, this benefit
  is lost.
- **`page-objects/`**: the most commonly skipped layer in AI-generated suites. Without it, every step
  definition re-writes its own selectors, so one UI change breaks dozens of files instead of one.
  **Rule: no selector may appear directly inside a step definition file.**
- **`api-clients/`**: makes Category C (server-side validation), E (silent-failure verification), G
  (authz), and I (concurrency state checks) actually possible — without a way to hit the backend
  directly, you're stuck trusting the UI, which is the root of "it just runs, not testing properly."
- **`mocks/`**: required for Category H — you cannot test a dependency-timeout/failure path without a
  way to force that dependency to fail on command.
- **`fixtures/auth/`**: separate from `fixtures/users/` because authz-boundary testing (cross-tenant/role)
  needs its own token set, not user records.
- **`e2e/`**: kept as a sibling to `features/`, never mixed in — E2E state carries forward for real
  between steps, unlike isolated feature-level tests.
- **`reports/`**: always git-ignored, always regenerated. Committed report artifacts are a violation.

### Naming Conventions
- Feature files: `<feature>-<category>.feature` — the category must be visible in the filename.
- Step definitions: mirror the domain folder of the feature file exactly.
- Page objects: `<feature>.page.ts`, one per distinct screen/component (a multi-step wizard gets one per
  step if the DOM differs meaningfully).
- **Tags on every scenario (mandatory):** domain tag (`@auth`), sub-feature tag (`@sign-up`), category tag
  (`@happy-path`, etc. — see Section 6), and Allure severity (`@critical`, `@major`, `@minor`).

---

## 4. Definition of Done for a Test

A generated or written test is only acceptable if it satisfies **all** of the following:

### 4.1 It must fail when the feature is broken
Prove it: temporarily break the underlying behavior and confirm the test goes red. A test that stays
green regardless of what the app does is worthless. Non-negotiable for every critical test (Section 6).

### 4.2 It must assert outcomes, not just absence of errors
Banned as the *sole* assertion: "status is not 500," "page is truthy," waiting for navigation with no
follow-up check, checking an element merely *exists* when the test is about its content/state/behavior.
Required: assert the actual expected value/state.

### 4.3 It must assert both the positive and the negative
For every "X should happen," also check the implicit "and Y should NOT happen" where it matters.

### 4.4 No hard-coded sleeps / arbitrary waits
Fixed-duration waits are banned except as a documented last resort with a comment explaining why no
proper wait condition exists. Use state-based waits tied to visibility/enabled/URL/response conditions.

### 4.5 Selectors must be resilient and meaningful
Prefer role/label/test-id based selectors over brittle CSS/XPath tied to styling or DOM position.

### 4.6 Test data must be isolated and deterministic
No test may depend on data left over from another test, and none may leave data that breaks a later run.

### 4.7 One logical behavior per test
A failure must point unambiguously at *what* broke.

### 4.8 Every edge case gets its own explicit assertion of the failure mode
Not "page didn't crash" — the actual expected behavior (specific error text/status/fallback state).

---

## 5. Anti-Patterns — Automatic Rejection List

| Anti-pattern | Why it's banned |
|---|---|
| Tautological assertion (always-true check) | Verifies nothing |
| Test with zero assertions | Not a test, a script |
| Only checking URL changed, not resulting page state | Navigation ≠ correctness |
| Swallowing exceptions to force a pass | Hides real failures |
| Commented-out assertions ("will fix later") | Ships fake coverage |
| Testing the mock instead of the real integration point | Verifies your mock, not your app |
| Screenshot-only "visual check" with no assertion behind it | Not a pass/fail signal |
| Retrying a flaky assertion until it passes instead of fixing the wait | Masks real timing bugs |
| Click → immediately act on the result with no state check in between | Root cause of "runs fast, doesn't complete" |
| Reusing a locator captured before a page/step transition | Stale reference; silently targets the wrong/no element |
| Assuming prior form data persists after navigating back | False assumption about app state |

---

## 6. The Complete Test Case Taxonomy (A–K)

For **any** feature/endpoint involving a user or caller triggering an action, all applicable categories
below must exist as **separate, tagged scenarios** — never merged. A failure in one scenario must point
unambiguously at one behavior.

| # | Category | Tag | Severity | Proves |
|---|---|---|---|---|
| A | Happy path | `@happy-path` | `@critical` | Valid input produces the real, independently-verified outcome |
| B | Duplicate/repeat submission | `@duplicate` | `@critical` | Re-submitting identical valid data is rejected, no second effect occurs |
| C | Invalid input rejected | `@invalid-rejected` | `@major` | Constraint violations blocked client- AND server-side |
| D | False-positive success | `@false-positive-check` | `@critical` | Invalid input can never look like success (wrong redirect, false success toast) |
| E | Silent failure on valid input | `@silent-failure-check` | `@critical` | A "success" UI is independently re-verified against real system state |
| F | Contract/schema boundary | `@contract-boundary` | `@major` | Every field constraint from the schema/DTO is individually tested at its boundary |
| G | AuthN/AuthZ boundary | `@authz-boundary` | `@critical` | Missing/expired auth, wrong role, and cross-tenant (IDOR) access are all denied |
| H | Downstream dependency failure | `@dependency-failure` | `@critical` | Timeout/5xx/malformed response from a dependency is handled without corrupting state |
| I | Concurrency/idempotency | `@concurrency` | `@major` | Concurrent identical requests don't double-apply the effect |
| J | Resource/payload limits | `@resource-limit` | `@minor`/`@major` | Size/rate/pagination limits are enforced and recover correctly |
| K | Observability under failure | `@observability` | `@minor` | Correlation IDs propagate and failures are logged, not silent |

### Category detail

**A — Happy Path.** Submit fully valid input for the first time. Verify the actual downstream effect
(record exists, session is real, filter is truly applied) — not just a success message.

**B — Repeat Submission.** Submit the exact same valid input a second time. Must be rejected with the
specific expected error. Confirm no second effect occurred (re-check state, don't just check for the
error text).

**C — Invalid/Weak Input Rejected.** Derive from actual constraints (length, format, strength, required
fields). One scenario per constraint, not one generic "invalid input" scenario. If validation exists
client-side, the same input must also be sent by bypassing the client (direct API call) to confirm the
server independently enforces the rule.

**D — False-Positive Success.** Submit invalid/malformed input and assert the system does **not** behave
as if it succeeded (no redirect to a success screen, no success toast, no state change). If this scenario
ever fails, capture screenshot + video + trace automatically — visual proof is mandatory here.

**E — Silent Failure.** Submit fully valid input, see a "success" indicator, then independently re-verify
through a *second, unrelated path* (e.g. attempt login right after "successful" registration; re-query
data after a "successful" filter) — never trust the success message alone. This is the category most
often missing, and it's precisely the failure mode of "it just runs, not testing properly."

**F — Contract/Schema Boundary.** Derive from the request/response schema. Generate a scenario per
constraint found in code: exactly-at-max-length, one-over-max, wrong type, out-of-enum value, required
field genuinely absent, unexpected extra field. Assert the exact documented error shape.

**G — AuthN/AuthZ Boundary.** No token → 401, no leaked data. Expired token → rejected, not silently
valid. Valid token, wrong role/scope → 403. Valid token for a different tenant/user accessing this
tenant's resource (IDOR) → explicitly denied. Assert status code AND that no unauthorized data appears
anywhere in the response, headers, or accessible logs.

**H — Downstream Dependency Failure.** For every outbound call the endpoint makes, simulate timeout,
5xx, and malformed response via mocks. Assert the code's actual expected behavior (circuit breaker,
bounded retry, specific fallback) and that no partial/inconsistent state is left behind. If the code has
no handling for a path at all, generate the test asserting the CURRENT (likely broken) behavior, tag it
`@known-gap`, and state what correct behavior should be — do not silently skip broken paths.

**I — Concurrency/Idempotency.** Fire two identical requests concurrently; assert the system's documented
guarantee (exactly-once vs idempotent-same-result) via final system state, not just both HTTP responses.
Reused idempotency keys must return the original result, not create a second effect.

**J — Resource/Payload Limits.** Payload at exactly the limit / one over. Pagination past the last page →
graceful empty result. Rate limit exceeded → correct 429 with retry-after semantics, and confirm the
limit resets correctly afterward.

**K — Observability Under Failure.** A correlation/trace ID passed on request appears in the error
response and/or propagates downstream. A failure path logs at correct severity. If not verifiable in the
current harness, mark `@not-yet-testable` rather than skipping unmarked.

---

## 7. End-to-End (E2E) Journey Testing

Categories A–K are **feature-level** — one endpoint, isolated. None of them prove a real user/business
journey works *across* features and services. E2E is a separate layer on top, not a replacement.

**A scenario belongs in `e2e/journeys/`, not `features/`, when it satisfies all of:**
1. It crosses more than one microservice/endpoint in sequence.
2. It represents something a real user or business process actually does end to end (not an artificial
   combination invented for test convenience).
3. Its pass/fail meaning is "the whole journey works" — catching integration gaps that per-endpoint tests
   structurally cannot see (e.g. Service A's success writes data in a shape Service B doesn't expect).

**Rules specific to E2E:**
- Tag `@e2e` + journey-name tag + severity (usually `@critical` for core paths).
- **Fewer, not more.** Cover only the handful of journeys representing real business value or the
  highest-risk cross-service handoffs — do not generate one for every possible path.
- **Real state carries forward within one scenario** (the actual account just created, the actual token
  just issued) — unlike isolated feature-level tests, this is intentional.
- **Independent verification still applies, across services**: at the end of the journey, verify the
  final state through a path different from the one the journey used (e.g. after checkout, independently
  query the order service AND the inventory service, not just the UI's confirmation screen).
- **Run on a separate, slower CI cadence** (pre-merge to main, nightly, pre-release) against a real
  integrated environment — feature-level (A–K) runs on every commit against mocked dependencies.
- **Failure diagnosis must identify which service in the chain failed** — tag/log which step and which
  underlying service call broke, not just "the journey failed at step 4."

**Registry addition for E2E** (separate table in `FEATURE_REGISTRY.md`, since journeys aren't per-endpoint):

| Journey | Services involved | Tag | Status | Scenario file | Last updated |
|---|---|---|---|---|---|

---

## 8. Worked Examples

### 8.1 Concrete Example — Registration (all 5 core categories)

```gherkin
Feature: User Registration

  Background:
    Given I am on the registration page

  @auth @sign-up @happy-path @critical
  Scenario: Registering with valid, unique details succeeds
    When I fill in the registration form with a valid, unique email and a strong password
    And I submit the registration form
    Then I should see the registration success confirmation
    And I should be able to sign in immediately using the same credentials
    # sign-in re-check proves the account was REALLY created, not a fake success message

  @auth @sign-up @duplicate @critical
  Scenario: Registering twice with the same email is rejected
    Given a user has already registered successfully with a known email
    When I fill in the registration form using that same email and a valid password
    And I submit the registration form
    Then I should see a "this email is already registered" error
    And no second account should exist for that email

  @auth @sign-up @invalid-rejected @major
  Scenario Outline: Registration is blocked for constraint-violating input
    When I fill in the registration form with "<field>" set to "<invalid_value>"
    And I submit the registration form
    Then the registration should be rejected with a "<expected_error>" message
    And the same request sent directly to the registration API should also be rejected
    Examples:
      | field    | invalid_value | expected_error             |
      | password | 123           | password too short         |
      | email    | not-an-email  | invalid email format       |
      | email    | (empty)       | email is required          |

  @auth @sign-up @false-positive-check @critical
  Scenario: An invalid email must never be treated as a successful registration
    When I fill in the registration form with an invalid, malformed email
    And I submit the registration form
    Then I should NOT be redirected to the logged-in dashboard
    And I should NOT see any success confirmation
    And no account should exist for that malformed email

  @auth @sign-up @silent-failure-check @critical
  Scenario: A "successful" registration must correspond to a real account
    When I fill in the registration form with a valid, unique email and a strong password
    And I submit the registration form
    And I see the registration success confirmation
    Then attempting to sign in with those exact credentials should succeed
    And the account should appear in the backend user list for that email
```

### 8.2 Generic Placeholder Template (categories F–K, apply to ANY endpoint)

```gherkin
Feature: [Service Name] — [Endpoint/Action Name]

  Background:
    Given the [service/actor] is authenticated as [role]

  @[domain] @[sub-feature] @contract-boundary @major
  Scenario Outline: [Endpoint] rejects requests violating "<constraint>"
    When I send a request to [endpoint] with "<field>" = "<boundary_value>"
    Then the response should be rejected with "<expected_error_code>"
    Examples:
      | field | boundary_value | expected_error_code |

  @[domain] @[sub-feature] @authz-boundary @critical
  Scenario: [Endpoint] denies access across tenants/roles
    Given a resource belonging to [tenant/user A]
    When [tenant/user B] requests that resource via [endpoint]
    Then the response should be denied with [exact status]
    And no data belonging to [tenant/user A] should appear in the response

  @[domain] @[sub-feature] @dependency-failure @critical
  Scenario: [Endpoint] handles [dependency] failure without corrupting state
    Given [dependency] is simulated to [time out / return 5xx / return malformed data]
    When I send a valid request to [endpoint]
    Then the response should be [expected fallback/error behavior per code]
    And no partial/inconsistent state should be left behind

  @[domain] @[sub-feature] @concurrency @major
  Scenario: Concurrent identical requests to [endpoint] do not double-apply the effect
    When two identical requests are sent to [endpoint] at the same time
    Then only one should succeed / both should return the same idempotent result
    And the final system state should reflect exactly one applied effect
```

### 8.3 Generic E2E Template

```gherkin
Feature: [Journey Name] — cross-service flow

  @e2e @[journey-tag] @critical
  Scenario: [Describe the real business flow in one sentence]
    Given [starting state / actor]
    When [step 1 — call to Service A]
    And [step 2 — resulting call to Service B, using real output from step 1]
    And [step 3 — resulting call to Service C, using real output from step 2]
    Then [the end-user-visible outcome should be correct]
    And [independently verify final state via a path different from the journey itself]
```

---

## 9. Additive/Scalable Growth Rules

1. **Never edit an existing `.feature`, step-definition, or page-object file to add a new feature's
   tests.** A new feature always gets its own new files, in its own folder. Existing files are touched
   only to fix a proven bug in that exact file.
2. **One feature = one new folder + one registry entry.** Adding a feature means: create its folder,
   generate its scenarios, add rows to `FEATURE_REGISTRY.md`. Never regenerate the registry from scratch.
3. **Shared/support files are append-only.** Add a new helper/page-object class beside existing ones;
   never rewrite an existing function's behavior to fit a new feature.
4. **Every new feature's tests must be runnable in isolation**, with no dependency on any other feature's
   test having run first.
5. **New endpoint vs new variant:** if it has its own route/schema, it's a new feature folder. If it's a
   new input variant of an existing endpoint, it's a new scenario inside the existing feature's
   Category C/F file, not a new folder.
6. **Configuration changes are made once, centrally** (Section 2) — never per-feature.

---

## 10. Feature Registry Rules

`tests/automation/FEATURE_REGISTRY.md` is the single source of truth for coverage state.

- One row per (endpoint, category) pair. Columns: `Endpoint | Category | Tag | Status (Covered / N/A /
  Not-Yet-Testable / Known-Gap) | Scenario file | Last updated`.
- Separate table for E2E journeys (Section 7).
- **Append-only** in normal operation. Only edited in place when a category's status genuinely changes
  (e.g. Not-Yet-Testable → Covered).
- This is what lets anyone answer "is this service actually tested" without reading every feature file.

---

## 11. LLM Test-Generation Instruction Block

Paste this verbatim whenever asking an LLM to generate tests for a new endpoint:

> You are generating automated tests for a service endpoint. Follow these rules exactly:
>
> 1. Before writing any scenario, read and summarize: the route/controller, the request/response schema,
>    the service/business logic, every downstream dependency call, and the auth/authorization checks.
>    List the concrete constraints, branches, and dependency calls you found — do not proceed until you
>    can list them.
> 2. Check `FEATURE_REGISTRY.md` for existing coverage. Only generate scenarios for categories not
>    already covered — never duplicate.
> 3. Generate scenarios strictly from Categories A–K (Section 6). Every scenario must trace to a specific
>    line/branch/constraint found in step 1 — no invented edge cases with no basis in the actual code.
> 4. Your goal is to find ways this endpoint could break or misbehave, not to prove it works. Prioritize
>    boundary values, wrong types, missing/expired auth, cross-tenant access, dependency failures,
>    concurrent duplicate requests, and any visible-but-untested error/exception path.
> 5. Every `Then` step must assert a specific, independently-verifiable outcome — never "no error
>    occurred" alone. For any "success" scenario, verify the real effect through a second path (re-fetch
>    the resource, check the database, attempt the logically-dependent next action) — never trust a
>    success message alone.
> 6. Output only NEW files in NEW folders following the existing structure (Section 3). Never modify an
>    existing `.feature`, step-definition, or page-object file. If a shared helper is genuinely missing,
>    add a new function beside existing ones — never alter existing functions.
> 7. For every scenario generated, add a row to `FEATURE_REGISTRY.md`. Mark inapplicable categories N/A
>    with a one-line reason; mark tooling-limited categories `@not-yet-testable`.
> 8. If you find a code path with no visible error handling (uncaught exception, missing null check, a
>    dependency call with no timeout/retry), generate the test asserting the CURRENT behavior, tag it
>    `@known-gap`, and state in a comment what correct behavior should be. Never silently skip broken
>    code paths.
> 9. For every multi-step or dynamic-UI flow, add an explicit state assertion between each step
>    (dropdown opened → option list visible; dialog triggered → dialog visible and stable; page
>    transitioned → next page's marker element visible) before proceeding to the next action. Never chain
>    an action directly onto the result of a previous action without this checkpoint.
> 10. For any journey crossing more than one service, place it under `e2e/journeys/`, not `features/`,
>     and verify the final state via a path independent of the journey itself.

---

## 12. Dynamic UI & Multi-Step Flow Reliability Rules

### 12.1 The Core Rule Being Violated When Tests "Run Fast but Don't Complete"

A test is only complete when it asserts the real end state of the journey — not when the last click
succeeds. The automation framework has no concept of "did the user's actual goal get accomplished"; that
gap is entirely the test author's responsibility to close with assertions.

**Rule:** every transition between steps (page to page, step to step, dialog opened to dialog closed)
must have an explicit assertion that the NEXT expected state is visible/present BEFORE interacting with
it. Never chain "click → immediately act on the result" without a state check in between.

### 12.2 Dropdowns
- **Native `<select>` elements:** interact via value/label directly — no visibility wait needed for
  options.
- **Custom dropdowns (styled div/list):**
  1. Click to open.
  2. **Assert the option-list container is visible** before doing anything else — the step almost every
     broken flow skips.
  3. Locate and click the option by accessible role/text, never by position/index.
  4. **Assert the dropdown closed and the trigger/input reflects the selected value** before moving on.

### 12.3 Dialogs
- **Native browser dialogs** (`alert`/`confirm`/`prompt`): a handler must be registered BEFORE the
  triggering action, or the engine auto-dismisses it and the flow silently continues on a false
  assumption. Handling the dialog is its own discrete step, placed immediately before the trigger.
- **In-page/custom modals:** assert the modal is visible AND a stable element inside it (e.g. its submit
  button) is enabled before interacting — avoids clicking during a fade/slide-in animation, a very common
  source of intermittent failures.
- **Closing either kind:** always assert the dialog/modal is gone (not just that a "close" click
  happened) before asserting anything about the page underneath — a modal still visually closing but
  still intercepting clicks will make the NEXT action silently fail or hit the wrong element.

### 12.4 Scrolling
- Standard page-level scrolling into view is typically automatic before an action.
- **Custom scrollable containers** (inner `<div>` with its own scrollbar — common in dropdown lists,
  data tables, chat panels) are NOT automatically scrolled. The element must be explicitly scrolled into
  view within that specific container, not the page.
- **After scrolling, re-assert visibility** before interacting — a completed scroll is not proof the
  target is now actually visible/interactable (it may be behind a sticky header, partially clipped, etc.).

### 12.5 Multi-Step / Multi-Page Flows (fill → next → dialog → submit → back → resubmit)
1. **Every page/step transition is a checkpoint, not a formality.** After any "Next"/navigation action,
   the first thing the flow does is assert a unique marker element of the new step is visible — never
   assume the click worked and immediately try to fill the next form.
2. **Never reuse a locator captured before a navigation.** Re-locate elements fresh in the new context
   after any page/step change, even within the same SPA route.
3. **"Back" is a state reset, not a rewind.** Assert what's actually pre-filled (if anything) after going
   back, rather than assuming prior input persisted.
4. **Each discrete step is its own named action** in the step definitions/page object — never inlined
   together. This makes the failure point obvious and forces an explicit state check at each boundary.
5. **The final assertion of a multi-step flow must verify the CUMULATIVE, correct result** — e.g. after
   page 1 → dialog submit → page 2 → back → resubmit new data → final submit, the closing assertion must
   confirm the system's final state reflects the LAST submitted data specifically, not the first attempt
   or a merge of both. This is Category E's silent-failure logic applied to a multi-step context.
6. **An intermediate step must be able to fail the whole test.** Add an explicit assertion after every
   intermediate step, even ones that "always work" — a step silently no-op'ing (e.g. a dropdown that
   didn't actually open) is exactly what produces a fast, "successful," but incomplete run.

---

## 13. Diagnostic Checklist — "It Runs But Doesn't Complete Properly"

Work through these in order before assuming it's a framework/tool problem:

1. Is there an explicit assertion for the FINAL expected state of the whole journey, tied to real data
   (not just "a success message appeared somewhere")? If not, add one first.
2. For each transition, is there a visibility/state assertion for the next state BEFORE the next action
   is attempted? Any click → immediately-interact-with-result chain is the first place to add a
   checkpoint.
3. For any dropdown: is the option-list container's visibility asserted before clicking an option?
4. For any dialog/modal: is it a native browser dialog (needs a pre-registered handler) or a custom
   in-page modal (needs a visible + stable-and-enabled check)? Confirm the right kind is being handled.
5. For any scrolling issue: is the element inside a custom-scrolling container rather than the page body?
   If so, does the scroll target that specific container?
6. For "back then resubmit": is the test asserting what's actually present in the form after going back,
   rather than assuming prior data is still there?
7. Replay the failing run with the trace viewer, frame by frame — the exact moment the real app state
   diverges from what the script assumed will be visible in the DOM snapshots.

---

## 14. Per-Feature Checklist (fill this out before writing any scenario for a new feature)

| # | Question | Category | Verification method required |
|---|---|---|---|
| 1 | What is the minimum valid input that should succeed? | A | Independent re-check of resulting state |
| 2 | What is the real system-level effect of success? | A | Direct check via API/DB/second UI path |
| 3 | Can this exact valid action be repeated? Should it be? | B | Confirm reject + confirm no second effect |
| 4 | What are ALL stated constraints on each input field? | C | List every constraint explicitly, one scenario per constraint minimum |
| 5 | Is each constraint enforced only in the UI, or also server-side? | C | Bypass UI (API client), confirm server independently rejects |
| 6 | Could invalid input ever be mistaken for success (wrong redirect, false toast)? | D | Explicit negative assertion: success indicators must NOT appear |
| 7 | If the UI shows success, is that success independently confirmed elsewhere? | E | Second, unrelated verification path |
| 8 | Are there permission/role variants of this action? | RBAC extension of A/C/D | Repeat per role where behavior differs |
| 9 | What happens with malformed/unexpected input (corrupted query strings, oversized payloads)? | C/D/F | Explicit graceful-fallback scenario, specific expected fallback state |
| 10 | Does a failure produce console errors/network errors the UI silently swallows? | Cross-cutting | Assert clean console/network across ALL scenarios, not a separate test |
| 11 | Does this endpoint call other services? | F/H | List each dependency; one H scenario per dependency failure mode |
| 12 | Does this endpoint require auth/tenant scoping? | G | Missing/expired/wrong-role/cross-tenant scenarios |
| 13 | Can this action be triggered concurrently/duplicately at the request level? | I | Concurrent-identical-request scenario, verified via final state |
| 14 | Are there payload size, pagination, or rate limits? | J | Boundary + one-over scenarios, confirm recovery after limit |
| 15 | Is this part of a larger cross-service user journey? | E2E | Add/extend an `e2e/journeys/` scenario, independently verified |

Row 10 is the one most often skipped: a test can pass every explicit assertion while the app throws
errors in the background that nobody checks for.

---

## 15. Definition of "Feature Fully Covered"

A feature is only considered covered when:

1. All applicable categories from Section 6 exist as separate, tagged scenarios (mark inapplicable ones
   N/A with a reason — never leave them blank).
2. Every constraint identified in checklist row 4/11 has its own scenario, not lumped together.
3. Every scenario's `Then` steps assert real, specific, independently-verifiable outcomes — never a
   proxy.
4. Console/network cleanliness (row 10) is checked across all scenarios.
5. Role-based variants repeat categories A/C/D/G per role where applicable.
6. Every multi-step flow within the feature has a checkpoint assertion at every transition (Section 12).
7. If the feature is part of a cross-service journey, that journey exists (or is extended) in
   `e2e/journeys/` and is independently verified.

Anything short of this is partial coverage and must be labeled as such in `FEATURE_REGISTRY.md` — never
presented as "the feature is tested."