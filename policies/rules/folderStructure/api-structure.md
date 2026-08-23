# API-First & Data-Driven Folder Structure
*(Language-Agnostic Architecture Reference for Go, Python, Rust, Java, C++, Node.js/TypeScript, and C#)*

---

### Core Rules

1. **Language-Agnostic Principle**: This architecture specification is strictly **language-agnostic**. The folder hierarchy, contract isolation, database migration rules, and data-driven engine boundaries apply identically regardless of whether the service is implemented in Go, Python, Rust, Java, C++, Node.js/TypeScript, or C#.
2. **.gitkeep Requirement**: When generating or scaffolding folder structures, include a `.gitkeep` file in every folder to preserve directory hierarchy across Git commits.
3. **Contract-First Constraint**: No implementation source code inside `src/` is written until the API contract file is merged. Contract type is chosen once per feature — never generate unused contract formats.
   - **Contract Merge Pre-Condition**: Under no circumstances may any implementation file in `src/` (handlers, services, repositories, schemas) be created, scaffolded, or merged until the corresponding contract specification file (`contracts/openapi/`, `contracts/graphql/`, `contracts/proto/`, `contracts/asyncapi/`) is merged in a dedicated contract-only PR.
   - **Single Contract Selection**: Each feature endpoint or flow selects exactly ONE primary contract format (REST OpenAPI, GraphQL SDL, gRPC Proto, or AsyncAPI + JSON Schema). Speculative generation of unused contract formats (e.g. generating `.proto` or `.graphql` when building a REST API) is strictly prohibited.
   - **Automated Client & Stub Generation**: Hand-writing request/response types or server interface stubs is forbidden. The build toolchain or code generator (`generate.sh` / protoc / openapi-generator) MUST automatically generate server interfaces, request validation types, and client SDKs from the authoritative contract specification.
   - **Immutability & Deprecation Lifecycle**: Merged contract versions (`v1.yaml`, `v1.graphql`) are strictly immutable. Any breaking modification requires a new version (`v2.yaml`) running in parallel with deprecation headers (`Deprecation`, `Sunset`) for a minimum sunset window of 6 months.

4. **Data-Driven Logic Rule**: Write core engine logic ONCE (adapters, pipeline decorators, rules evaluator, workflow runner). New domain features are created by declaring schemas, transform rules, flow-by-flow queries, and state machine definitions as data — not by duplicating boilerplate logic.
   - **Single Engine Implementation Mandate**: Core infrastructure and logic engine mechanics — including CRUD adapters, payload transformation mappers, list operators (search, filter, sort, pagination), resilience pipeline decorators, business rules evaluators, and step DAG workflow runners — are implemented ONCE inside `shared/data-driven/`, `shared/rules-engine/`, and `shared/workflow-engine/`. Imperative re-implementation of engine logic inside individual feature directories is strictly forbidden.
   - **The 5 Immutable Feature Data Pillars**: Every feature inside `src/features/{feature-name}/` is defined purely as declarative DATA artifacts conforming to five standardized pillars:
     1. **Entity Schema Contract (`schema/`)**: Runtime field definitions, data types, validation constraints, default values, and bidirectional API/DB transformation mappers (`fromApi` / `toApi`).
     2. **Flow-by-Flow Parameterized Queries (`queries/`)**: Every database operation MUST be explicitly declared inside `features/{feature}/queries/{feature}.queries.[ext|sql]` as a named, flow-grouped parameterized query structure (`FLOW_SIGN_IN`, `FLOW_VERIFY_SESSION`, `FLOW_CREATE_API_KEY`). Raw inline SQL string construction inside services or handlers is strictly prohibited.
     3. **Rules as Data (`rules/`)**: Business logic decision trees declared as structured rule sets with priority weights, decision categories, deny-override conflict resolution, and async condition checkers (`evaluate.ts` / `rules.json`).
     4. **State Machines as Data (`machines/`)**: Multi-state lifecycle flows declared as state transition graphs with guard conditions, valid state triggers, and event side-effects evaluated by generic state machine actors.
     5. **Workflows as Data (`workflows/`)**: Multi-step DAG automation flows declared as step arrays (e.g. `evaluateRules`, `callEntity`, `callAI`, `humanApproval`) executed by the generic, OpenTelemetry-traced workflow engine.
   - **Declarative Anti-Corruption Layer (ACL)**: Imperative payload translation code (e.g. manually copying and renaming object properties line-by-line) is prohibited. Payload translation between external contract schemas and internal entity models MUST be handled declaratively using standardized data mapping operations (`rename`, `pick`, `omit`, `coerce`, `default`).
   - **Resilience Decorator Composition**: Infrastructure adapters MUST be wrapped using standardized pipeline decorator composition (`withTracing(withCircuitBreaker(withCache(withRetry(adapter))))`) at the call site, eliminating per-feature error handling, caching, or retry boilerplate.
   - **Strict Architecture Enforcement**: Any PR introducing imperative `if/else` forest logic, custom payload mappers, inline query strings, or bespoke state toggles inside feature packages violates this architecture and will be rejected.



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

### Per-Package Contract, Database Migration & Containerization Tree

Every service/package declares its contract, database schema migrations, containerization, and test suite prior to writing feature code.

```
{package}/
├── Dockerfile                           ← Multi-stage production container build
├── Dockerfile.dev                       ← Local development container with hot-reload
├── docker-compose.yml                   ← Package isolated runtime + test dependencies (Databases, Redis, Mock APIs)
├── .dockerignore                        ← Container build context exclusion rules
│
├── database/                            ← Language-agnostic database schema migrations & seed data
│   ├── .gitkeep
│   ├── migrations/                      ← Numbered SQL DDL migrations with rollback files
│   │   ├── .gitkeep
│   │   ├── 0001_initial_schema.sql
│   │   └── 0001_initial_schema.rollback.sql
│   ├── kafka-topics/                    ← Versioned Kafka Topic Provisioning & Rollback Specs
│   │   ├── .gitkeep
│   │   ├── 0001_create_user_events.json
│   │   └── 0001_create_user_events.rollback.json
│   └── seeds/                           ← Development & test seed datasets
│       └── .gitkeep
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
    ├── integration/                     ← Test suite against containerized infra (Database, Redis)
    │   └── .gitkeep
    ├── contract/                        ← OpenAPI / AsyncAPI / gRPC schema compliance tests
    │   └── .gitkeep
    ├── performance/                     ← Benchmark performance load & stress tests (K6, Locust)
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
4. **Client & Stub Generation**: Run the code generation script (`generate.sh` or target language toolchain) to produce server stubs, client SDKs, and types from the contract. Never write API stubs by hand.
5. **Implementation**: Implement feature handlers behind the contract interface in the chosen language.
6. **Verification**: Run unit, contract, integration, and performance tests to validate that implementation strictly satisfies SLAs and contracts.

---

### Per-Package Source Tree — Language-Agnostic Structure with Flow-by-Flow Queries

```
{package}/
└── src/
    ├── api/                             ← All entry points live here only
    │   ├── .gitkeep
    │   ├── rest/
    │   │   ├── .gitkeep
    │   │   ├── v1/
    │   │   │   ├── .gitkeep
    │   │   │   ├── router                   ├── features/                        ← All business logic & data-driven declarations
    │   ├── .gitkeep
    │   └── {feature-name}/
    │       ├── .gitkeep
    │       ├── index                    ← Only public surface of this feature
    │       ├── ports/                   ← Hexagonal Ports (Inbound & Outbound interfaces & implementations)
    │       │   ├── .gitkeep
    │       │   ├── inbound/
    │       │   │   ├── .gitkeep
    │       │   │   └── implementations/
    │       │   │       └── .gitkeep
    │       │   └── outbound/
    │       │       ├── .gitkeep
    │       │       └── implementations/
    │       │           └── .gitkeep
    │       ├── adapters/                ← Hexagonal Adapters (Inbound & Outbound drivers & implementations)
    │       │   ├── .gitkeep
    │       │   ├── inbound/
    │       │   │   ├── .gitkeep
    │       │   │   └── implementations/
    │       │   │       └── .gitkeep
    │       │   └── outbound/
    │       │       ├── .gitkeep
    │       │       └── implementations/
    │       │           └── .gitkeep
    │       ├── schema                   ← Entity schema contract (fields, validate, fromApi, toApi)
    │       ├── queries/                 ← MANDATORY: Flow-by-Flow Database Queries
    │       │   ├── .gitkeep
    │       │   └── {feature}.queries.[ext|sql] ← Named, flow-by-flow parameterized queries
    │       ├── rules                    ← Business rules AS DATA (priority, category, async conditions)
    │       ├── machines                 ← State machine definitions AS DATA (State DAG / DSL)
    │       ├── workflows                ← Step automation DAG definitions AS DATA
    │       ├── service                  ← Feature business logic (no HTTP, no raw IO)
    │       ├── repository               ← DB access via queries/ and port interface only
    │       ├── types                    ← Feature-local domain types
    │       └── tests/
    │           ├── .gitkeep
    │           ├── unit/                ← Feature unit tests
    │           ├── integration/         ← Feature integration tests
    │           └── contract/            ← Feature contract validation tests← All business logic & data-driven declarations
    │   ├── .gitkeep
    │   └── {feature-name}/
    │       ├── .gitkeep
    │       ├── index                    ← Only public surface of this feature
    │       ├── schema                   ← Entity schema contract (fields, validate, fromApi, toApi)
    │       ├── queries/                 ← MANDATORY: Flow-by-Flow Database Queries
    │       │   ├── .gitkeep
    │       │   └── {feature}.queries.[ext|sql] ← Named, flow-by-flow parameterized queries
    │       ├── rules                    ← Business rules AS DATA (priority, category, async conditions)
    │       ├── machines                 ← State machine definitions AS DATA (State DAG / DSL)
    │       ├── workflows                ← Step automation DAG definitions AS DATA
    │       ├── service                  ← Feature business logic (no HTTP, no raw IO)
    │       ├── repository               ← DB access via queries/ and port interface only
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
    │   ├── messaging/                   ← Centralized Kafka broker connection & driver management
    │   │   ├── .gitkeep
    │   │   ├── broker-config            ← Broker endpoints, connection pooling & health checks
    │   │   ├── client-factory           ← Single-instance Kafka producer & consumer connection factory
    │   │   └── migrations/              ← Automated Topic Provisioner & Config Rollback Engine
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
        ├── messaging/                   ← Centralized Kafka producer, consumer, middleware & topic management
        │   ├── .gitkeep
        │   ├── middleware/              ← Reusable Producer & Consumer Middleware Pipeline Engine (Zero Code Repetition)
        │   ├── tracing/                 ← MessagingTracer W3C Distributed Trace Context engine & span lifecycle
        │   ├── producers/               ← Middleware-driven typed Kafka event producers
        │   ├── consumers/               ← Middleware-driven consumer group manager & event dispatcher
        │   ├── topics/                  ← Centralized topic catalog & schema registry bindings
        │   ├── handlers/                ← Abstract message handler contracts & event registries
        │   └── cqrs/                    ← CQRS Write Commands, Materialized Read Projections & Query Selectors
        ├── types/
        ├── errors/
        ├── di/
        └── utils/
```

---

### Data-Driven Architecture Guidelines (Language-Agnostic)

1. **Write Engine Logic Once**: Generic logic for CRUD data adapters, anti-corruption JSON mapping (`fromApi`/`toApi`), list transformations (search, filter, sort, paginate), and resilience decorators (`withRetry`, `withCache`, `withCircuitBreaker`, `withTracing`) lives in `shared/data-driven/`. Never duplicate this per feature.
2. **Features as Data**: Define features by declaring:
   - **Entity Schema**: Field types, runtime validation rules, and field translation maps (`fromApi`/`toApi`).
   - **Flow-by-Flow Queries**: All database queries **MUST** be explicitly declared inside `features/{feature}/queries/{feature}.queries.[ext|sql]` as named, flow-by-flow parameterized query structures to enable end-to-end tracing of every database execution step.
   - **Rules as Data**: Declarative rule sets with priority levels, categories, and async condition checkers (`evaluate` / `rules.json`).
   - **State Machines as Data**: Declarative state transitions and guards.
   - **Workflows as Data**: Step DAG automation definitions evaluated by a traced DAG runner.

---

### Kafka & Messaging Architecture Guidelines (Language-Agnostic)

1. **Centralized Messaging Infra (`infra/messaging/`)**: Low-level Kafka broker connections, connection pooling, security/SASL configs, and connection factories are maintained in `infra/messaging/`. Never open raw Kafka sockets or initialize driver instances inside feature handlers or HTTP routers.
2. **Topic Migrations & Rollback Engine (`database/kafka-topics/` & `infra/messaging/migrations/`)**: Every Kafka topic must be provisioned via versioned migration specs (`NNNN_topic_name.json`) and matching rollback files (`NNNN_topic_name.rollback.json`). Topic definitions declare partition counts, replication factor, retention MS, cleanup policy (`delete` | `compact`), and `min.insync.replicas`. Topic provisioner automatically applies or rolls back topic configurations safely across environments.
3. **Distributed Tracing Graph & W3C Context Propagation**:
   - **Producer Injection**: Producer automatically injects OpenTelemetry W3C Trace Context (`traceparent` and `tracestate`) into Kafka Message Headers before publishing.
   - **Consumer Extraction**: Consumer extracts `traceparent` from Kafka Message Headers to parent child spans, generating a complete, contiguous distributed tracing graph across microservice boundaries.
   - **Correlation & Baggage**: Passes `correlation_id` and `tenant_id` in headers for global trace query filtering.
4. **Scale & Performance Optimizations**:
   - **Idempotence & Reliability**: Enable idempotent producer (`enable.idempotence=true`, `acks=all`) for exactly-once in-order message delivery.
   - **Batching & Compression**: Configure producer batching (`linger.ms=10`, `batch.size=32768`) with `snappy` or `zstd` compression.
   - **Consumer Backpressure & Offsets**: Consumers process messages in batches, commit offsets asynchronously (`commitAsync`), and route unprocessable messages to Dead Letter Queue (DLQ) retry topics (`{topic}-dlq`).
5. **Pluggable Messaging Middleware Engine (`shared/messaging/middleware/`)**: All event producers and consumers **MUST** execute through composable middleware pipelines (`ProducerMiddlewarePipeline`, `ConsumerMiddlewarePipeline`). Imperative duplicate `try/catch`, logging, or tracing boilerplate inside individual producer methods or consumer handler classes is strictly prohibited.
6. **Messaging Tracing Engine (`shared/messaging/tracing/`)**: Dedicated `MessagingTracer` handles W3C trace parent context generation, span lifecycle tracking, and attribute tagging (`messaging.system`, `messaging.destination`, `messaging.kafka.event_name`, `messaging.correlation_id`, `messaging.tenant_id`) across producer and consumer middleware chains.
7. **CQRS & Append-Only Event Stream (`shared/messaging/cqrs/`)**: Write commands publish immutable, append-only events to Kafka. Writes never mutate read tables directly. Consumers fold incoming event streams into materialized projection stores (`projection.store.ts`), and isolated query selectors (`query.selectors.ts`) serve reads with zero write-side coupling.

---

### Order of Development & Change Management

To prevent contract drift, schema locking, and coupling violations, all development follows a strict 7-step sequence:

```
[1. API Contract] ──► [2. DB Migration] ──► [3. Port Interface] ──► [4. Data-Driven Schema & Queries] ──► [5. Service Logic] ──► [6. API Handler] ──► [7. Test Suite]
```

1. **Step 1 — API Contract Definition (`contracts/`)**: Define or update `openapi/v1.yaml`, `graphql/`, or `proto/` in a contract-only PR. Generate client SDKs via `generate.sh`.
2. **Step 2 — Database Schema Migration (`database/migrations/`)**: Create a numbered migration file (`database/migrations/NNNN_description.sql`) and matching rollback file (`database/migrations/NNNN_description.rollback.sql`). See [database/migration.md](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/migration.md).
3. **Step 3 — Shared Infrastructure Port Interface (`shared/ports/`)**: Declare or update abstract infrastructure interface ports (e.g. `database.interface`, `cache.interface`).
4. **Step 4 — Data-Driven Entity & Query Declaration (`src/features/{feature}/`)**: Declare entity schemas (`schema/`), flow-by-flow queries (`queries/`), transformation mappers (`fromApi`/`toApi`), and declarative rules (`rules/`).
5. **Step 5 — Core Domain Service Implementation (`src/features/{feature}/service`)**: Implement business logic using pure domain models and injected repository ports (no direct HTTP/IO).
6. **Step 6 — API Router & Handler Mounting (`src/api/rest/v1/`)**: Connect contract stubs to domain service methods via resource handlers (`auth.handler`).
7. **Step 7 — Comprehensive Test Suite Verification (`tests/`)**: Validate with unit tests, containerized integration tests, contract compliance tests, and K6 performance load tests.

---

### Order of Database & Schema Migration Changes

All database modifications must comply with zero-downtime Expand and Contract migration rules:

1. **Never Touch Database Manually**: Every schema change is a versioned SQL file inside `database/migrations/` with a mandatory rollback counterpart.
2. **Column Rename (5-PR Sequence)**:
   - PR 1: Add new column via migration file.
   - PR 2: Dual-write to both old and new columns in application layer.
   - PR 3: Backfill old data into new column via async worker.
   - PR 4: Switch application reads to new column.
   - PR 5: Drop old column via migration with rollback file.
3. **Database Architecture & Replication**: All multi-region replication, horizontal sharding keys, WAL archiving, and storage engine choices must strictly align with [database/sharding-replication-architecture.md](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/sharding-replication-architecture.md) and [database/query-writing-rules.md](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/query-writing-rules.md).

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
