API-First Folder Structure



Core Rule
No file inside src/ is written until the contract file is merged. Contract type is chosen once per feature — not all types are generated.

Contract Type Selection
Client-facing query or mutation → GraphQL SDL
Service-to-service synchronous call → OpenAPI OR proto, pick one
Async or event-driven → AsyncAPI + JSON Schema
Internal only, no cross-package boundary → local feature/types only, nothing in shared/

Shared Contracts Tree

shared/
├── contracts/
│   ├── openapi/
│   │   └── {service}/
│   │       ├── v1.yaml
│   │       ├── v2.yaml                  ← only when a breaking change occurs
│   │       └── changelog.md             ← every change documented here
│   │
│   ├── graphql/
│   │   └── {service}/
│   │       ├── v1.graphql
│   │       ├── v2.graphql               ← only when a breaking change occurs
│   │       └── changelog.md
│   │
│   ├── proto/                           ← only when gRPC is explicitly chosen
│   │   └── {service}/
│   │       ├── v1/
│   │       └── v2/
│   │
│   ├── asyncapi/                        ← only when a real async event exists
│   │   └── {service}/
│   │       ├── v1.yaml
│   │       └── changelog.md
│   │
│   └── json-schema/
│       └── {event}/
│           └── v1.json
│
├── events/
│   ├── registry.yaml                    ← all event names, versions, owners
│   └── conventions.md                   ← naming rules, read before adding
│
├── errors/
│   ├── codes.yaml                       ← canonical error codes
│   └── mapping.md
│
├── tracing/
│   ├── conventions.md                   ← span naming rules
│   ├── baggage-keys.md                  ← stage 3 and above only
│   └── sampling-rules.yaml             ← stage 3 and above only
│
└── ports/                               ← all infra port interfaces
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


Per-Package Contract Tree
Every package declares its own contracts before any source is written.

{package}/
└── contracts/
    ├── openapi/
    │   ├── v1.yaml
    │   └── v2.yaml              ← only when breaking change forces it
    ├── graphql/
    │   ├── v1.graphql
    │   └── v2.graphql           ← only when breaking change forces it
    ├── proto/
    │   └── v1/                  ← only when gRPC is chosen
    ├── asyncapi/
    │   └── v1.yaml              ← only when async event exists
    └── changelog.md


API-First Workflow — Mandatory Steps
Choose one contract type for the feature. Write that file only.
Add every field with its type and nullability. Add every error case. Add auth requirements and rate limit hint.
Open a contract-only PR. No implementation code in this PR.
Contract lint must pass. Breaking change check must pass. One review minimum.
Merge contract PR. Update .contract-lock if stage 2 or above.
Run generate.sh to produce clients and types from the contract. Never write clients by hand.
Implement the feature behind the contract.
Contract tests validate that the implementation matches the contract.

Per-Package Source Tree — After Contract Merges

{package}/
└── src/
    ├── api/                             ← all entry points live here only
    │   ├── rest/
    │   │   ├── v1/
    │   │   │   ├── router               ← mounts routes, zero logic
    │   │   │   └── handlers/            ← one file per resource
    │   │   └── v2/                      ← only when v2 contract exists
    │   │
    │   ├── graphql/                     ← only when GraphQL is chosen
    │   │   ├── v1/
    │   │   │   ├── schema               ← loads SDL from contracts/
    │   │   │   ├── resolvers/           ← one file per type
    │   │   │   └── dataloaders/         ← one per relation, required
    │   │   └── v2/
    │   │
    │   ├── grpc/                        ← only when gRPC is chosen
    │   │   └── v1/
    │   │       ├── server
    │   │       └── handlers/
    │   │
    │   └── events/                      ← only when async events exist
    │       ├── consumers/               ← one file per event type
    │       └── publishers/              ← one file per event type
    │
    ├── features/                        ← all business logic, nowhere else
    │   └── {feature-name}/
    │       ├── index                    ← only public surface of this feature
    │       ├── service                  ← all business logic, no IO, no HTTP
    │       ├── repository               ← db access via port interface only
    │       ├── types                    ← feature-local types
    │       └── tests/
    │           ├── unit/
    │           ├── integration/         ← added when real infra available
    │           └── contract/            ← added when contract is published
    │
    ├── infra/                           ← stage 1 and above only
    │   ├── adapters/
    │   │   └── {vendor}/
    │   ├── clients/                     ← generated only, never hand-written
    │   │   └── {upstream-service}/
    │   │       └── v1/
    │   └── tracing/
    │       ├── tracer
    │       └── middleware
    │
    └── shared/                          ← package-internal only
        ├── types/
        ├── errors/
        ├── di/
        └── utils/


Contract Rules — REST
Every version published is immutable. No breaking changes to an existing version.
A breaking change always creates a new version file.
Old version runs in parallel until its sunset date passes.
Sunset date minimum 6 months from deprecation notice.
Sunset and Deprecation headers sent on every deprecated response.
.contract-lock pins the exact version each package consumes.

Contract Rules — GraphQL
Schema SDL lives in shared/contracts/graphql/{service}/v{n}.graphql.
Resolvers live in feature/handler/ — never inside the schema file.
Schema stitching and federation config lives in apis/gateway/graphql/ only.
Every type has a description comment. No undocumented types.
Every field marked @deprecated must have a reason and a sunset date.
Mutations always return the mutated type. Never return Boolean.
Subscriptions are backed by a queue, never by polling.
N+1 is a contract violation. A dataloader is required per relation.
Generated types from SDL only. Never hand-written client types.
Introspection is disabled in production. Schema served via registry only.
Query depth limit and complexity limit declared in apis/gateway/graphql/limits.yaml.

Breaking vs Compatible GraphQL Changes

Breaking — new version required
Compatible — in-place allowed
Removing a type
Adding an optional field
Removing a field
Adding a new type
Renaming a type or field
Adding a new query or mutation
Changing a field type
Adding a new optional argument
Making a nullable field non-null
Adding @deprecated
Removing an enum value
Expanding an enum additively
Changing argument from optional to required
Adding a new subscription
Removing a query, mutation, or subscription
Relaxing non-null to nullable


What Is Never Generated Speculatively
v2 contracts — only when a breaking change actually occurs
proto/ directory — only when gRPC is explicitly chosen
asyncapi/ directory — only when a real async event exists
clients/ directory — only when a cross-package call exists
dataloaders/ — only when a relation exists in the GraphQL schema
grpc/ in src/api/ — only when gRPC is chosen
events/ in src/api/ — only when async consumers or publishers exist
