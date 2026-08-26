Language-Specific Multiple Package Structure

while generating folder structure add .gitkeep in each folder


Core Rules
1. Every sub-package is fully isolated. No sub-package imports source from another sub-package, even within the same language. Runtime calls always go through a versioned contract and a generated client.
2. **DRY Guardrail (Do Not Repeat Code)**: Never duplicate code, broker setup, connection pools, serializers, or middleware pipelines. Every feature and service MUST re-use pre-existing shared components under `src/infra/messaging/` and `src/shared/`.
3. **Directory Initialization**: Always include `.gitkeep` in empty or newly generated directories.

Language Workspace Layout

packages/
├── python/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── python-shared/           ← types and pure utils only, no business logic
│
├── rust/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── rust-shared/
│
├── go/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── go-shared/
│
├── node/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── node-shared/
│
├── java/
│   ├── {sub-package-a}/
│   ├── {sub-package-b}/
│   └── java-shared/
│
└── apis/                        ← gateway package, stage 2 and above only


Language-Shared Rules
{lang}-shared/ contains zero runtime dependencies and zero business logic.
Only type definitions and pure utility functions with no IO.
A sub-package imports from {lang}-shared/ via its index export only.
If a utility requires IO or has side effects, it does not belong in {lang}-shared/.
Runtime calls between two sub-packages of the same language still require a full contract and generated client.

{lang}-shared/
├── types/       ← exported via index only
└── utils/       ← pure functions only, no IO, no side effects


Universal Sub-Package Layout
Every sub-package in every language follows this structure. Files use the language's native extension.

{lang}/{package-name}/
│
├── contracts/                       ← written before any src file
│   ├── openapi/
│   │   ├── v1.yaml
│   │   └── changelog.md
│   ├── graphql/                     ← only when GraphQL is chosen
│   │   ├── v1.graphql
│   │   └── changelog.md
│   ├── proto/                       ← only when gRPC is chosen
│   │   └── v1/
│   ├── asyncapi/                    ← only when async event exists
│   │   └── v1.yaml
│   └── changelog.md
│
├── src/
│   ├── api/
│   │   ├── rest/v1/
│   │   │   ├── router
│   │   │   └── handlers/
│   │   ├── graphql/v1/
│   │   │   ├── schema
│   │   │   ├── resolvers/
│   │   │   └── dataloaders/
│   │   ├── grpc/v1/
│   │   │   ├── server
│   │   │   └── handlers/
│   │   └── events/
│   │       ├── consumers/
│   │       └── publishers/
│   │
│   ├── features/
│   │   └── {feature-name}/
│   │       ├── index
│   │       ├── contex.ymal   <--- here create context of this feature what is the business logic we have,all dependcy, core architecture desision, networking,
                               and how this is connected to each other, why its even exists? criticality
│   │       ├── service
│   │       ├── repository
│   │       ├── types
│   │       └── tests/
│   │           ├── unit/
│   │           ├── integration/
│   │           └── contract/
│   │
│   ├── infra/
│   │   ├── adapters/{vendor}/
│   │   ├── clients/{upstream-service}/v1/
│   │   ├── messaging/               <--- messaging infrastructure & broker abstraction
│   │   │   ├── broker/              <--- broker_config.py, connection pools, and health checks
│   │   │   ├── producer/            <--- producer pipeline & clients
│   │   │   │   ├── factory/         <--- producer_factory.py (singleton connection pool)
│   │   │   │   └── producer_client/ <--- kafka_producer_client.py
│   │   │   ├── consumer/            <--- consumer pipeline & clients
│   │   │   │   ├── factory/         <--- consumer_factory.py
│   │   │   │   ├── consumer_client/ <--- kafka_consumer_client.py
│   │   │   │   ├── handlers/        <--- span & domain consumer event handlers
│   │   │   │   └── cqrs/            <--- event-driven queries & projection stores
│   │   │   │       ├── queries/     <--- query_selectors.py
│   │   │   │       └── projections/ <--- projection_store.py
│   │   │   ├── middleware/          <--- producer & consumer pipeline execution engines
│   │   │   │   ├── pipeline.py      <--- ProduceCtx, ConsumeCtx & compose() utility
│   │   │   │   ├── producer_middleware.py <--- tracing, circuit breaker, retry, dedupe, schema, serialization, partition key
│   │   │   │   ├── consumer_middleware.py <--- DLQ, tracing, heartbeat, concurrency, tenant, retry count, deserialization
│   │   │   │   └── tracing_middleware.py  <--- OTEL span context bridge
│   │   │   ├── topics/              <--- topic_provisioner.py & topic_manager.py
│   │   │   ├── migrations/          <--- kafka_topic_migration.py (kafka topic schema migrations)
│   │   │   ├── reporters/           <--- span_reporter.py (kafka span telemetry exporter)
│   │   │   └── tracing/             <--- messaging_tracer.py, context_propagation.py & genai_attributes.py
│   │   └── tracing/
│   │       ├── tracer
│   │       └── middleware
│   │
│   └── shared/
│       ├── types/
│       ├── errors/
│       ├── di/
│       └── utils/
│
├── database/
│   ├── migrations/                  <--- database SQL schema migrations
│   │   ├── 0001_init.sql
│   │   ├── 0001_init.rollback.sql
│   │   └── {NNNN}_{description}.sql
│   ├── seeds/
│   └── schema.lock
│   │   └── {NNNN}_{description}.sql
│   ├── seeds/
│   └── schema.lock
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── e2e/
│   └── performance/
│
├── scripts/
│   ├── run.sh
│   ├── migrate.sh
│   ├── test.sh
│   └── ...
│
├── deploy/
│   ├── docker/
│   │   ├── docker-compose.dev.yaml
│   │   ├── docker-compose.test.yaml
│   │   └── docker-compose.prod.yaml
│   ├── kubernetes/              ← stage 3 only
│   │   ├── base/
│   │   └── overlays/
│   └── terraform/              ← stage 3 only
│
├── build/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── Dockerfile.test
│
├── .github/workflows/
│   ├── ci.yaml
│   ├── cd-staging.yaml
│   └── cd-production.yaml
│
├── .env.example
├── .package-meta.yaml
└── .port-registry


Python
Package manager: own pyproject.toml with src/ layout per sub-package.
Linter: ruff --select ALL, zero warnings.
Types: mypy --strict, zero errors.
Security: bandit and safety check.
Import guard: ruff rule banning cross-package imports.
Test runner: pytest with pytest-cov, minimum 80% coverage.
REST client generation: openapi-python-client into src/infra/clients/.
GraphQL client generation: ariadne-codegen from SDL.
Proto generation: grpcio-tools with buf generate.
Tracing: opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-sqlalchemy.
Contract tests: schemathesis for REST, pytest-gql for GraphQL.
Migrations: alembic managed or raw SQL runner via migrate.sh.
GraphQL server: strawberry or ariadne, schema loaded from SDL file.

Rust
Package manager: own Cargo.toml in workspace. Workspace members never depend on each other.
Linter: clippy --deny warnings, zero warnings.
Types: no unsafe without documented justification.
Security: cargo audit and cargo deny.
Test runner: cargo test with cargo tarpaulin, minimum 80% coverage.
REST client generation: openapi-generator into src/infra/clients/.
GraphQL client generation: cynic or graphql-client codegen.
Proto generation: tonic with buf generate.
Tracing: opentelemetry, tracing, tracing-opentelemetry.
Migrations: sqlx migrate preferred, or refinery.
GraphQL server: async-graphql, schema-first via SDL.

Go
Package manager: own go.mod as a separate module. replace directives never committed to main.
Linter: golangci-lint strict configuration, zero warnings.
Types: go vet and staticcheck.
Security: govulncheck and gosec.
Import guard: depguard, cross-module imports blocked.
Test runner: go test ./..., minimum 80% coverage.
REST client generation: oapi-codegen into src/infra/clients/.
GraphQL server and client generation: gqlgen, schema-first from SDL.
Proto generation: buf generate with connectrpc.
Tracing: go.opentelemetry.io/otel with contrib instrumentation packages.
Migrations: golang-migrate with raw SQL files.

Node / TypeScript
Package manager: own package.json. Workspaces for build tooling only. No runtime cross-package imports.
Linter: eslint --max-warnings 0 and prettier.
Types: tsc --strict, no any, no ts-ignore without documented justification.
Security: npm audit --audit-level=high.
Import guard: eslint no-restricted-imports, cross-package imports banned.
Test runner: vitest preferred or jest, minimum 80% coverage.
REST client generation: openapi-typescript-codegen into src/infra/clients/.
GraphQL client generation: graphql-codegen from shared/contracts/graphql/.
Proto generation: buf generate with @connectrpc/connect.
Tracing: @opentelemetry/sdk-node with auto-instrumentations-node.
Contract tests: openapi-fetch with MSW for REST, graphql-request with MSW for GraphQL.
Migrations: db-migrate or knex migrate, raw SQL preferred.
GraphQL server: apollo-server or graphql-yoga, schema-first via SDL.

Java
Package manager: own Maven module or Gradle subproject per sub-package.
Linter: checkstyle, pmd, spotbugs, zero violations.
Types: no raw types, no unchecked casts without documented justification.
Security: owasp dependency-check.
Import guard: ArchUnit tests, cross-module type references blocked automatically in CI.
Test runner: junit5 with jacoco, minimum 80% coverage.
REST client generation: openapi-generator-maven-plugin into infra/clients/.
GraphQL client generation: graphql-java-codegen from SDL.
Proto generation: protobuf-maven-plugin with grpc-java.
Tracing: opentelemetry-java-instrumentation agent, zero-code instrumentation.
Migrations: flyway preferred or liquibase, SQL files only.
GraphQL server: graphql-java, schema-first, SDL loaded at startup.

Cross Sub-Package Communication Rules

Scenario
Resolution
Type only, same language
Use {lang}-shared/types/ via index export.
Runtime call
Full package boundary always. Contract in shared/contracts/, generated client in src/infra/clients/.
Pure utility, no IO, language-specific
Use {lang}-shared/utils/.
Pure utility needed across languages
Evaluate shared/ at project root.
Database
Each sub-package owns its own database and schema. Never shared.
Event
Schema in shared/events/, publish and subscribe via broker only.
GraphQL schema overlap
Schemas federated via apis/gateway/graphql/stitcher. Never merged inside src/.


