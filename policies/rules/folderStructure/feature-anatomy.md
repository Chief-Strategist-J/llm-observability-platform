Feature Anatomy & Folder Structure



Core Principle
A feature is a vertical slice through the entire application stack. It owns everything it needs — its API entry point, all business logic, its data access, its types, and its tests. Nothing leaks out except through its public index. Nothing leaks in except through its declared dependencies.

What a Vertical Slice Means

Layer
Traditional Horizontal (avoid)
Feature-First Vertical (use)
Entry point
controllers/ — all controllers together
features/payments/api/handler
Business logic
services/ — all services together
features/payments/service
Data access
repositories/ — all repos together
features/payments/repository
Types / models
models/ — all models together
features/payments/types
Tests
tests/ — mixed all features
features/payments/tests/


The Feature Golden Rule
A feature is a directory, not a file. Everything a feature needs lives inside that directory. The only thing other parts of the codebase can touch is the feature's index file. If it is not exported from index, it does not exist to the outside world.

Single Feature — Complete Anatomy

src/features/{feature-name}/
│
├── index   ← the ONLY public surface exports: use-cases, types needed by callers
│           never exports: service, repository, internal types
│
├── service ← ALL business logic lives here pure functions — no IO, no HTTP, 
             no DB calls calls repository via injected port interface calls other features ONLY via their index
│
├── repository  ← ALL data access lives here implements the feature's 
                data port  interface calls infra/adapters via port interface only no business logic — query and map only
│
├── handler ← entry-point glue (REST, GraphQL, gRPC, event)
│   ├── rest   ← REST handler — calls service via index
│   ├── graphql ← GraphQL resolver — calls service via index
│   ├── grpc ← gRPC handler — calls service via index
│   └── event ← event consumer — calls service via index
│
├── types   ← ALL types owned by this feature
│   ├── input ← request/command types
│   ├── output ← response/result types
│   ├── domain ← domain model types (internal)
│   └── errors ← feature-specific error types
│
├── contracts ← feature's own API contract
│   ├── v1.yaml  ← written BEFORE service and handler
│   └── changelog.md
│
├── migrations  ← database changes owned by this feature
│   ├── 0001_init.sql
│   └── 0001_init.rollback.sql
│
├── seeds  ← dev and test seed data for this feature only
│   └── {feature-name}.sql
│
├── feature-flag.yaml ← declares any feature flags this feature uses
│
└── tests/
    ├── unit/ ← service logic, pure, no IO
    ├── integration/  ← repository against real DB
    ├── contract/   ← validates own published contract
    ├── e2e/   ← full slice from handler to DB and back
    └── fixtures/ ← shared test data factories for this feature


Feature Index — What It Exports and What It Does Not

Exported from index — callers may use
Never exported — internal only
Use-case functions (create, update, get, delete)
service internals
Input types (CreatePaymentInput, etc.)
repository
Output types (PaymentResult, etc.)
domain model types
Error types (PaymentNotFoundError, etc.)
database query internals
Feature flag keys (as constants)
handler implementations
Event names this feature publishes (as constants)
migration files


Feature Layer Responsibility

Layer
Owns
Does Not Own
IO Allowed
index
public API surface of this feature
implementation details
No
service
all business logic, decisions, rules
IO, data access, HTTP
No — pure logic only
repository
data read and write via port interface
business rules, HTTP
Yes — DB calls only
handler
protocol translation (HTTP ↔ domain)
business logic, data access
No — calls index only
types
all type definitions for this feature
logic of any kind
No
contracts
API contract definition
implementation
No — document only
migrations
schema changes for this feature
application logic
Yes — SQL only
tests
validation of all the above
production logic
Yes — controlled

