# Microservice Test Generation Ruleset — Addendum (Code-Aware, Additive, Generic)

> This is an ADDENDUM to `generic-test-flow-rules.md` and `professional-automation-structure.md`.
> Categories A–E (Happy Path / Duplicate / Invalid-Rejected / False-Positive / Silent-Failure) still
> apply exactly as defined there. This document adds:
> 1. Categories F–K, specific to microservices and derived by READING THE SOURCE CODE, not guessing.
> 2. Strict rules so growth is always additive — nothing here requires rewriting existing tests.
> 3. The literal instruction block to give an LLM so it generates adversarial, break-it tests instead of
>    happy-path filler.

---

## 1. Meta-Rules for Additive, Scalable Growth (read this first, every time)

These rules exist so the suite never needs to be "redone" — only extended.

1. **Never edit an existing `.feature`, step-definition, or page-object file to add a new feature's
   tests.** A new feature always gets its own new files, in its own folder, following the structure in
   `professional-automation-structure.md`. Existing files are only touched to fix a proven bug in that
   exact file.
2. **One feature = one new folder + one registry entry.** Maintain a single file,
   `tests/automation/FEATURE_REGISTRY.md`, listing every feature/endpoint covered and which of
   categories A–K it has. Adding a feature means: create its folder, generate its scenarios, add one row
   to the registry. Never regenerate the registry from scratch.
3. **Shared/support files (`support/`, `utils/`, `page-objects/base.page.ts`, configs) are
   append-only.** You may add a new helper function or a new page object class. You do not rewrite
   existing functions' behavior to fit a new feature — if a shared helper doesn't fit, add a new one
   beside it.
4. **Every new feature's tests must be runnable in isolation** (`npx playwright test
   tests/automation/<domain>/<feature>/`) and must not depend on any other feature's test having run
   first. This is what makes "just add a folder" actually safe.
5. **When in doubt about whether something is a new feature or a variant of an existing one:** if it has
   its own endpoint/route/schema, it's a new feature folder. If it's a new input variant of an existing
   endpoint, it's a new scenario inside the existing feature's Category C/F file, not a new folder.

---

## 2. What the LLM Must Read Before Generating Anything

Do not generate a single scenario from the feature name alone. For a microservice endpoint, the LLM must
first ingest:

| Source | What to extract |
|---|---|
| Route/controller definition | HTTP method, path, path/query params, required auth |
| Request schema / DTO / validation annotations | Every field: type, required/optional, min/max length, regex, enum values, uniqueness constraints |
| Response schema | Success shape, all documented error codes and their meaning |
| Service/business logic layer | Side effects (DB writes, events published, calls to other services), any conditional branches, any TODO/FIXME comments, any unhandled exception paths |
| Downstream dependencies | Which other services/DBs/queues this endpoint calls, and what happens in code if each one times out, errors, or returns malformed data |
| Existing tests for this endpoint (if any) | To avoid duplicating Category A–E coverage that already exists — only fill gaps |
| Auth/authorization middleware | What roles/scopes/tenant checks apply, and where in the code they're enforced |

**Rule:** every generated scenario must trace back to something actually observed in the code above. A
scenario invented without a corresponding code detail (a constraint, a branch, a dependency call) is
speculation, not a test, and must not be generated.

---

## 3. Categories F–K (Microservice-Specific, Adversarial)

These extend A–E. Same rules apply: one behavior per scenario, tagged, real independent assertions, no
proxies.

### F — Contract & Schema Boundary
- **Derive from:** the request/response schema and validation annotations.
- **Generate one scenario per constraint found in code**, not one generic "invalid input" scenario:
  - Field at exactly max length / one over max length.
  - Field at exactly min length / one under min length.
  - Wrong data type for a typed field (string where number expected, etc.).
  - Enum field given a value outside the declared set.
  - Required field omitted entirely (not just empty string — genuinely absent from the payload).
  - Unexpected extra field included — assert it's ignored/rejected per how the code actually handles
    unknown fields (strict vs permissive parsing).
- **Assert:** the exact documented error code/shape from the response schema — not just "a 4xx happened."

### G — Authentication & Authorization Boundary
- **Derive from:** auth middleware and any role/scope/tenant checks in the code.
- **Generate scenarios for:**
  - No token / missing auth header → correct 401, no data leaked in the response body.
  - Expired token → correct rejection, not silently treated as valid.
  - Valid token, wrong role/scope → correct 403.
  - Valid token for a DIFFERENT tenant/user attempting to access this tenant/user's resource
    (IDOR check) → must be rejected, not just "the wrong data doesn't happen to show" — assert
    explicitly that access is denied.
- **Assert:** exact status code AND that no unauthorized data appears anywhere in the response, headers,
  or logs accessible to the caller.

### H — Downstream Dependency Failure Injection
- **Derive from:** every outbound call this endpoint's code makes (DB, other microservice, queue, cache).
- **For each dependency, generate a scenario simulating (via mock/stub):**
  - Timeout from the dependency.
  - 5xx / error response from the dependency.
  - Malformed/unexpected response shape from the dependency.
- **Assert the code's actual documented/expected behavior for each** — e.g. circuit breaker opens,
  retry occurs a bounded number of times, a specific fallback/error response is returned to the caller,
  the request does NOT partially succeed and leave inconsistent state. If the code has no handling for a
  dependency failure path at all, that is itself a finding — the scenario should assert the CURRENT
  (likely broken) behavior and be tagged `@known-gap` until the code is fixed, rather than being
  skipped.

### I — Concurrency & Idempotency
- **Derive from:** whether the endpoint has an idempotency key, unique constraints, or shared mutable
  state (counters, balances, seat/slot allocation).
- **Generate scenarios for:**
  - Two identical requests fired concurrently → exactly one should succeed if the action must be
    unique, or both should produce the same result if idempotency is intended — verify which the code
    claims to guarantee, then assert that specific guarantee.
  - Rapid sequential duplicate requests with the same idempotency key (if supported) → second request
    must return the original result, not create a second effect.
- **Assert:** final system state (via API/DB check), not just both HTTP responses individually.

### J — Resource & Payload Limits
- **Derive from:** any documented/coded limits — payload size caps, pagination limits, rate limits.
- **Generate scenarios for:**
  - Payload at exactly the size limit / one byte over.
  - Pagination requested beyond available data (e.g. page far past the last page) → graceful empty
    result, not an error or crash.
  - Rate limit exceeded → correct 429 with retry-after semantics if coded, and confirm the limit
    actually resets appropriately afterward.

### K — Observability Under Failure
- **Derive from:** logging/tracing/metrics code paths (correlation ID propagation, error-level logging).
- **Generate scenarios asserting:**
  - A correlation/trace ID passed in on the request is present in the resulting error response and/or
    propagated to downstream calls (if verifiable via test doubles).
  - A failure path actually logs at the correct severity (verifiable if logs are accessible to the test
    harness) rather than failing silently with no trace.
- **Note:** if observability isn't testable in your current harness, mark this category `@not-yet-testable`
  in the registry rather than skipping it unmarked — the gap should be visible, not invisible.

---

## 4. Updated Category Table (A–K, all additive)

| # | Category | Tag | Comes from |
|---|---|---|---|
| A | Happy path | `@happy-path` | Original taxonomy |
| B | Duplicate/repeat | `@duplicate` | Original taxonomy |
| C | Invalid input rejected | `@invalid-rejected` | Original taxonomy |
| D | False-positive success | `@false-positive-check` | Original taxonomy |
| E | Silent failure | `@silent-failure-check` | Original taxonomy |
| F | Contract/schema boundary | `@contract-boundary` | This addendum |
| G | AuthN/AuthZ boundary | `@authz-boundary` | This addendum |
| H | Downstream dependency failure | `@dependency-failure` | This addendum |
| I | Concurrency/idempotency | `@concurrency` | This addendum |
| J | Resource/payload limits | `@resource-limit` | This addendum |
| K | Observability under failure | `@observability` | This addendum |

A feature/endpoint is only "fully covered" once its registry row has every applicable category checked —
"applicable" meaning: skip a category only if the code genuinely has nothing matching it (e.g. no
downstream calls exist → H is N/A, not failed). Mark N/A explicitly; never leave it blank.

---

## 5. Generic Scenario Template (placeholder form — apply to ANY endpoint)

This is deliberately feature-agnostic. Replace the bracketed terms; do not change the shape.

```gherkin
Feature: [Service Name] — [Endpoint/Action Name]

  Background:
    Given the [service/actor] is authenticated as [role]

  @[domain] @[sub-feature] @happy-path @critical
  Scenario: [Action] with fully valid input succeeds
    When I send a valid [request] to [endpoint]
    Then the response should be [exact expected shape/status]
    And [independent verification of real effect, e.g. querying the resource back]

  @[domain] @[sub-feature] @contract-boundary @major
  Scenario Outline: [Endpoint] rejects requests violating "<constraint>"
    When I send a request to [endpoint] with "<field>" = "<boundary_value>"
    Then the response should be rejected with "<expected_error_code>"
    Examples:
      | field | boundary_value | expected_error_code |
      | ...   | ...            | ...                  |

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

---

## 6. The Literal Instruction Block to Give an LLM

Paste this verbatim as a standing system/task instruction whenever asking an LLM to generate tests for a
new endpoint. It enforces code-reading, adversarial thinking, and additive-only output.

> You are generating automated tests for a microservice endpoint. Follow these rules exactly:
>
> 1. Before writing any scenario, read and summarize: the route/controller, the request/response
>    schema, the service/business logic, every downstream dependency call, and the auth/authorization
>    checks. List the concrete constraints, branches, and dependency calls you found — do not proceed
>    until you can list them.
> 2. Check `FEATURE_REGISTRY.md` for whether this endpoint already has coverage. Only generate scenarios
>    for categories not already covered — do not regenerate or duplicate existing ones.
> 3. Generate scenarios strictly from categories A–K as defined in this ruleset. Every scenario must
>    trace to a specific line/branch/constraint you found in step 1 — no invented edge cases with no
>    basis in the actual code.
> 4. Your goal is to find ways this endpoint could break or misbehave, not to prove it works. Prioritize:
>    boundary values, wrong types, missing/expired auth, cross-tenant access, dependency failures,
>    concurrent duplicate requests, and any error/exception path visible in the code but not obviously
>    tested.
> 5. Every `Then` step must assert a specific, independently-verifiable outcome. Never assert "no error
>    occurred" as the sole check. For any "success" scenario, verify the real effect through a second
>    path (re-fetch the resource, check the database, attempt the logically-dependent next action) —
>    never trust a success message alone.
> 6. Output only NEW files in NEW folders following the existing directory structure. Do not modify any
>    existing `.feature`, step-definition, or page-object file. If a shared helper is genuinely missing,
>    add a new function to the relevant `utils/`/`support/` file — do not alter existing functions.
> 7. For every scenario generated, add one row to `FEATURE_REGISTRY.md` recording the endpoint, the
>    category, and the tag. Mark any inapplicable category as N/A with a one-line reason, and mark any
>    category you couldn't test due to tooling limits as `@not-yet-testable`.
> 8. If you find a code path with no visible error handling (e.g. an uncaught exception, a missing null
>    check, a dependency call with no timeout/retry), generate the test asserting the CURRENT behavior,
>    tag it `@known-gap`, and state in a comment what the correct behavior should be. Do not silently
>    skip broken code paths.

---

## 7. Microservice-Specific Folder Structure (Additive Extension)

This extends the folder structure in `professional-automation-structure.md`. Nothing below replaces it —
these are new folders that exist specifically because a microservice needs dependency mocking, per-tenant
auth fixtures, and a coverage registry that a UI-only suite doesn't need.

```
tests/
└── automation/
    ├── features/
    │   └── <domain>/
    │       └── <endpoint-name>/
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
    ├── step-definitions/
    │   └── <domain>/
    │       └── <endpoint>.steps.ts        # backs ALL category files above for this endpoint
    │
    ├── api-clients/
    │   └── <domain>/
    │       └── <endpoint>.api.ts          # direct backend calls — required for F, G, I verification
    │
    ├── mocks/                              # NEW — required for Category H (dependency failure injection)
    │   └── <dependency-name>/
    │       ├── timeout.mock.ts             # simulates the dependency timing out
    │       ├── error-5xx.mock.ts           # simulates the dependency returning a server error
    │       └── malformed-response.mock.ts  # simulates the dependency returning an unexpected shape
    │
    ├── fixtures/
    │   ├── auth/                           # NEW — required for Category G (authz boundary)
    │   │   ├── tenant-a-user-token.json
    │   │   ├── tenant-b-user-token.json
    │   │   ├── expired-token.json
    │   │   └── wrong-role-token.json
    │   └── idempotency/                    # NEW — required for Category I (concurrency)
    │       └── sample-idempotency-keys.json
    │
    ├── support/
    │   ├── world.ts
    │   ├── hooks.ts
    │   ├── environment.ts
    │   └── correlation-id.ts               # NEW — required for Category K (observability)
    │
    └── FEATURE_REGISTRY.md                 # NEW — single coverage source of truth, append-only
```

**Rule:** when a new endpoint is added, only new leaf files/folders are created under `features/`,
`step-definitions/`, `api-clients/`, `mocks/` (if new dependencies are involved), and `fixtures/` (if new
auth/tenant combinations are needed). The top-level structure itself never changes.

---

## 7.5 End-to-End (E2E) Test Flow — the Missing Layer

Everything in Categories A–K is **feature-level**: one endpoint, tested in isolation. None of them prove
that a real user journey works *across* features and *across* microservices. That's a separate layer,
with its own folder, its own tagging, and its own rules — it does not replace A–K, it sits on top of them.

### Where it lives (additive folder)

```
tests/
└── automation/
    ├── features/            # feature-level (A–K), one endpoint per file — unchanged
    ├── e2e/                 # NEW — top-level, sibling to features/
    │   ├── journeys/
    │   │   ├── new-user-onboarding.feature
    │   │   ├── purchase-checkout-flow.feature
    │   │   └── admin-user-suspension-flow.feature
    │   ├── step-definitions/
    │   │   └── journeys.steps.ts
    │   └── support/
    │       └── journey-context.ts     # carries state between steps that cross multiple services
    └── FEATURE_REGISTRY.md
```

### What makes something an E2E journey (not just another feature scenario)

A scenario belongs in `e2e/journeys/`, not in `features/`, when it satisfies **all** of:
1. It crosses **more than one microservice/endpoint** in sequence (e.g. registration service → auth
   service → dashboard service).
2. It represents something a **real user or business process actually does end to end**, not an
   artificial combination invented for test convenience.
3. Its pass/fail meaning is "the whole journey works," not "this one endpoint's contract is correct" —
   individual endpoint correctness is already covered by A–K; E2E exists to catch **integration** gaps
   that per-endpoint tests structurally cannot see (e.g. service A's success writes data in a shape
   service B doesn't actually expect).

### Rules specific to E2E

- **Tag:** `@e2e`, plus a journey-name tag (`@onboarding-journey`), plus severity. E2E critical-path
  journeys are almost always `@critical`.
- **Fewer, not more:** E2E suites are deliberately small in count and slow to run (real service calls,
  real sequencing) — do not generate an E2E journey for every possible path. Cover the handful of
  journeys that represent actual core business value or the highest-risk cross-service handoffs.
- **Real service state carries forward within one scenario.** Unlike feature-level tests (isolated,
  disposable data per scenario), an E2E scenario's `Given`/`When` steps build on the *actual result* of
  the previous step (the real account just created, the real token just issued) — this is intentional
  and is what makes it "end to end."
- **Independent verification still applies (Category E logic, but across services).** At the end of the
  journey, verify the final state through a path different from the one the journey itself used — e.g.
  after "checkout flow" completes, independently query the order service and the inventory service, not
  just trust the UI's "order confirmed" screen.
- **Run separately in CI** from the feature-level suite: feature-level (A–K) runs on every commit/PR
  (fast, mocked dependencies per Category H); E2E runs on a slower cadence (pre-merge to main, nightly,
  or pre-release) against a real integrated environment, because it's inherently slower and more
  expensive to run.
- **Failure diagnosis:** because an E2E scenario spans services, its failure-artifact capture
  (screenshot/video/trace) must also capture **which service in the chain failed** — log/tag which step
  and which underlying service call failed, not just "the journey failed at step 4," so triage doesn't
  require re-running the whole chain to find the break point.

### Generic E2E Template (placeholder form)

```gherkin
Feature: [Journey Name] — cross-service flow

  @e2e @[journey-tag] @critical
  Scenario: [Describe the real business flow in one sentence]
    Given [starting state / actor]
    When [step 1 — call to Service A]
    And [step 2 — resulting call to Service B, using real output from step 1]
    And [step 3 — resulting call to Service C, using real output from step 2]
    Then [the end-user-visible outcome should be correct]
    And [independently verify the final state via a path different from the journey itself,
         e.g. query Service C's data store directly, or check Service A's audit log]
```

### Registry addition for E2E

Add a separate table (or section) in `FEATURE_REGISTRY.md` for journeys, since they aren't per-endpoint:

| Journey | Services involved | Tag | Status | Scenario file | Last updated |
|---|---|---|---|---|---|

---



These are additions to the configuration rules already stated in `generic-test-flow-rules.md` Section 1.
State them as requirements to whoever owns the config files — do not treat any of these as optional:

- **Environment isolation:** each environment (`dev`, `staging`, `ci`) must have its own config file
  under `config/environments/`, holding at minimum: base URL, service-to-service base URLs for any
  dependency being mocked, and test-only auth credentials/tokens. No environment's config may be
  hardcoded inside a test or step definition file.
- **Mock/stub server configuration:** downstream dependencies used in Category H must be mockable via
  configuration (a toggle or base-URL override), never by editing the service's own code. The test
  config must be able to point a dependency call at a mock server for the duration of a single scenario
  without affecting other scenarios running in parallel.
- **Auth fixture configuration:** tokens/credentials for each role and tenant used in Category G must be
  generated or retrieved through config-driven setup (a test-only auth endpoint or signed test tokens),
  never committed as long-lived real credentials in the repo.
- **Idempotency key configuration:** if the service supports idempotency keys, the test config must
  define how a fresh, unique key is generated per scenario run and how a duplicate key is deliberately
  reused for Category I scenarios.
- **Correlation/trace ID propagation:** test config must define how a correlation ID is injected on
  outbound test requests, and where the harness looks for it in responses/logs — required for
  Category K to be anything more than `@not-yet-testable`.
- **Reporting configuration (Allure):** every category tag (A–K) must map to an Allure label/severity so
  a report can be filtered by category, not just by domain — this is what lets you answer "do we have
  dependency-failure coverage across all services" in one report view instead of reading every file.
- **CI configuration:** category H (dependency failure) and category J (resource/rate limits) scenarios
  must run against the mock layer in CI, never against real downstream services or real rate limits —
  configuration must make this the default, not something a developer has to remember to set.
- **Secrets handling:** any real secret needed for staging/CI runs (API keys, signing keys for test
  tokens) must be injected via the CI secret store, never present in any file under `tests/automation/`.

**Rule:** none of the above requires touching an existing feature's test files. Config changes are made
once, in `config/`, and every existing and future feature automatically benefits — this is what keeps the
whole suite additive instead of requiring a rewrite every time a new microservice is onboarded.

---

## 9. Registry File Rules

`tests/automation/FEATURE_REGISTRY.md` is the single source of truth for coverage state. Rules:

- One row per (endpoint, category) pair.
- Columns: `Endpoint | Category | Tag | Status (Covered / N/A / Not-Yet-Testable / Known-Gap) | Scenario file | Last updated`.
- This file is **append-only** in normal operation — new rows are added as features/categories are
  covered. It is only edited in place when a category's status genuinely changes (e.g.
  `Not-Yet-Testable` → `Covered` once tooling improves).
- This file is what lets you or any reviewer answer "is this microservice actually tested" without
  reading every feature file — a quick scan shows exactly which endpoints are missing which category.