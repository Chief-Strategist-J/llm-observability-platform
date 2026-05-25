---
trigger: always_on
---
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NON-NEGOTIABLE AXIOMS  —  any violation = immediate PR REJECT, no discussion
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  AX-1   packages NEVER import each other's source — ever, in any language
  AX-2   packages NEVER share a database, schema, or table
  AX-3   packages NEVER share memory or in-process state
  AX-4   packages communicate ONLY via versioned published contracts
  AX-5   API/GraphQL contract is written, reviewed, and merged BEFORE src/
  AX-6   shared/ contains ZERO business logic — schemas and conventions only
  AX-7   duplication across packages is ACCEPTABLE — coupling is NOT
  AX-8   every cross-boundary call MUST emit a trace span with full attrs
  AX-9   no package calls another package's internal endpoint directly
  AX-10  apis/ is a router — ZERO domain logic, ZERO db access lives there
  AX-11  every infra dependency uses a PORT interface — no vendor in logic
  AX-12  NO package hardcodes a vendor (postgres, mongo, kafka, stripe, s3)
  AX-13  every schema change is a numbered migration file — never manual
  AX-14  every API version lives until explicitly sunset — never silently dropped
  AX-15  CI must pass on every commit — no exceptions, no force pushes to main
  AX-16  every package has its own scripts/ — no package calls another's scripts
  AX-17  GraphQL schema is a contract — schema changes follow same version rules
  AX-18  every feature starts with API/GraphQL design — code follows contract
  AX-19  no script contains business logic — scripts orchestrate only
  AX-20  every package is deployable in complete isolation — no shared boot order
  AX-21  LAZY GENERATION: generate only what is needed, only when needed
  AX-22  PROTOTYPE→SCALE: start with the minimal structure that fits your stage
  AX-23  COUPLING DETECTION is a CI gate — violations block merge, no exceptions
  AX-24  TRACING is a first-class citizen — no feature ships without spans
  AX-25  MIGRATIONS are immutable law — no migration = no schema change, ever


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LAZY GENERATION RULES  —  generate only when you need it
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The full structure defined in this document is the DESTINATION, not the
starting point. Nothing is created speculatively. Nothing is scaffolded
"just in case". You build exactly what you need RIGHT NOW and scale when
a real forcing function appears.

GENERATION TRIGGER RULES
──────────────────────────────────────────────────────────────

  G-LAZ-1   NO file is created until its immediate parent rule requires it
  G-LAZ-2   NO directory is created until at least one file must live in it
  G-LAZ-3   NO script is written until you must run that operation
  G-LAZ-4   NO contract version (v2, v3) is created until a breaking change
             actually occurs — not "might occur"
  G-LAZ-5   NO adapter is written until you adopt that vendor
  G-LAZ-6   NO port interface is defined until at least one package needs it
  G-LAZ-7   NO test suite (integration, e2e, performance) is created until
             the feature under test is merged and working
  G-LAZ-8   NO CI stage is added until the tool it calls exists
  G-LAZ-9   NO kubernetes manifest is written until you deploy to kubernetes
  G-LAZ-10  NO terraform file is written until infra is provisioned via terraform
  G-LAZ-11  NO grpc contract is written unless a service explicitly requires grpc
  G-LAZ-12  NO asyncapi/event schema is written until a real async event exists

WHAT THIS MEANS IN PRACTICE
──────────────────────────────────────────────────────────────

  "I want a feature" does NOT generate:
    ✗ all 28 scripts
    ✗ kubernetes/ overlays
    ✗ terraform/
    ✗ v2 of any contract
    ✗ performance/ test suite
    ✗ all 12 adapter stubs
    ✗ proto/ contracts (unless grpc is chosen)
    ✗ asyncapi/ schemas (unless async is chosen)

  "I want a feature" DOES generate:
    ✓ contracts/ (the chosen type only — REST or GraphQL or event, not all three)
    ✓ src/ (after contract merges)
    ✓ database/migrations/ (if feature touches db)
    ✓ scripts/setup.sh, run.sh, test.sh, migrate.sh, scan.sh (minimum set)
    ✓ tests/unit/ (immediately, alongside src/)
    ✓ .env.example entries for this feature's vars

  "I need to call this feature from another package" generates:
    ✓ shared/contracts/{type}/{service}/v1.{ext}
    ✓ src/infra/clients/{service}/v1/ (generated from contract)

  "I need to swap my database vendor" generates:
    ✓ src/infra/adapters/{new-vendor}/
    ✓ update .port-registry

  "I need to deploy to kubernetes" generates:
    ✓ deploy/kubernetes/base/
    ✓ deploy/kubernetes/overlays/{env}/
    ✓ scripts/deploy-k8s.sh

THE LAZY GENERATION CHECKLIST — ask before creating anything
──────────────────────────────────────────────────────────────

  □ Do I need this file RIGHT NOW (not "soon", not "eventually")?
  □ Will this file be empty or contain only placeholder code?
    → If yes, DO NOT create it yet
  □ Is this file required by a rule that is currently active?
    → If no active rule requires it, DO NOT create it
  □ Am I generating this "for completeness" or "as best practice"?
    → If yes, DO NOT create it — wait for a real trigger
  □ Would deleting this file block any current work?
    → If no, it should not exist yet


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROTOTYPE → SCALE PROGRESSION  —  mandatory stages, no skipping
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every project and every package moves through stages. You MUST follow the
stage that matches your current reality. You MUST NOT build for a future
stage until a real forcing function promotes you.

A FORCING FUNCTION is a real, present event — not a plan, not a prediction.
Examples: "we have a second service that needs this" (cross-package contract
becomes real), "production latency regressed" (performance tests become real),
"we are deploying to k8s next week" (k8s manifests become real).

──────────────────────────────────────────────────────────────
STAGE 0 — PROTOTYPE
──────────────────────────────────────────────────────────────

PURPOSE: Validate that the idea works. Nothing else.

Allowed structure (minimum viable, all within one package):
  {package}/
  ├── contracts/
  │   └── openapi/v1.yaml           ← even prototypes have a contract
  ├── src/
  │   ├── api/rest/v1/
  │   │   ├── router.{ext}
  │   │   └── handlers/
  │   └── features/{feature}/
  │       ├── index.{ext}
  │       ├── service.{ext}
  │       └── repository.{ext}      ← may use vendor directly at this stage only
  ├── database/
  │   └── migrations/
  │       ├── 0001_init.sql         ← migrations are NEVER optional, even in stage 0
  │       └── 0001_init.rollback.sql
  ├── scripts/
  │   ├── run.sh
  │   ├── migrate.sh
  │   └── test.sh
  ├── tests/unit/                   ← unit tests are NEVER optional
  └── .env.example

NOT allowed in stage 0:
  ✗ port interfaces / adapters (direct vendor use is acceptable here ONLY)
  ✗ shared/contracts/ (only needed when a second package consumes this)
  ✗ kubernetes/ manifests
  ✗ terraform/
  ✗ CI/CD pipelines (a local test.sh is sufficient)
  ✗ v2 contracts
  ✗ asyncapi / proto (unless the feature is inherently async/grpc)
  ✗ performance/ tests
  ✗ integration tests (unless you have real infra to test against)

NON-NEGOTIABLE even in stage 0:
  ✓ contract written BEFORE src/ (AX-5 always applies)
  ✓ numbered migration files (AX-13 always applies)
  ✓ unit tests alongside src/
  ✓ .env.example with all vars
  ✓ tracing: at minimum, a single root span per request (AX-8 applies)
  ✓ migration header block (always)
  ✓ rollback file for every migration (always)

──────────────────────────────────────────────────────────────
STAGE 1 — SINGLE PACKAGE, PRODUCTION-READY
──────────────────────────────────────────────────────────────

FORCING FUNCTION: you are deploying to production, or a second person is
contributing, or the prototype has validated.

Additions from stage 0:
  ✓ port interfaces — wrap every vendor call behind shared/ports/
  ✓ src/infra/adapters/{vendor}/ — implement port interfaces
  ✓ .port-registry — document every adapter
  ✓ full scripts/ set — all 28 scripts from the reference list
  ✓ tests/integration/ — real infra, clean db per run
  ✓ tests/contract/ — validate own published contract
  ✓ CI pipeline — static analysis, unit, contract, integration, build
  ✓ deploy/docker/ — dev, test, prod compose files
  ✓ OTEL tracer init — full span attrs per T-4
  ✓ tracing middleware on all api/ entry points
  ✓ coupling-map.md — even if empty, must exist and be checked by CI
  ✓ schema.lock — checked into repo

Still NOT required in stage 1:
  ✗ kubernetes/ (until you deploy to k8s)
  ✗ terraform/ (until you provision via terraform)
  ✗ CD pipelines (until you have a staging environment)
  ✗ v2 contracts (until a breaking change forces it)
  ✗ performance/ tests (until you have p99 baselines to enforce)
  ✗ shared/contracts/ (until a second package consumes this)
  ✗ proto or asyncapi (unless your feature requires it)

──────────────────────────────────────────────────────────────
STAGE 2 — MULTI-PACKAGE
──────────────────────────────────────────────────────────────

FORCING FUNCTION: a second package needs to consume this package's API,
or you are splitting a monolith, or a new package is being created.

Additions from stage 1:
  ✓ shared/contracts/{type}/{service}/v1.{ext} — public contract registered
  ✓ shared/events/registry.yaml — if events are introduced
  ✓ .contract-lock — pins contract versions consumed by each package
  ✓ shared/errors/codes.yaml — canonical error codes
  ✓ src/infra/clients/{service}/v1/ — generated, never hand-written
  ✓ shared/tracing/conventions.md — span naming aligned across packages
  ✓ coupling-map.md gets CI enforcement — violations block merge
  ✓ apis/ gateway package — if external clients need a unified entry point
  ✓ contract tests — pact consumer/provider tests across packages
  ✓ CD staging pipeline — deploy before production

Still NOT required in stage 2:
  ✗ kubernetes/ (until you deploy to k8s)
  ✗ terraform/ (until infra is code-managed)
  ✗ CD production pipeline (until staging is stable)
  ✗ performance/ tests (until SLOs are defined)

──────────────────────────────────────────────────────────────
STAGE 3 — SCALED / PRODUCTION MULTI-SERVICE
──────────────────────────────────────────────────────────────

FORCING FUNCTION: production traffic exists, SLOs are defined, you have
multiple environments, or a team beyond 2-3 people contributes.

Additions from stage 2:
  ✓ kubernetes/ manifests — base + overlays per env
  ✓ terraform/ — infra as code
  ✓ CD production pipeline — blue-green or canary
  ✓ tests/performance/ — baselines declared and enforced in CD
  ✓ tests/e2e/ — full flow isolation
  ✓ HPA, PDB, NetworkPolicy — k8s hardening
  ✓ sunset-registry.yaml — version lifecycle tracked in CI
  ✓ shared/tracing/sampling-rules.yaml — production sampling strategy
  ✓ shared/tracing/baggage-keys.md — baggage propagation documented
  ✓ span duration SLO thresholds per endpoint

──────────────────────────────────────────────────────────────
STAGE PROMOTION RULES
──────────────────────────────────────────────────────────────

  SP-1  you always know which stage you are in — it is written in
        .package-meta.yaml under the field: stage: 0|1|2|3
  SP-2  stage promotion requires a PR titled "PROMOTE: {package} stage N→M"
  SP-3  promotion PR only adds structure — no feature code mixed in
  SP-4  you NEVER skip a stage — 0→2 is forbidden
  SP-5  multiple packages in the same project may be at different stages
  SP-6  stage is assessed per-package, not per-project


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROJECT ROOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

project/
├── shared/                          ← only cross-package truth, zero logic
│   ├── contracts/
│   │   ├── openapi/
│   │   │   └── {service}/
│   │   │       ├── v1.yaml
│   │   │       ├── v2.yaml
│   │   │       └── changelog.md
│   │   ├── graphql/                 ← GraphQL schemas (SDL)
│   │   │   └── {service}/
│   │   │       ├── v1.graphql
│   │   │       ├── v2.graphql
│   │   │       └── changelog.md
│   │   ├── proto/                   ← gRPC contracts (generate when grpc needed)
│   │   │   └── {service}/
│   │   │       ├── v1/
│   │   │       └── v2/
│   │   ├── asyncapi/                ← event/queue contracts (generate when async needed)
│   │   │   └── {service}/
│   │   │       ├── v1.yaml
│   │   │       └── changelog.md
│   │   └── json-schema/             ← event payload schemas
│   │
│   ├── events/
│   │   ├── registry.yaml            ← all event names + versions + owners
│   │   └── conventions.md           ← naming rules — MUST READ before adding
│   │
│   ├── errors/
│   │   ├── codes.yaml               ← canonical error codes, never in packages
│   │   └── mapping.md
│   │
│   ├── tracing/
│   │   ├── conventions.md           ← span naming rules — MUST READ (stage 2+)
│   │   ├── baggage-keys.md          ← (stage 3+)
│   │   └── sampling-rules.yaml      ← (stage 3+)
│   │
│   └── ports/                       ← ALL infra port interfaces live here only
│       ├── database.interface        ← generate when first package needs it
│       ├── cache.interface
│       ├── queue.interface
│       ├── storage.interface
│       ├── email.interface
│       ├── sms.interface
│       ├── payment.interface
│       ├── search.interface
│       ├── logger.interface
│       ├── feature-flag.interface
│       ├── metrics.interface
│       └── secret-store.interface
│
├── packages/
│   ├── python/
│   ├── rust/
│   ├── go/
│   ├── node/
│   ├── java/
│   ├── shell/
│   └── apis/                        ← gateway only, no domain logic (stage 2+)
│
├── infra/
│   ├── otel/                        ← collector config (stage 1+)
│   ├── broker/                      ← kafka/rabbitmq/nats config (when async introduced)
│   ├── registry/                    ← buf.build or local contract registry (stage 2+)
│   ├── database/                    ← global provisioning only, no schemas
│   └── platform/
│       ├── docker/
│       │   └── docker-compose.platform.yaml  ← broker, otel, registry only
│       ├── kubernetes/               ← stage 3+ only
│       │   └── platform/
│       ├── terraform/                ← stage 3+ only
│       └── scripts/
│           ├── bootstrap.sh
│           ├── start-platform.sh
│           ├── stop-platform.sh
│           ├── start-all.sh
│           ├── stop-all.sh
│           ├── status.sh
│           ├── migrate-all.sh
│           ├── rollback.sh
│           ├── logs.sh
│           ├── trace-check.sh
│           ├── scan-all.sh
│           └── deploy-all.sh
│
├── .contract-lock                   ← pinned contract versions (stage 2+)
├── .port-registry                   ← adapter implementations per package (stage 1+)
└── coupling-map.md                  ← live violations list — must be empty on main


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API / GRAPHQL FIRST — MANDATORY WORKFLOW (every feature, every language)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Starting ANY feature that has an API surface?
│
└─ STOP — no src/ file is written until contract is merged
   │
   Step 1: choose contract type (pick ONE — do not generate all types)
   │  ├─ client-facing query/mutation?   → GraphQL SDL in shared/contracts/graphql/
   │  ├─ service-to-service sync?        → OpenAPI yaml OR proto (pick one)
   │  ├─ async / event-driven?           → AsyncAPI + json-schema
   │  └─ internal only (no cross-pkg)?   → types in feature/types only — no shared/
   │
   Step 2: write contract file with ALL of:
   │  □ version (v1, v2, ...)
   │  □ all fields with types and nullability
   │  □ all error cases (reference shared/errors/codes.yaml)
   │  □ auth requirements
   │  □ rate limit hint
   │  □ deprecation status (if applicable)
   │
   Step 3: open contract-only PR — no implementation code
   │  □ contract lint passes (spectral / buf lint / graphql-inspector)
   │  □ breaking change check passes (oasdiff / buf breaking)
   │  □ 1 review minimum before merge
   │
   Step 4: update .contract-lock (stage 2+ only)
   │
   Step 5: generate clients/stubs (automated, never hand-written)
   │        LAZY: generate ONLY the client for the language that needs it now
   │
   Step 6: implement feature behind contract
   │
   └─ Step 7: contract tests validate implementation matches contract


GRAPHQL-SPECIFIC CONTRACT RULES
──────────────────────────────────────────────────────────────
  G-1   schema SDL lives in shared/contracts/graphql/{service}/v{n}.graphql
  G-2   resolvers live in feature/handler/ — never in schema file
  G-3   schema stitching / federation config lives in apis/gateway/graphql/
  G-4   every type has a description comment — no undocumented types
  G-5   every field marked @deprecated must have a reason and sunset date
  G-6   breaking GraphQL changes follow same version rules as REST
  G-7   introspection disabled in production — schema served via registry only
  G-8   query depth limit declared in apis/gateway/graphql/limits.yaml
  G-9   query complexity limit declared in apis/gateway/graphql/limits.yaml
  G-10  mutations always return the mutated type — never just Boolean
  G-11  subscriptions are async events — backed by queue, never polling
  G-12  N+1 problem is a contract violation — dataloader required per relation
  G-13  generated types from SDL — never hand-written client types

WHAT IS A BREAKING GRAPHQL CHANGE
──────────────────────────────────────────────────────────────
  BREAKING → new version required       COMPATIBLE → in-place allowed
  ──────────────────────────────────    ──────────────────────────────
  removing a type                       adding optional field
  removing a field                      adding new type
  renaming a type or field              adding new query/mutation
  changing field type                   adding new optional arg
  making nullable field non-null        adding @deprecated
  removing enum value                   expanding enum (additive)
  changing arg from optional→required   adding new subscription
  removing a query/mutation/sub         relaxing nullability (non→nullable)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COUPLING RULES  —  STRICT, CI-ENFORCED, ZERO TOLERANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Coupling is the single most dangerous failure mode in this architecture.
A coupling violation left unchecked compounds into a system that cannot be
tested, deployed, or changed in isolation. Therefore:

  COUPLING RULE ZERO:
  A coupling violation on main = the system is broken.
  There is no "we'll fix it later". There is no "just this once".
  Any engineer who introduces a coupling violation owns it.
  It is their P0 until it is resolved.

COUPLING DETECTION — CI ENFORCEMENT
──────────────────────────────────────────────────────────────

  CL-1   CI runs a coupling scan on EVERY commit, every PR, every push
  CL-2   coupling scan is stage 1+ — present from first production commit
  CL-3   coupling scan includes ALL of these checks (zero exceptions):
           □ cross-package source imports (language linter rules)
           □ shared database connections (static analysis + runtime check)
           □ shared in-memory state (static analysis)
           □ hardcoded vendor names in feature/service code (grep + linter)
           □ API calls skipping the generated client (direct HTTP calls)
           □ trace context missing on cross-boundary calls
           □ contracts missing from shared/ (PR that adds shared call without contract)
           □ .port-registry out of sync (missing or stale entries)
           □ .contract-lock out of sync (pinned version does not match shared/)
           □ coupling-map.md has entries without a phase plan (PR blocked)
  CL-4   coupling scan exit code 0 = zero violations
          exit code 1 = violations found — PR merge is blocked, no override
  CL-5   if coupling scan is flaky or misconfigured, it defaults to FAIL
          — never default to pass
  CL-6   scan results are published as CI artifact with full line numbers

COUPLING CLASSIFICATION — SEVERITY ORDER
──────────────────────────────────────────────────────────────

  Severity is ordered highest to lowest. Higher severity = fix first.

  CoI — IDENTITY COUPLING (highest severity)
    Two packages share a database or schema.
    Two packages share in-memory state.
    One package imports source from another package.
    → System cannot be independently deployed. Fix before anything else.

  CoV — VALUE COUPLING
    Hardcoded values shared across packages (e.g. same table name string,
    same error message string, same vendor name).
    → Breaks silently during refactor. Fix in same sprint as discovery.

  CoA — ACTION COUPLING
    One package calls another package's internal HTTP endpoint directly
    (not via generated client, not via contract).
    → Bypasses versioning and tracing. Fix in next PR after discovery.

  CoE — EXECUTION COUPLING
    Shared boot order — package A fails to start if package B is not up.
    Implicit timing dependency not expressed via health checks.
    → Breaks canary deployments. Fix before scaling.

  CoM — MESSAGE COUPLING (lowest severity — acceptable in controlled form)
    Two packages share an event schema.
    This is acceptable ONLY when:
      ✓ schema lives in shared/contracts/asyncapi/ or shared/contracts/json-schema/
      ✓ schema is versioned
      ✓ consuming package pins the version in .contract-lock
    CoM without shared schema or without versioning = CoI severity.

COUPLING MAP
──────────────────────────────────────────────────────────────

  coupling-map.md format (required per entry):

  | ID | Package A | Coupling Type | Package B | Severity | Owner | Phase | Target PR |
  |----|-----------|---------------|-----------|----------|-------|-------|-----------|
  | C-001 | python/auth | CoI | node/payments | HIGH | @dev | 2 | PR#45 |

  Rules:
  □ every known violation has an entry — undocumented violation = P0
  □ every entry has an owner (person), phase (1/2/3), and target PR
  □ no entry may be on main without a phase plan — CI blocks it
  □ every entry resolved in a PR must update coupling-map.md in same PR
  □ coupling-map.md must be empty on main — CI enforces this
  □ quarterly review: stale entries (>30 days past target PR) = team alert

COUPLING RESOLUTION — ONE VIOLATION PER PR
──────────────────────────────────────────────────────────────

  C-RES-1  every violation is resolved in its own isolated PR sequence
  C-RES-2  NEVER combine two violation resolutions in one PR
  C-RES-3  NEVER combine a violation resolution with a feature PR
  C-RES-4  NEVER use "temporary" coupling — there is no temporary coupling
  C-RES-5  NEVER add a comment "// TODO: decouple" — that IS a violation entry
  C-RES-6  each resolution PR must pass all CI stages before the next opens
  C-RES-7  rollback a resolution PR if staging shows regressions — do not proceed


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNIVERSAL PACKAGE STRUCTURE  —  every language, every sub-package
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{lang}/{package-name}/
│
├── contracts/                       ← WRITTEN FIRST, before src/
│   ├── openapi/
│   │   ├── v1.yaml
│   │   └── v2.yaml                  ← only create when breaking change occurs
│   ├── graphql/
│   │   ├── v1.graphql
│   │   └── v2.graphql               ← only create when breaking change occurs
│   ├── proto/                       ← only create when grpc is chosen
│   │   └── v1/
│   ├── asyncapi/                    ← only create when async event exists
│   │   └── v1.yaml
│   └── changelog.md                 ← every contract change documented
│
├── src/
│   ├── api/                         ← ALL entry points — REST, GraphQL, gRPC, events
│   │   ├── rest/
│   │   │   ├── v1/
│   │   │   │   ├── router.{ext}     ← mounts routes, NO logic
│   │   │   │   └── handlers/        ← one file per resource, calls feature only
│   │   │   └── v2/                  ← only when v2 contract exists
│   │   ├── graphql/                 ← only when graphql is chosen
│   │   │   ├── v1/
│   │   │   │   ├── schema.{ext}
│   │   │   │   ├── resolvers/
│   │   │   │   └── dataloaders/
│   │   │   └── v2/                  ← only when v2 schema exists
│   │   ├── grpc/                    ← only when grpc is chosen
│   │   │   └── v1/
│   │   └── events/                  ← only when async events exist
│   │       ├── consumers/
│   │       └── publishers/
│   │
│   ├── features/                    ← vertical slices, ALL business logic here
│   │   └── {feature-name}/
│   │       ├── index.{ext}
│   │       ├── service.{ext}
│   │       ├── repository.{ext}
│   │       ├── types.{ext}
│   │       └── tests/
│   │           ├── unit/
│   │           ├── integration/     ← add when real infra available
│   │           └── contract/        ← add when contract is published
│   │
│   ├── infra/                       ← stage 1+ only
│   │   ├── adapters/                ← one per vendor, one per port
│   │   │   └── {vendor}/
│   │   ├── clients/                 ← generated — only when cross-package call exists
│   │   │   └── {upstream-service}/
│   │   │       └── v1/
│   │   └── tracing/
│   │       ├── tracer.{ext}
│   │       └── middleware.{ext}
│   │
│   └── shared/                      ← package-internal only
│       ├── types/
│       ├── errors/
│       ├── di/
│       └── utils/
│
├── database/
│   ├── migrations/                  ← MANDATORY from day one, even in stage 0
│   │   ├── 0001_init.sql
│   │   ├── 0001_init.rollback.sql
│   │   ├── 0002_{description}.sql
│   │   └── 0002_{description}.rollback.sql
│   ├── seeds/
│   └── schema.lock
│
├── tests/
│   ├── unit/                        ← MANDATORY from day one
│   ├── integration/                 ← add when infra is real (stage 1+)
│   ├── contract/                    ← add when contract is published (stage 2+)
│   ├── e2e/                         ← add when multi-service flows exist (stage 2+)
│   └── performance/                 ← add when SLOs are defined (stage 3+)
│
├── scripts/                         ← MINIMUM in stage 0: run.sh, migrate.sh, test.sh
│   ├── setup.sh                     ← add in stage 1
│   ├── run.sh                       ← REQUIRED stage 0+
│   ├── run-prod.sh                  ← add in stage 1
│   ├── stop.sh                      ← add in stage 1
│   ├── build.sh                     ← add in stage 1
│   ├── test.sh                      ← REQUIRED stage 0+
│   ├── test-unit.sh                 ← add in stage 1
│   ├── test-integration.sh          ← add in stage 1 (when integration/ exists)
│   ├── test-contract.sh             ← add in stage 2 (when contract/ exists)
│   ├── test-e2e.sh                  ← add in stage 2 (when e2e/ exists)
│   ├── test-performance.sh          ← add in stage 3
│   ├── migrate.sh                   ← REQUIRED stage 0+
│   ├── rollback-migration.sh        ← add in stage 1
│   ├── seed.sh                      ← add in stage 1
│   ├── generate.sh                  ← add in stage 2 (when clients/ exist)
│   ├── scan.sh                      ← add in stage 1
│   ├── health-check.sh              ← add in stage 1
│   ├── smoke-test.sh                ← add in stage 1
│   ├── deploy-docker.sh             ← add in stage 1
│   ├── deploy-k8s.sh                ← add in stage 3 (when k8s manifests exist)
│   ├── deploy-terraform.sh          ← add in stage 3 (when terraform exists)
│   ├── rollback-deploy.sh           ← add in stage 1
│   ├── logs.sh                      ← add in stage 1
│   ├── shell.sh                     ← add in stage 1
│   └── clean.sh                     ← add in stage 1
│
├── deploy/
│   ├── docker/                      ← add in stage 1
│   │   ├── docker-compose.dev.yaml
│   │   ├── docker-compose.test.yaml
│   │   └── docker-compose.prod.yaml
│   ├── kubernetes/                  ← stage 3+ only
│   │   ├── base/
│   │   └── overlays/
│   └── terraform/                   ← stage 3+ only
│
├── build/
│   ├── Dockerfile                   ← add in stage 1
│   ├── Dockerfile.dev               ← add in stage 1
│   └── Dockerfile.test              ← add in stage 1
│
├── .github/workflows/               ← add in stage 1
│   ├── ci.yaml
│   ├── cd-staging.yaml              ← add in stage 2
│   └── cd-production.yaml           ← add in stage 3
│
├── .env.example                     ← REQUIRED stage 0+
├── .package-meta.yaml               ← name, version, owned contracts, stage number
└── .port-registry                   ← stage 1+ only


LAYER CALL RULES  —  zero exceptions, enforced by linter
──────────────────────────────────────────────────────────────
  api/*          → features/*/index      ✓
  api/*          → infra/               ✗ NEVER
  api/*          → features/*/service   ✗ NEVER bypass index
  features/*/service → features/*/repository  ✓
  features/*/service → infra/adapters/  ✗ NEVER — use port interface via DI
  features/*/service → infra/clients/   ✓ (call other packages via generated client)
  features/*/repository → infra/adapters/    ✓ (via port interface)
  features/*/repository → features/*/service ✗ NEVER (circular)
  features/A/*   → features/B/*         ✗ NEVER — go through B/index
  features/A/*   → features/B/service   ✗ NEVER — go through B/index
  infra/*        → features/*           ✗ NEVER
  shared/*       → features/*           ✗ NEVER
  scripts/*      → src/*                ✗ NEVER — scripts call HTTP/CLI only


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APIS PACKAGE — GATEWAY + VERSIONING (strictest rules in the project)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

packages/apis/
├── contracts/
│
├── src/
│   ├── gateway/
│   │   ├── rest/
│   │   │   ├── v1/
│   │   │   │   └── router.{ext}
│   │   │   └── v2/
│   │   ├── graphql/
│   │   │   ├── schema/
│   │   │   │   ├── stitcher.{ext}
│   │   │   │   └── limits.yaml
│   │   │   ├── v1/
│   │   │   │   └── router.{ext}
│   │   │   └── v2/
│   │   ├── grpc/
│   │   │   └── v1/
│   │   ├── auth/
│   │   │   ├── validator.{ext}
│   │   │   └── middleware.{ext}
│   │   ├── ratelimit/
│   │   │   └── middleware.{ext}
│   │   ├── versioning/
│   │   │   ├── negotiator.{ext}
│   │   │   └── sunset-registry.yaml
│   │   └── tracing/
│   │       └── middleware.{ext}
│   │
│   └── adapters/
│       └── {package-name}/
│           ├── v1/
│           │   ├── client/
│           │   └── translator/
│           └── v2/
│               ├── client/
│               └── translator/
│
├── tests/
│   ├── contract/
│   ├── integration/
│   └── e2e/
│
└── scripts/


GATEWAY STRICT RULES
──────────────────────────────────────────────────────────────
  ALLOWED IN GATEWAY                  FORBIDDEN IN GATEWAY
  ──────────────────────────────      ────────────────────────────────
  route requests              ✓       business logic              ✗
  validate auth tokens        ✓       database access             ✗
  rate limiting               ✓       direct package src import   ✗
  trace context inject        ✓       data transformation         ✗
  schema stitching config     ✓       aggregating responses       ✗
  schema version negotiation  ✓       orchestrating services      ✗
  request/response logging    ✓       caching domain data         ✗
  sunset header injection     ✓       user session storage        ✗
  complexity/depth limiting   ✓       feature flags evaluation    ✗
  protocol translation        ✓       error message translation   ✗


API VERSIONING RULES
──────────────────────────────────────────────────────────────
  V-1   URL versioning mandatory: /api/v1/  /api/v2/  /graphql/v1
  V-2   version once published NEVER receives breaking changes
  V-3   breaking change = new version, always, no exceptions
  V-4   old version runs in parallel until sunset date passes
  V-5   sunset date minimum 6 months from deprecation notice
  V-6   Sunset + Deprecation HTTP headers on every deprecated response
  V-7   every version has its own adapter in apis/adapters/{pkg}/v{n}/
  V-8   contract in shared/contracts/{type}/{service}/v{n}
  V-9   .contract-lock pins exact version each package consumes
  V-10  no adapter references another adapter version — ever
  V-11  GraphQL: deprecated fields return data until sunset — no silent nulls
  V-12  sunset-registry.yaml checked in CI — expired + still-running = REJECT


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORT / ADAPTER PATTERN  —  mandatory for every infra dependency (stage 1+)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Adding any infra dependency?
│
├─ Port exists in shared/ports/?
│  ├─ YES → implement adapter in src/infra/adapters/{vendor}/
│  └─ NO  → define port in shared/ports/ FIRST — then implement
│
├─ Adapter rule: adapter file contains translation only
│  □ receives port interface call
│  □ translates to vendor SDK call
│  □ translates vendor response back to port interface type
│  □ wraps vendor call in child trace span
│  □ maps vendor errors to shared/errors/codes.yaml
│  □ ZERO conditional business logic in adapter
│
└─ DI wiring in src/shared/di/ selects adapter from env config
   └─ business logic sees ONLY the port interface — never the adapter type

VENDOR SWAP DECISION TREE
──────────────────────────────────────────────────────────────
  Want to swap vendor?
  │
  ├─ Service layer uses port interface only?
  │  ├─ YES → write new adapter, swap DI config, done
  │  └─ NO  → AX-11 violated — fix abstraction first, then swap
  │
  ├─ Schema-based → document store?
  │  → see VENDOR SWAP DATABASE MIGRATION section
  │
  ├─ Payment provider swap?
  │  PR 1: write new adapter implementing payment.interface
  │  PR 2: shadow mode — log new provider calls, use old for charges
  │  PR 3: canary — 5% traffic to new provider, monitor
  │  PR 4: full cutover after one billing cycle verified
  │  PR 5: remove old adapter, update .port-registry
  │
  └─ Same vendor, different region/instance?
     └─ env config change only — zero code change if port is clean

.port-registry format
──────────────────────────────────────────────────────────────
  package: python/auth
  port: database
  adapter: postgres
  version: "15.2"
  ---
  package: node/payments
  port: payment
  adapter: stripe
  version: "2024-06-20"
  ---
  RULES:
  □ every infra dependency has an entry — missing entry = CI fails
  □ adapter swap = update .port-registry in same PR


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATABASE MIGRATION RULES  —  STRICTEST RULES IN THE PROJECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Migrations are the permanent, immutable record of your schema's history.
They are not a convenience layer. They are law.

  MIGRATION RULE ZERO:
  If there is no migration file for a schema change, the schema change
  does not exist. It will be reverted. No exceptions, no emergency patches.

CORE MIGRATION RULES
──────────────────────────────────────────────────────────────

  DB-1   NEVER touch a database manually — ever, in any environment
         including local dev, staging, and hotfix scenarios
  DB-2   EVERY schema change is a numbered migration file — zero exceptions
  DB-3   migration files are IMMUTABLE once merged to main
         editing a merged migration = immediate PR reject + incident
  DB-4   filename: {NNNN}_{description}.sql  zero-padded 4 digits
  DB-5   every migration has a rollback file: {NNNN}_{description}.rollback.sql
         no rollback file = PR blocked, no merge, no exceptions
  DB-6   migrations run via migrate.sh — BEFORE application starts
         application start without successful migration = blocked
  DB-7   schema.lock records last applied migration number — committed to repo
         schema.lock out of sync with migration files = CI fails
  DB-8   CI runs full migration suite on clean db on every pipeline
  DB-9   no application code references a column/table removed in migration
  DB-10  no cross-package foreign keys — ever, in any form
  DB-11  enums stored as varchar + CHECK constraint — never db enum type
  DB-12  no stored procedures, triggers, or views — logic in application only
  DB-13  every table: id, created_at, updated_at mandatory — no exceptions
  DB-14  soft deletes: deleted_at column — never hard delete by default
         if hard delete is required, justify it in the migration header
  DB-15  every foreign key is explicit with ON DELETE behaviour declared
  DB-16  every foreign key has an index — missing index = CI blocks
  DB-17  no nullable column without documented reason in migration header

MIGRATION DISCIPLINE RULES
──────────────────────────────────────────────────────────────

  DB-18  migration file size limit: a migration that changes more than 3
         tables or adds more than 5 columns MUST be split into smaller
         migrations — large migrations cannot be rolled back cleanly
  DB-19  every migration is tested on a clean database in CI before merge
         — not on an existing database with accumulated state
  DB-20  every migration is tested with its rollback file in CI:
         apply → verify → rollback → verify — both directions must pass
  DB-21  production migration must be run during low-traffic window if it:
         □ locks a table
         □ backfills > 10,000 rows
         □ adds a non-nullable column to an existing table
         □ rebuilds an index
  DB-22  for table locks or heavy migrations: use a migration readiness
         checklist in the PR body:
         □ estimated lock duration
         □ estimated row count affected
         □ fallback plan if migration hangs
         □ rollback procedure documented
         □ team notified of maintenance window
  DB-23  never use a migration to seed production data — seeds go in
         database/seeds/ and are NEVER run via migrate.sh in production
  DB-24  migration depends_on field must be accurate —
         if migration 0005 depends on 0004, that is declared in the header
         and CI validates it — cannot apply 0005 without 0004
  DB-25  every index name must be explicit and unique:
         CREATE INDEX idx_{table}_{column(s)} ON ...
         never rely on database-generated index names

MIGRATION FILE HEADER (mandatory on every file)
──────────────────────────────────────────────────────────────

  -- migration:    0004
  -- description:  add payment_status index to orders
  -- author:       {name}
  -- date:         {ISO date}
  -- depends_on:   0003
  -- reversible:   YES | NO (if NO, explain why in reason)
  -- lock_risk:    LOW | MEDIUM | HIGH (HIGH requires maintenance window)
  -- rows_affected: estimated count or "schema only"
  -- reason:       query performance — orders by status scans full table

  BEGIN;
    ... migration SQL ...
  COMMIT;

SAFE DESTRUCTIVE MIGRATION  —  never in a single PR
──────────────────────────────────────────────────────────────

  Removing column/table?
  │
  PR 1: add comment DEPRECATED to column in migration
        ensure no new writes to column
        add alert: fire if column is read
  │
  PR 2 (after 1 full release cycle, verified):
        remove all reads from application code
  │
  PR 3 (after staging verified clean):
        migration: DROP COLUMN
        rollback file must exist
  │
  └─ three PRs minimum — never collapse into one

COLUMN RENAME  —  never rename in one step
──────────────────────────────────────────────────────────────

  PR 1: add new column with new name
  PR 2: dual-write both columns in application
  PR 3: backfill old → new (migration + verify row count matches)
  PR 4: remove reads of old column
  PR 5: DROP old column (migration with rollback)

VENDOR SWAP DATABASE MIGRATION
──────────────────────────────────────────────────────────────

  Step 1: write new adapter implementing database.interface
  Step 2: write {NNNN}_vendor_migration_{from}_{to}.sh in database/migrations/
  Step 3: shadow write — write to both old and new, read from old
  Step 4: validation job — compare old vs new row by row, log diffs
  Step 5: feature-flag flip — read from new (5% canary)
  Step 6: scale to 100% reads from new, monitor one full release cycle
  Step 7: remove shadow write + old adapter
  Step 8: update .port-registry
  Rule:   each step is a separate PR — never combine


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRACING RULES  —  FIRST-CLASS CITIZEN, MANDATORY FROM DAY ONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tracing is not an observability feature you add when the system is slow.
Tracing is the primary diagnostic instrument of this architecture.
A feature without tracing is not done. A deployment without traces
flowing to the collector is a failed deployment — rolled back immediately.

  TRACING RULE ZERO:
  If a trace is not flowing, the system is dark. A dark system is not
  running in production. No production deploy completes without
  trace-check.sh returning 0.

CORE TRACING RULES
──────────────────────────────────────────────────────────────

  T-1   OTEL tracer initialised BEFORE any other startup code — first line
  T-2   every inbound request/event creates a ROOT span immediately
        no code executes before the root span is open
  T-3   every outbound call propagates W3C traceparent — no exceptions
        calls without traceparent propagation = AX-8 violation
  T-4   every span MUST carry ALL of these attributes — missing = CI fails:
          service.name       = {lang}.{package-name}
          service.version    = {semver}
          feature.name       = {feature-name}
          api.version        = v1|v2
          deployment.env     = prod|staging|dev
          host.name          = {hostname}
  T-5   GraphQL resolvers: span per resolver, query hash in span attrs
  T-6   every error: span.record_error(err) with full stacktrace
        span status set to ERROR — not just logged
  T-7   span names follow shared/tracing/conventions.md exactly (stage 2+)
        at stage 0/1: use {lang}.{package}.{feature}.{operation}
  T-8   ZERO business logic gated on trace context presence
        if traceparent is absent, the request still processes normally
  T-9   queue messages carry traceparent in message attributes — always
  T-10  every adapter wraps vendor call in child span
  T-11  database queries auto-instrumented via adapter middleware
  T-12  W3C traceparent only — no custom propagation formats
  T-13  GraphQL N+1 queries surface in traces — dataloader miss = span event
  T-14  span duration SLO thresholds declared per endpoint (stage 3+)

TRACING DISCIPLINE RULES
──────────────────────────────────────────────────────────────

  T-15  trace-check.sh is part of smoke-test.sh — always
        smoke-test failure includes trace absence as a failure reason
  T-16  trace context is propagated even in background jobs, cron tasks,
        and CLI commands — root span created with synthetic trace ID
  T-17  no span is silently swallowed — every span.end() is called
        in a finally block (or language equivalent) — never conditional
  T-18  span names are STABLE — changing a span name is a breaking change
        to dashboards and alerts — requires the same PR process as a
        contract breaking change (new name added, old deprecated, then removed)
  T-19  every cross-package boundary creates a NEW span on the receiving side
        the receiving span links to the parent via W3C traceparent
        — never reuse the sending span across the boundary
  T-20  sampling strategy is declared, not random:
        stage 0/1: 100% sampling (all traces captured)
        stage 2:   100% on error paths, configurable on success paths
        stage 3:   defined in shared/tracing/sampling-rules.yaml,
                   head-based + tail-based as needed
  T-21  sensitive data NEVER appears in span attributes:
        no PII, no passwords, no tokens, no card numbers, no SSNs
        use hashed or truncated identifiers where identity is needed
  T-22  every PR that adds a new outbound call must include the span
        for that call — it is not a separate follow-up ticket
  T-23  every PR that adds a new async consumer must include the span
        extraction from the message headers — same PR, not later
  T-24  trace-check.sh validates that at least one trace with the correct
        service.name attribute has arrived at the collector in the last
        60 seconds — binary pass/fail

TRACING VIOLATION RESPONSES
──────────────────────────────────────────────────────────────

  Missing root span:         → P1 — no deploy until fixed
  Missing traceparent prop:  → P1 — treated as CoA coupling violation
  Missing required attrs:    → CI block — PR cannot merge
  Missing error recording:   → P2 — next sprint fix
  PII in span attrs:         → P0 immediate — security incident protocol
  trace-check failing prod:  → auto-rollback triggered
  Span name changed silently: → P1 — all dependent dashboards invalidated

TRACING IN STAGE 0 (minimum viable)
──────────────────────────────────────────────────────────────

  Even in stage 0, these are non-negotiable:
  □ OTEL SDK initialised at startup (T-1)
  □ root span created for every inbound request (T-2)
  □ every error recorded on the span (T-6)
  □ span attributes: service.name, deployment.env at minimum
  □ no business logic gated on trace context (T-8)

  At stage 0, exporting to a local collector (or stdout) is acceptable.
  OTEL SDK with stdout exporter = valid. No exporter at all = invalid.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPTS — STRICT RULES (every package, every language)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EVERY script must begin with:
  #!/usr/bin/env bash
  set -euo pipefail
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  PACKAGE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

EVERY script must declare and validate env vars before doing anything:
  : "${SERVICE_NAME:?SERVICE_NAME is required}"
  : "${DEPLOY_ENV:?DEPLOY_ENV must be prod|staging|dev}"

SCRIPT RULES
──────────────────────────────────────────────────────────────
  S-1   set -euo pipefail on every script — no exceptions
  S-2   every required env var validated at top with :? — fail fast
  S-3   scripts NEVER source another package's scripts
  S-4   scripts call other packages via HTTP/curl/grpcurl only
  S-5   scripts contain ZERO business logic — orchestration only
  S-6   scripts log to stderr, data output to stdout
  S-7   scripts return 0 = success, non-zero = failure — always
  S-8   every script has a --help / -h flag that prints usage
  S-9   destructive scripts (clean, delete, rollback) require
        explicit confirmation: CONFIRM=yes env var or --yes flag
  S-10  scripts propagate traceparent env var in every curl call
  S-11  shellcheck must pass with zero warnings on every script
  S-12  scripts never hardcode hostnames, ports, credentials

MINIMUM SCRIPTS FOR STAGE 0
──────────────────────────────────────────────────────────────
  run.sh       — start the package in dev mode
  migrate.sh   — run pending migrations
  test.sh      — run unit tests

All other scripts are added when their operation becomes real.

SCRIPT REFERENCE (full set — generate when needed per stage)
──────────────────────────────────────────────────────────────

  setup.sh (stage 1+)
    □ install language dependencies
    □ generate clients from shared/contracts/ (calls generate.sh)
    □ create .env from .env.example if not exists
    □ run database migrations (calls migrate.sh)
    □ idempotent — safe to run multiple times

  run.sh / run-prod.sh
    □ validate env vars
    □ call migrate.sh first — always
    □ start application

  build.sh (stage 1+)
    □ compile / build production artifact
    □ run scan.sh first — build fails if scan fails
    □ build docker image tagged :{git-sha}
    □ output: image sha to stdout for CD pipeline consumption

  test.sh
    □ calls test-unit.sh → test-integration.sh → test-contract.sh
    □ exits non-zero if any suite fails
    □ outputs coverage report

  scan.sh (stage 1+)
    □ lint (zero warnings)
    □ type-check (strict)
    □ security scan (SAST)
    □ secret scan (gitleaks)
    □ dependency CVE audit
    □ coupling check (no cross-package imports)
    □ contract lint
    □ port-registry sync check
    □ schema.lock consistency
    □ exits non-zero if ANY check fails

  migrate.sh
    □ check schema.lock
    □ run pending migrations in transaction
    □ rollback all if any migration fails
    □ update schema.lock on success
    □ exit non-zero on any failure — prevents app start
    □ idempotent — no-op if already up to date

  generate.sh (stage 2+)
    □ pull latest contracts from shared/contracts/
    □ regenerate src/infra/clients/ from contracts
    □ regenerate types from GraphQL SDL
    □ NEVER edit generated files manually — they are overwritten

  deploy-docker.sh (stage 1+)
    □ accept: IMAGE_SHA, DEPLOY_ENV
    □ call migrate.sh before starting containers
    □ use docker-compose with correct overlay for env
    □ call smoke-test.sh after deploy
    □ rollback on smoke-test failure

  deploy-k8s.sh (stage 3+)
    □ accept: IMAGE_SHA, NAMESPACE, DEPLOY_ENV
    □ apply kustomize overlay for env
    □ wait for rollout: kubectl rollout status
    □ call smoke-test.sh after rollout
    □ kubectl rollout undo on smoke-test failure

  rollback-deploy.sh (stage 1+)
    □ accept: TARGET_SHA
    □ redeploy image at TARGET_SHA
    □ call rollback-migration.sh if schema changed

  health-check.sh (stage 1+)
    □ call /health or /healthz endpoint
    □ return 0 = healthy, 1 = unhealthy
    □ timeout: 5 seconds max

  smoke-test.sh (stage 1+)
    □ call health-check.sh
    □ call one read endpoint per feature
    □ call trace-check.sh — MANDATORY — traces must flow
    □ return 0 = ok, non-zero = fail

  trace-check.sh (stage 1+)
    □ query OTEL collector for traces with this service.name
    □ verify at least one trace in last 60 seconds
    □ return 0 = traces flowing, 1 = dark
    □ called from smoke-test.sh — never optional


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TESTING RULES  —  per package, per language
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UNIT TESTS (stage 0+)
  □ coverage minimum 80% — never lower, no exceptions
  □ zero network, zero disk, zero real db
  □ all infra via port interface mocks
  □ all external API calls via generated client mocks
  □ must complete < 2 minutes
  □ zero flaky tests — flaky test = P0 fix before any other work
  □ GraphQL: test resolver logic with mocked feature index
  □ test every error path — not just happy path

CONTRACT TESTS (stage 2+)
  □ validate own published contracts are fully implemented
  □ validate consumed contracts match .contract-lock versions
  □ consumer-driven contract tests via pact or equivalent
  □ breaking change detection: oasdiff (REST) / buf breaking (proto)
    / graphql-inspector (GraphQL) — runs on every PR
  □ contract test failure = no merge, no exceptions

INTEGRATION TESTS (stage 1+)
  □ spin up real infra via docker-compose.test.yaml in CI
  □ each test suite gets a CLEAN database — no shared state
  □ run migrations on clean db before every integration suite
  □ test every adapter against real vendor
  □ test every feature entry point end-to-end within the package
  □ teardown all infra after — no state leaks
  □ GraphQL: test full query execution with real resolvers + real db

E2E TESTS (stage 2+)
  □ test full user-facing flows
  □ isolated — no dependency on other packages running
  □ mock other package APIs via recorded contract responses

PERFORMANCE TESTS (stage 3+)
  □ baseline thresholds declared in tests/performance/thresholds.yaml
  □ p99 latency threshold per endpoint
  □ CI fails if p99 exceeds threshold in CD (not required on PR)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CI / CD PIPELINES  —  per package, per stage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CI STAGE 0 (minimum — local only, no pipeline yet)
──────────────────────────────────────────────────────────────
  Run manually via test.sh:
  □ unit tests pass
  □ migrate.sh passes on clean db

CI STAGE 1 (first pipeline — all stages required)
──────────────────────────────────────────────────────────────
  stage 1: STATIC ANALYSIS          (calls scan.sh)
    □ lint — zero warnings
    □ type-check — strict mode
    □ CVE audit — no known high/critical
    □ secret scan — gitleaks, zero findings
    □ coupling check — no cross-package imports
    □ contract lint — own contracts valid
    □ port-registry sync
    □ schema.lock consistency

  stage 2: UNIT TESTS
    □ coverage ≥ 80%
    □ < 2 minutes total

  stage 3: INTEGRATION TESTS
    □ clean infra spun up
    □ migrations run on clean db
    □ infra torn down after

  stage 4: SECURITY SCAN
    □ SAST — semgrep or language equivalent
    □ container image scan — trivy
    □ OWASP dependency check

  stage 5: BUILD
    □ production artifact built
    □ image tagged :{git-sha}
    □ image pushed to registry

CI STAGE 2+ (additional stages added)
──────────────────────────────────────────────────────────────
  stage 3 (after unit): CONTRACT TESTS
    □ own contracts implemented correctly
    □ consumed contracts match .contract-lock
    □ pact consumer tests pass
    □ graphql-inspector breaking change check
    □ sunset-registry expiry check

CD STAGING (stage 2+ — merge to main)
──────────────────────────────────────────────────────────────
  1. verify CI passed on same commit sha
  2. call migrate.sh against staging db
  3. call deploy-docker.sh or deploy-k8s.sh
  4. call smoke-test.sh (includes trace-check.sh)
  5. call test-contract.sh against live staging
  6. verify traces in collector — if dark, rollback immediately
  7. notify with trace link on pass, error details on fail

CD PRODUCTION (stage 3+ — git tag v* only)
──────────────────────────────────────────────────────────────
  1. verify CD staging passed on same sha
  2. require 2 PR approvals — enforced, no bypass
  3. pre-flight:
     □ all consumers on compatible contract versions
     □ no expired versions still in sunset-registry
     □ schema.lock matches migration files
     □ trace-check.sh passes on staging
  4. call migrate.sh with auto-rollback on failure
  5. blue-green or canary deploy — never direct cutover
  6. smoke-test.sh on new instances before traffic shift
     □ trace-check.sh is part of smoke-test — if dark, rollback
  7. traffic: 5% → 25% → 100% with health-check gate at each step
  8. monitor error rate + p99 latency for 15 min at each step
  9. auto-rollback if error rate > threshold OR trace-check fails
  10. tag image :latest ONLY after 100% traffic stable for 15 min


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MULTI SUB-PACKAGE RULES  —  all languages
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

packages/{lang}/
├── {sub-package-a}/
├── {sub-package-b}/
└── {lang}-shared/                   ← language-internal only, zero runtime deps
    ├── types/
    └── utils/

Sub-package A needs sub-package B (same language)?
│
├─ TYPE only, used only within this language?
│  └─ {lang}-shared/types/ via index export only
│
├─ RUNTIME CALL?
│  └─ full package boundary — always
│     └─ contract in shared/contracts/ + generated client
│
├─ PURE UTIL (no IO, no business logic)?
│  └─ language-specific only?
│     ├─ YES → {lang}-shared/utils/
│     └─ NO  → evaluate shared/ at project root
│
├─ DATABASE?
│  └─ each sub-package owns its own db/schema — always
│
├─ EVENT?
│  └─ schema in shared/events/ + publish/subscribe via broker only
│
└─ GraphQL schema overlap?
   └─ schemas federated via apis/gateway/graphql/stitcher — never merged in src


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE-SPECIFIC ENFORCEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PYTHON
──────────────────────────────────────────────────────────────
  package mgmt:   each sub-package = own pyproject.toml + src/ layout
  lint:           ruff --select ALL (zero warnings)
  types:          mypy --strict (zero errors)
  security:       bandit -ll + safety check
  forbidden:      ruff rule to ban cross-package imports
  test:           pytest + pytest-cov, minimum 80%
  contracts REST: openapi-python-client generated into src/infra/clients/
  contracts GQL:  ariadne-codegen from shared/contracts/graphql/
  contracts proto: grpcio-tools + buf generate
  OTEL:           opentelemetry-sdk + opentelemetry-instrumentation-fastapi
                  + opentelemetry-instrumentation-sqlalchemy
  contract tests: schemathesis (REST) + pytest-gql (GraphQL)
  migrations:     alembic (managed) or raw SQL runner via migrate.sh
  graphql server: strawberry or ariadne — schema loaded from SDL file

RUST
──────────────────────────────────────────────────────────────
  package mgmt:   each sub-package = own Cargo.toml in workspace
                  workspace members NEVER depend on each other
  lint:           clippy --deny warnings (zero warnings)
  types:          no unsafe without documented justification
  security:       cargo audit + cargo deny
  test:           cargo test + cargo tarpaulin (coverage ≥ 80%)
  contracts REST: openapi-generator → src/infra/clients/
  contracts GQL:  cynic or graphql-client codegen
  contracts proto: tonic + buf generate
  OTEL:           opentelemetry + tracing + tracing-opentelemetry
  migrations:     sqlx migrate (preferred) or refinery
  graphql server: async-graphql — schema-first via SDL

GO
──────────────────────────────────────────────────────────────
  package mgmt:   each sub-package = own go.mod (separate module)
                  replace directives NEVER committed to main
  lint:           golangci-lint strict config (zero warnings)
  types:          go vet + staticcheck
  security:       govulncheck + gosec
  forbidden:      depguard — cross-module imports blocked
  test:           go test ./... + coverage ≥ 80%
  contracts REST: oapi-codegen into src/infra/clients/
  contracts GQL:  gqlgen (schema-first from SDL)
  contracts proto: buf generate + connectrpc
  OTEL:           go.opentelemetry.io/otel + contrib instrumentation
  migrations:     golang-migrate (raw SQL files)
  graphql server: gqlgen — schema loaded from contracts/graphql/v{n}.graphql

NODE / TYPESCRIPT
──────────────────────────────────────────────────────────────
  package mgmt:   each sub-package = own package.json
                  workspaces for build tooling ONLY — no runtime imports
  lint:           eslint --max-warnings 0 + prettier
  types:          tsc --strict (no any, no ts-ignore without justification)
  security:       npm audit --audit-level=high
  forbidden:      eslint no-restricted-imports (cross-package banned)
  test:           vitest (preferred) or jest, coverage ≥ 80%
  contracts REST: openapi-typescript-codegen into src/infra/clients/
  contracts GQL:  graphql-codegen from shared/contracts/graphql/
  contracts proto: buf generate + @connectrpc/connect
  OTEL:           @opentelemetry/sdk-node + auto-instrumentations-node
  contract tests: openapi-fetch + MSW (REST) / graphql-request + MSW (GQL)
  migrations:     db-migrate or knex migrate (raw SQL preferred)
  graphql server: apollo-server or graphql-yoga — schema-first via SDL

JAVA
──────────────────────────────────────────────────────────────
  package mgmt:   each sub-package = own maven module or gradle subproject
  lint:           checkstyle + pmd + spotbugs (zero violations)
  types:          no raw types, no unchecked casts without justification
  security:       owasp dependency-check
  forbidden:      ArchUnit tests — no cross-module type references (automated)
  test:           junit5 + jacoco (coverage ≥ 80%)
  contracts REST: openapi-generator-maven-plugin into infra/clients/
  contracts GQL:  graphql-java-codegen from SDL
  contracts proto: protobuf-maven-plugin + grpc-java
  OTEL:           opentelemetry-java-instrumentation agent (zero-code)
  migrations:     flyway (preferred) or liquibase — SQL files only
  graphql server: graphql-java — schema-first, SDL loaded at startup

SHELL SCRIPTS
──────────────────────────────────────────────────────────────
  every script:   set -euo pipefail as first executable line
  lint:           shellcheck — zero warnings
  forbidden:      source/. another package's scripts
  API calls:      curl or grpcurl only — with traceparent header
  GraphQL calls:  curl POST with application/json — no special client
  logic:          zero business logic — orchestration and ops only
  env vars:       declared and :? validated at top of every script
  secrets:        read from env only — never hardcoded, never logged
  idempotency:    setup.sh and migrate.sh must be idempotent


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOCKER COMPOSE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  □ every service declares healthcheck with test, interval, timeout, retries
  □ depends_on uses condition: service_healthy — never bare depends_on
  □ no hardcoded passwords — all via env vars, all in .env.example
  □ each package has its OWN db service — never share db container
  □ volumes are named — never anonymous
  □ networks are explicit per package — never shared default bridge
  □ resource limits declared: mem_limit, cpus on every service
  □ DB_ADAPTER env var controls which db image is used
  □ adapter swap = change DB_ADAPTER + swap adapter class — zero app code change

  DB_ADAPTER pattern in docker-compose:
  ─────────────────────────────────────
  # .env
  DB_ADAPTER=postgres
  DB_VERSION=15

  services:
    db:
      image: ${DB_ADAPTER:-postgres}:${DB_VERSION:-15}
      healthcheck:
        test: ["CMD", "pg_isready"]
      volumes:
        - db-data:/var/lib/postgresql/data
      networks:
        - {package}-internal


KUBERNETES RULES (stage 3+ only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  □ readinessProbe + livenessProbe on every deployment
  □ resource requests AND limits on every container
  □ securityContext.runAsNonRoot: true on every deployment
  □ secrets from vault or sealed-secrets — never plaintext yaml
  □ HPA on every production service
  □ PodDisruptionBudget on every stateful service
  □ each package deployed to its own namespace
  □ NetworkPolicy: deny-all ingress + egress by default
  □ image pinned to sha256 digest in production — never :latest
  □ kustomize overlays for staging vs production differences only


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MIGRATION TO THIS STRUCTURE  —  existing projects
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 0 — AUDIT  (touch zero code)
──────────────────────────────────────────────────────────────
  □ determine current stage of each existing package
  □ write stage into each .package-meta.yaml
  □ generate coupling-map.md entries for:
      - every cross-package import
      - every shared database/schema/table
      - every missing contract (REST, GraphQL, event)
      - every missing migration file (manual schema changes)
      - every missing port abstraction (direct vendor calls)
      - every missing trace instrumentation
      - every missing script
      - every GraphQL schema not in shared/contracts/graphql/
  □ severity per entry: CoI > CoV > CoA > CoE > CoM
  □ assign: owner, target phase, target PR number
  □ commit coupling-map.md to repo root
  □ add CI check: new entries without phase plan = pipeline fails
  □ DO NOT write a single line of implementation code in phase 0
  □ DO NOT generate any files speculatively in phase 0 —
    only document what is missing

PHASE 1 — CONTRACTS AND PORTS  (no feature work during this phase)
──────────────────────────────────────────────────────────────
  □ write all missing REST contracts into shared/contracts/openapi/
    ONLY for cross-package calls that currently exist
  □ write all missing GraphQL schemas into shared/contracts/graphql/
    ONLY for cross-package calls that currently exist
  □ write all missing event schemas into shared/contracts/asyncapi/
    ONLY for real async calls that currently exist
  □ write all missing port interfaces into shared/ports/
    ONLY for vendors actually used today
  □ write all missing event definitions into shared/events/
  □ write 0001_init.sql capturing CURRENT schema state for every package
  □ write 0001_init.rollback.sql for every init migration
  □ create schema.lock with current applied version
  □ create .contract-lock pinning current versions (stage 2+)
  □ create .port-registry listing all current infra dependencies
  □ review and merge — zero implementation changes in phase 1
  □ no feature PRs until phase 1 is fully merged

PHASE 2 — STRANGLE  (one violation per PR, never more)
──────────────────────────────────────────────────────────────
  Each PR: deployed to staging + verified before next PR opens

  Cross-package import violation (CoI):
    PR 1: wrap function/class behind HTTP or GraphQL handler
    PR 2: generate client from shared/contracts/ (calls generate.sh)
    PR 3: replace import with generated client call + add trace span
    PR 4: remove original import
    PR 5: update coupling-map.md (remove entry)

  Shared database violation (CoI):
    PR 1: add event publisher to table owner (event schema first)
    PR 2: add subscriber + own isolated db to consumer
    PR 3: dual-write old shared db + publish events — verify staging
    PR 4: flip consumer reads to own db
    PR 5: remove shared db access from consumer
    PR 6: update .port-registry + coupling-map.md

  Missing port abstraction (CoA):
    PR 1: define port interface in shared/ports/ if missing
    PR 2: write adapter implementing interface exactly
    PR 3: replace direct vendor call with port via DI
    PR 4: update .port-registry
    PR 5: update coupling-map.md

  Missing trace instrumentation:
    PR 1: add OTEL init to startup (before everything else)
    PR 2: add tracing middleware to api/ entry points
    PR 3: add context propagation to all infra/clients/ calls
    PR 4: add span attrs per T-4 rules
    PR 5: add trace-check.sh to smoke-test.sh
    RULE: tracing PRs are P0 — nothing blocks them, they block everything else

  Missing migration files:
    PR 1: write 0001_init.sql from current schema
    PR 2: write rollback file + create schema.lock
    PR 3: add migrate.sh to scripts/
    PR 4: add CI migration stage (clean db test)

  Missing scripts:
    PR 1: add minimum scripts for current stage (run.sh, migrate.sh, test.sh)
    PR 2: add remaining stage scripts
    PR 3: add shellcheck to CI scan stage

PHASE 3 — HARDEN
──────────────────────────────────────────────────────────────
  □ enable linter rules blocking all cross-package imports
  □ add contract breaking-change check to every CI pipeline
  □ add graphql-inspector to every GraphQL package CI
  □ coupling-map.md violation count check in CI (must be 0 on main)
  □ schema.lock consistency check in CI
  □ .port-registry sync check in CI
  □ .contract-lock sync check in CI
  □ sunset-registry expiry check in CI
  □ shellcheck on all scripts in CI
  □ trace-check.sh in smoke-test and CD gate
  □ migration rollback test in CI (apply + rollback both directions)
  □ migration lock_risk: HIGH triggers maintenance window reminder in CI
  □ phase complete when coupling-map.md has zero entries
  □ phase complete when all CI checks are green on main

MIGRATION NON-NEGOTIABLES
──────────────────────────────────────────────────────────────
  □ NEVER break a running production system
  □ NEVER combine more than one violation in a single PR
  □ NEVER skip the contract step to save time
  □ NEVER remove dual-write before consumer db is verified stable
  □ NEVER write a migration without a rollback file
  □ NEVER merge a PR adding a new coupling not in coupling-map.md
  □ NEVER proceed to next phase while current phase has open PRs
  □ NEVER rename a column in a single migration — add/dual-write/remove
  □ tracing must be instrumented before phase 2 ends — not deferred
  □ scripts must be added before phase 2 ends — CI must call them
  □ NEVER generate files speculatively during migration — only what is needed


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR REJECTION CHECKLIST  —  [auto] = enforced by CI, [manual] = reviewer check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [auto]   packages/* importing another packages/* source?                REJECT
  [auto]   new shared db connection across packages?                      REJECT
  [auto]   cross-package call missing trace context propagation?          REJECT
  [auto]   contract added inside package not in shared/?                  REJECT
  [auto]   GraphQL schema modified not in shared/contracts/graphql/?      REJECT
  [auto]   business logic in apis/gateway/?                               REJECT
  [auto]   db access in apis/gateway/?                                    REJECT
  [auto]   handler calling repository directly (skipping service)?        REJECT
  [auto]   infra/ importing from features/?                               REJECT
  [auto]   feature importing another feature's non-index file?            REJECT
  [auto]   span missing required attrs from T-4?                          REJECT
  [auto]   contract changed without version bump in .contract-lock?       REJECT
  [auto]   breaking change applied to existing version?                   REJECT
  [auto]   breaking GraphQL change applied to existing version?           REJECT
  [auto]   sunset date not set for deprecated version?                    REJECT
  [auto]   sunset date expired but version still serving?                 REJECT
  [auto]   .port-registry out of sync with actual adapters?               REJECT
  [auto]   schema.lock out of sync with migration files?                  REJECT
  [auto]   migration file modified after merge to main?                   REJECT
  [auto]   migration missing rollback file (reversible: YES)?             REJECT
  [auto]   migration missing header block?                                REJECT
  [auto]   migration not wrapped in BEGIN/COMMIT?                         REJECT
  [auto]   migration missing lock_risk field?                             REJECT
  [auto]   migration missing rows_affected field?                         REJECT
  [auto]   migration rollback not tested in CI (both directions)?         REJECT
  [auto]   new coupling in coupling-map.md without phase plan?            REJECT
  [auto]   linter warnings > 0?                                           REJECT
  [auto]   type-check errors > 0?                                         REJECT
  [auto]   test coverage below threshold?                                 REJECT
  [auto]   known high/critical CVE in dependencies?                       REJECT
  [auto]   secret detected by gitleaks?                                   REJECT
  [auto]   shellcheck warnings on any script?                             REJECT
  [auto]   script missing set -euo pipefail?                              REJECT
  [auto]   script missing env var validation?                             REJECT
  [auto]   generated client file manually edited?                         REJECT
  [auto]   GraphQL resolver not using dataloader for relations?           REJECT
  [auto]   graphql-inspector breaking change detected?                    REJECT
  [auto]   src/ file written before contracts/ file merged?               REJECT
  [auto]   PII detected in span attributes?                               REJECT — security incident
  [auto]   cross-boundary call missing new span on receiving side?        REJECT
  [auto]   new file created at a stage where it is not yet required?      REJECT — lazy generation violation
  [auto]   .package-meta.yaml missing or missing stage field?             REJECT
  [auto]   stage promotion PR contains feature code?                      REJECT
  [auto]   coupling-map.md has entries on main?                           REJECT

  [manual] PR touches > 3 files outside one package?                      REJECT — split
  [manual] PR fixes multiple unrelated violations?                        REJECT — split
  [manual] adapter contains conditional business logic?                   REJECT
  [manual] repository method contains conditional logic beyond query?     REJECT
  [manual] script calls another package's scripts directly?               REJECT
  [manual] script contains business logic?                                REJECT
  [manual] GraphQL mutation returns Boolean instead of mutated type?      REJECT
  [manual] GraphQL subscription uses polling instead of event?            REJECT
  [manual] feature implemented before contract review merged?             REJECT
  [manual] deploy-*.sh missing migrate.sh call before start?              REJECT
  [manual] smoke-test.sh missing trace-check.sh call?                    REJECT
  [manual] migration lock_risk: HIGH without maintenance window note?     REJECT
  [manual] migration changes > 3 tables or > 5 columns in single file?   REJECT — split migration
  [manual] tracing added AFTER feature code in same PR?                   REJECT — tracing must be in same PR
  [manual] span name changed without deprecation notice?                  REJECT
  [manual] new file generated that does not have a current forcing function? REJECT — lazy generation violation
  [manual] stage 0 package with port interfaces or adapters?              REJECT — premature
  [manual] stage 0 package with kubernetes manifests?                     REJECT — premature
  [manual] stage 0 package with v2 contracts?                             REJECT — premature


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUICK REFERENCE — WHAT TO BUILD AT EACH STAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  STAGE 0 — PROTOTYPE
  ────────────────────
  ✓ contracts/ (chosen type only)
  ✓ src/api/ + src/features/
  ✓ database/migrations/0001_init.sql + rollback
  ✓ database/schema.lock
  ✓ tests/unit/
  ✓ scripts/run.sh, migrate.sh, test.sh
  ✓ .env.example
  ✓ .package-meta.yaml (stage: 0)
  ✓ OTEL root span (stdout exporter acceptable)
  ✗ everything else

  STAGE 1 — SINGLE PACKAGE PRODUCTION
  ─────────────────────────────────────
  + src/infra/adapters/ + port interfaces
  + full scripts/ set
  + tests/integration/
  + CI pipeline (scan, unit, integration, build)
  + deploy/docker/
  + build/Dockerfile*
  + OTEL full attrs (T-4) + tracing middleware
  + trace-check.sh in smoke-test.sh
  + .port-registry
  + coupling-map.md (empty but present and CI-checked)
  ✗ shared/contracts/ (not yet — no second package)
  ✗ kubernetes/
  ✗ terraform/

  STAGE 2 — MULTI-PACKAGE
  ─────────────────────────
  + shared/contracts/{type}/{service}/v1.*
  + src/infra/clients/{service}/v1/ (generated)
  + tests/contract/
  + tests/e2e/
  + .contract-lock
  + shared/errors/codes.yaml
  + shared/tracing/conventions.md
  + CD staging pipeline
  + apis/ gateway package (if external clients need it)
  ✗ kubernetes/ (not yet)
  ✗ performance tests (not yet)

  STAGE 3 — SCALED PRODUCTION
  ─────────────────────────────
  + deploy/kubernetes/
  + deploy/terraform/
  + tests/performance/
  + CD production pipeline (blue-green/canary)
  + shared/tracing/sampling-rules.yaml
  + span SLO thresholds per endpoint
  + sunset-registry.yaml + CI expiry check
  + HPA, PDB, NetworkPolicy


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
.package-meta.yaml FORMAT (REQUIRED on every package)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  name: python/auth
  version: 1.4.2
  stage: 1                           ← 0 | 1 | 2 | 3
  owned_contracts:
    - shared/contracts/openapi/auth/v1.yaml
  owned_db: postgres/auth_db
  owned_events: []
  port_registry: .port-registry
  last_promotion: 2025-03-12         ← date of last stage promotion PR
  promotion_pr: PR#102
  tracing_status: instrumented       ← instrumented | partial | missing
  coupling_violations: 0             ← must be 0 on main


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE PRECEDENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When two rules appear to conflict, the following order resolves it:

  1. Coupling rules (CL-*) — coupling is always fixed first
  2. Migration rules (DB-*) — no schema change without a migration
  3. Tracing rules (T-*) — tracing is in the same PR as the feature
  4. Axioms (AX-*) — non-negotiable baseline
  5. Stage rules — stage determines what structure is built
  6. Lazy generation rules (G-LAZ-*) — don't build what you don't need yet

Example: "I am in stage 0 and I need to add a vendor call"
  → Stage 0 allows direct vendor use (stage rule)
  → BUT coupling rules still apply (CL-1: no cross-package import)
  → AND tracing still applies (T-1, T-2 minimum)
  → AND migration rules still apply (DB-1 through DB-7 minimum)
  → Stage 0 only relaxes port abstraction — not coupling, not tracing, not migrations
  ====
  
Connascence — The Real Coupling Taxonomy

COLDEST (safest, easiest to change)
  │
  ├── CoN  — Connascence of Name         → A calls B by name
  ├── CoT  — Connascence of Type         → A and B agree on a type
  ├── CoM  — Connascence of Meaning      → A and B agree on a value's meaning (e.g. 0 = success)
  ├── CoP  — Connascence of Position     → A passes args in the right order
  ├── CoA  — Connascence of Algorithm    → A and B must use the same algorithm (e.g. same hash)
  ├── CoE  — Connascence of Execution    → A must run before B
  ├── CoT  — Connascence of Timing       → A must run at the same time as B (race conditions)
  ├── CoV  — Connascence of Value        → A and B share a mutable value
  └── CoI  — Connascence of Identity     → A and B must reference the exact same object in memory
  │
HOTTEST (most dangerous, hardest to change)
The goal: Push all coupling toward the top (Name/Type). Any coupling below Algorithm is a design smell in large systems.

