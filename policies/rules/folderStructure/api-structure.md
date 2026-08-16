# API-First & Data-Driven Folder Structure
*(Language-Agnostic Architecture Reference for Node.js/TypeScript, Go, Python, Rust, Java, C++)*

---

### Core Rules

1. **.gitkeep Requirement**: When generating or scaffolding folder structures, include a `.gitkeep` file in every folder to preserve directory hierarchy across Git commits.
2. **Contract-First Constraint**: No implementation source code inside `src/` is written until the API contract file is merged. Contract type is chosen once per feature — never generate unused contract formats.
3. **Data-Driven Logic Rule**: Write core engine logic ONCE (adapters, pipeline decorators, rules evaluator, workflow runner). New domain features are created by declaring schemas, transform rules, and state machine definitions as data — not by duplicating boilerplate logic.

---

### Contract Type Selection

- **Client-facing query or mutation** → GraphQL SDL
- **Service-to-service synchronous call** → OpenAPI OR gRPC Proto (select one)
- **Async or event-driven streaming** → AsyncAPI + JSON Schema
- **Internal only, no cross-package boundary** → Local feature types only, nothing in shared contracts

---

### Shared Contracts Tree

```
shared/
├── contracts/
│   ├── openapi/
│   │   └── {service}/
│   │       ├── .gitkeep
│   │       ├── v1.yaml
│   │       ├── v2.yaml                  ← only when a breaking change occurs
│   │       └── changelog.md             ← every change documented here
│   │
│   ├── graphql/
│   │   └── {service}/
│   │       ├── .gitkeep
│   │       ├── v1.graphql
│   │       ├── v2.graphql               ← only when a breaking change occurs
│   │       └── changelog.md
│   │
│   ├── proto/                           ← only when gRPC is explicitly chosen
│   │   └── {service}/
│   │       ├── .gitkeep
│   │       ├── v1/
│   │       └── v2/
│   │
│   ├── asyncapi/                        ← only when a real async event exists
│   │   └── {service}/
│   │       ├── .gitkeep
│   │       ├── v1.yaml
│   │       └── changelog.md
│   │
│   └── json-schema/
│       └── {event}/
│           ├── .gitkeep
│           └── v1.json
│
├── events/
│   ├── .gitkeep
│   ├── registry.yaml                    ← all event names, versions, owners
│   └── conventions.md                   ← naming rules, read before adding
│
├── errors/
│   ├── .gitkeep
│   ├── codes.yaml                       ← canonical error codes
│   └── mapping.md
│
├── tracing/
│   ├── .gitkeep
│   ├── conventions.md                   ← span naming rules
│   ├── baggage-keys.md                  ← stage 3 and above only
│   └── sampling-rules.yaml              ← stage 3 and above only
│
└── ports/                               ← all infra port interfaces
    ├── .gitkeep
    ├── database.interface
    ├── cache.interface
    ├── queue.interface
    ├── storage.interface
    ├── email.interface
    ├── sms.interface
    ├── payment.interface
    ├── search.interface
    ├── logger.interface
    ├── feature-flag.interface
    ├── metrics.interface
    └── secret-store.interface
```

---

### Per-Package Contract & Containerization Tree

Every service/package declares its contract, containerization, and test suite prior to writing feature code.

```
{package}/
├── Dockerfile                           ← Multi-stage production container build
├── Dockerfile.dev                       ← Local development container with hot-reload
├── docker-compose.yml                   ← Package isolated runtime + test dependencies (DB, Redis, Mock APIs)
├── .dockerignore                        ← Container build context exclusion rules
│
├── deploy/                              ← Infrastructure deployment manifests
│   ├── .gitkeep
│   ├── k8s/                             ← Kubernetes manifests (Deployment, Service, HPA, ConfigMap)
│   └── helm/                            ← Helm deployment values chart
│
├── contracts/                           ← Contract specs owned by this package
│   ├── .gitkeep
│   ├── openapi/
│   │   ├── .gitkeep
│   │   ├── v1.yaml
│   │   └── v2.yaml                      ← only when breaking change forces it
│   ├── graphql/
│   │   ├── .gitkeep
│   │   ├── v1.graphql
│   │   └── v2.graphql                   ← only when breaking change forces it
│   ├── proto/
│   │   ├── .gitkeep
│   │   └── v1/                          ← only when gRPC is chosen
│   ├── asyncapi/
│   │   ├── .gitkeep
│   │   └── v1.yaml                      ← only when async event exists
│   └── changelog.md
│
└── tests/                               ← Global Package Test Suite
    ├── .gitkeep
    ├── unit/                            ← Isolated domain unit tests
    │   └── .gitkeep
    ├── integration/                     ← Test suite against containerized infra (Postgres, ClickHouse, Redis)
    │   └── .gitkeep
    ├── contract/                        ← OpenAPI / AsyncAPI / gRPC schema compliance tests
    │   └── .gitkeep
    ├── performance/                     ← K6 / Locust / Benchmark performance load & stress tests
    │   ├── .gitkeep
    │   ├── scenarios/
    │   │   ├── .gitkeep
    │   │   ├── load-test.spec           ← High concurrency steady load scenario
    │   │   ├── stress-test.spec         ← System breaking point stress scenario
    │   │   └── spike-test.spec          ← Sudden traffic burst scenario
    │   └── thresholds.json              ← Latency SLAs (p95 < 100ms, error rate < 0.01%)
    └── e2e/                             ← End-to-End API workflow test suite
        └── .gitkeep
```

---

### API-First Workflow — Mandatory Steps

1. **Contract Definition**: Choose one contract type for the feature. Write that contract file only.
2. **Field Completion**: Add every field with its data type, nullability, validation constraints, error codes, authentication requirements, and rate limit hints.
3. **Contract Review**: Open a contract-only PR. No implementation code in this PR. Contract linting and breaking change checks must pass.
4. **Client & Stub Generation**: Run the code generation script (`generate.sh` or language toolchain) to produce server stubs, client SDKs, and types from the contract. Never write API stubs by hand.
5. **Implementation**: Implement feature handlers behind the contract interface.
6. **Verification**: Run unit, contract, integration, and performance tests to validate that implementation strictly satisfies SLAs and contracts.

---

### Per-Package Source Tree — After Contract Merges

```
{package}/
└── src/
    ├── api/                             ← All entry points live here only
    │   ├── .gitkeep
    │   ├── rest/
    │   │   ├── .gitkeep
    │   │   ├── v1/
    │   │   │   ├── .gitkeep
    │   │   │   ├── router               ← Mounts routes, zero business logic
    │   │   │   └── handlers/            ← One handler file per resource
    │   │   │       └── .gitkeep
    │   │   └── v2/                      ← Only when v2 contract exists
    │   │
    │   ├── graphql/                     ← Only when GraphQL is chosen
    │   │   ├── .gitkeep
    │   │   ├── v1/
    │   │   │   ├── .gitkeep
    │   │   │   ├── schema               ← Loads SDL from contracts/
    │   │   │   ├── resolvers/           ← One file per type
    │   │   │   └── dataloaders/         ← One per relation, required
    │   │   └── v2/
    │   │
    │   ├── grpc/                        ← Only when gRPC is chosen
    │   │   ├── .gitkeep
    │   │   └── v1/
    │   │       ├── .gitkeep
    │   │       ├── server
    │   │       └── handlers/
    │   │
    │   └── events/                      ← Only when async events exist
    │       ├── .gitkeep
    │       ├── consumers/               ← One file per event type
    │       └── publishers/              ← One file per event type
    │
    ├── features/                        ← All business logic & data-driven declarations
    │   ├── .gitkeep
    │   └── {feature-name}/
    │       ├── .gitkeep
    │       ├── index                    ← Only public surface of this feature
    │       ├── schema                   ← Entity schema contract (fields, validate, fromApi, toApi)
    │       ├── rules                    ← Business rules AS DATA (priority, category, async conditions)
    │       ├── machines                 ← State machine definitions AS DATA (XState / State DAG)
    │       ├── workflows                ← Step automation DAG definitions AS DATA
    │       ├── service                  ← Feature business logic (no HTTP, no raw IO)
    │       ├── repository               ← DB access via port interface only
    │       ├── types                    ← Feature-local domain types
    │       └── tests/
    │           ├── .gitkeep
    │           ├── unit/                ← Feature unit tests
    │           ├── integration/         ← Feature integration tests
    │           └── contract/            ← Feature contract validation tests
    │
    ├── infra/                           ← Infrastructure adapters & client generators
    │   ├── .gitkeep
    │   ├── adapters/                    ← DB, Redis, S3, Email implementation adapters
    │   │   ├── .gitkeep
    │   │   └── {vendor}/
    │   ├── clients/                     ← Generated client SDKs only, never hand-written
    │   │   ├── .gitkeep
    │   │   └── {upstream-service}/
    │   │       └── v1/
    │   └── tracing/                     ← OTEL instrumentation & middleware
    │       ├── .gitkeep
    │       ├── tracer
    │       └── middleware
    │
    └── shared/                          ← Package-internal shared utilities & engine core
        ├── .gitkeep
        ├── data-driven/                 ← Core data-driven engine (run once, declared as data)
        │   ├── .gitkeep
        │   ├── entity-schema            ← Generic CRUD schema validator
        │   ├── list-transform           ← Generic filter/search/sort/paginate runner
        │   ├── json-map                 ← Generic anti-corruption field mapper
        │   └── adapter-decorators       ← withRetry / withCache / withCircuitBreaker / withTracing
        ├── rules-engine/                ← Declarative rules engine (priority, deny-override)
        │   ├── .gitkeep
        │   ├── evaluator
        │   └── async-checkers
        ├── workflow-engine/             ← Generic step-as-data DAG runner
        │   ├── .gitkeep
        │   ├── step-registry
        │   └── runner
        ├── types/
        ├── errors/
        ├── di/
        └── utils/
```

---

### Data-Driven Architecture Guidelines

1. **Write Engine Logic Once**: Generic logic for CRUD data adapters, anti-corruption JSON mapping (`fromApi`/`toApi`), list transformations (search, filter, sort, paginate), and resilience decorators (`withRetry`, `withCache`, `withCircuitBreaker`, `withTracing`) lives in `shared/data-driven/`. Never duplicate this per feature.
2. **Features as Data**: Define features by declaring:
   - **Entity Schema**: Field types, runtime validation rules, and field translation maps (`fromApi`/`toApi`).
   - **Rules as Data**: Declarative rule sets with priority levels, categories, and async condition checkers (`evaluate.ts` / `rules.json`).
   - **State Machines as Data**: Declarative state transitions and guards.
   - **Workflows as Data**: Step DAG automation definitions evaluated by a traced DAG runner.

---

### Contract Rules — REST

- Every published version is immutable. No breaking changes to an existing version.
- A breaking change always creates a new version file (`v2.yaml`).
- Old version runs in parallel until its sunset date passes (minimum 6 months from deprecation notice).
- `Deprecation` and `Sunset` HTTP headers sent on every response from a deprecated version.
- `.contract-lock` pins the exact version each package consumes.

---

### Contract Rules — GraphQL

- Schema SDL lives in `shared/contracts/graphql/{service}/v{n}.graphql`.
- Resolvers live in `feature/handler/` — never inside the schema file.
- Every type must have a description comment.
- Mutations always return the mutated type — never return Boolean.
- N+1 queries are contract violations; a dataloader is required per relation.
- Introspection is disabled in production.

---

### Breaking vs Compatible GraphQL Changes

| Breaking (New Version Required) | Compatible (In-Place Allowed) |
|---|---|
| Removing a type or field | Adding an optional field or type |
| Renaming a type or field | Adding a new query or mutation |
| Changing a field type | Adding a new optional argument |
| Making a nullable field non-null | Adding `@deprecated` tag |
| Removing an enum value | Expanding an enum additively |

---

### What Is Never Generated Speculatively

- `v2` contracts — generated only when a breaking change occurs.
- `proto/` directory — generated only when gRPC is explicitly chosen.
- `asyncapi/` directory — generated only when real async event streams exist.
- `clients/` directory — generated only when cross-package service calls exist.
