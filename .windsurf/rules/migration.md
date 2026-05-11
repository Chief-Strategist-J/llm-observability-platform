Code Guidelines + Migration Guide



Part A — Code Guidelines

Layer Call Rules
Every call between layers follows a fixed direction. Enforced by linter rules. No exceptions.

From
To
Allowed
api/*
features/*/index
Yes
api/*
features/*/service
No — never bypass index
api/*
infra/*
No — never
features/*/service
features/*/repository
Yes
features/*/service
infra/adapters/
No — use port interface via DI
features/*/service
infra/clients/
Yes — via generated client
features/*/repository
infra/adapters/
Yes — via port interface only
features/*/repository
features/*/service
No — circular
features/A/*
features/B/*
No — go through B/index
infra/*
features/*
No — never
shared/*
features/*
No — never
scripts/*
src/*
No — scripts call HTTP or CLI only


Coupling Rules
Coupling Rule Zero
A coupling violation on main means the system is broken. There is no fixing it later. The engineer who introduces it owns it as their only priority until it is resolved.

Coupling Severity — Highest to Lowest

Type
Description
Fix Priority
CoI — Identity
Shared database, schema, or table. Direct source import. Shared in-memory state. Cannot independently deploy.
Before any other work
CoV — Value
Hardcoded values shared across packages — same table name string, same error message, same vendor name.
Same sprint as discovery
CoA — Action
One package calls another's internal endpoint directly, not via generated client or contract.
Next PR after discovery
CoE — Execution
Shared boot order. Package A fails if package B is not up. Breaks canary deployments.
Before scaling
CoM — Message
Two packages share an event schema. Acceptable only when versioned in shared/contracts/ and pinned in .contract-lock.
Maintain versioning


Coupling Resolution — One Violation Per PR
Every violation is resolved in its own isolated PR sequence.
Never combine two violation resolutions in one PR.
Never combine a violation resolution with a feature PR.
There is no such thing as temporary coupling.
Each resolution PR must pass all CI stages before the next one opens.

Cross-Package Import Violation — Resolution Sequence
Wrap the function or class behind an HTTP or GraphQL handler.
Generate a client from shared/contracts/ via generate.sh.
Replace the import with the generated client call and add a trace span.
Remove the original import.
Update coupling-map.md to remove the entry.

Shared Database Violation — Resolution Sequence
Add an event publisher to the table owner. Write the event schema first.
Add a subscriber and its own isolated database to the consumer.
Dual-write to the old shared database and publish events. Verify on staging.
Flip consumer reads to its own database.
Remove the consumer's shared database access.
Update .port-registry and coupling-map.md.

Port / Adapter Pattern
When to Define a Port
If a port for the required infra type already exists in shared/ports/, implement an adapter that satisfies it.
If no port exists yet, define the port in shared/ports/ first, then implement the adapter.

Adapter Rules
Receives a port interface call.
Translates that call to a vendor SDK call.
Translates the vendor response back to the port interface type.
Wraps the vendor call in a child trace span.
Maps vendor errors to entries in shared/errors/codes.yaml.
Contains zero conditional business logic.

DI Wiring
The DI container in src/shared/di/ selects the adapter based on environment configuration.
Business logic sees only the port interface. It never references the adapter type directly.

Tracing Rules
Tracing Rule Zero
If a trace is not flowing, the system is dark. A dark system does not run in production. No production deploy completes without trace-check.sh returning 0.

Required Attributes on Every Span

Attribute
Value
service.name
language.package-name
service.version
semver
feature.name
feature name
api.version
v1 or v2
deployment.env
prod, staging, or dev
host.name
hostname

A span missing any of these attributes fails CI.

Core Tracing Requirements
OTEL tracer is initialised before any other startup code. It is the first thing that runs.
Every inbound request or event creates a root span immediately. No code executes before the root span is open.
Every outbound call propagates W3C traceparent. No exceptions.
Every error calls span.record_error with the full stacktrace and sets span status to ERROR.
span.end() is always called in a finally block or language equivalent. Never conditional.
No business logic is gated on trace context presence. If traceparent is absent the request still processes normally.
Queue messages carry traceparent in message attributes.
Every adapter wraps its vendor call in a child span.
Database queries are auto-instrumented via adapter middleware.
W3C traceparent is the only propagation format. No custom formats.
Sensitive data never appears in span attributes. No PII, no tokens, no passwords, no card numbers.
Span names are stable. Changing a span name is a breaking change. The old name must be deprecated before removal.
Every cross-package boundary creates a new span on the receiving side.
Every PR that adds a new outbound call includes the span in that same PR. Not a follow-up ticket.
Every PR that adds a new async consumer includes span extraction in that same PR.

Tracing Violation Response

Violation
Priority
Missing root span
P1 — no deploy until fixed
Missing traceparent propagation
P1 — treated as coupling violation
Missing required span attributes
CI block — PR cannot merge
Missing error recording
P2 — next sprint
PII in span attributes
P0 — security incident protocol
trace-check failing in production
Auto-rollback triggered
Span name changed without deprecation
P1 — all dependent dashboards invalidated


Minimum Tracing in Stage 0
OTEL SDK initialised at startup.
Root span created for every inbound request.
Every error recorded on the span.
Span attributes: service.name and deployment.env at minimum.
No business logic gated on trace context.
Exporting to stdout exporter is acceptable at stage 0. No exporter at all is not acceptable.

Part B — Migration Guide

Migration Rule Zero
If there is no migration file for a schema change, the schema change does not exist. It will be reverted. No exceptions, no emergency patches.

Core Migration Rules
Never touch a database manually, in any environment including local dev, staging, and hotfix.
Every schema change is a numbered migration file. Zero exceptions.
Migration files are immutable once merged to main. Editing a merged migration is an immediate PR reject and a production incident.
Every migration has a corresponding rollback file. No rollback file means the PR is blocked.
Migrations run via migrate.sh before the application starts. The application cannot start without a successful migration.
schema.lock records the last applied migration number and is committed to the repository.
CI runs the full migration suite on a clean database on every pipeline.
No cross-package foreign keys, ever, in any form.
Enums stored as varchar with a CHECK constraint. Never as a database enum type.
No stored procedures, triggers, or views. Logic lives in the application.
Every table must have id, created_at, and updated_at.
Soft deletes use a deleted_at column. Never hard delete by default.
Every foreign key declares its ON DELETE behaviour explicitly and has an index.
No nullable column without a documented reason in the migration header.

Migration File Naming

{NNNN}_{description}.sql
{NNNN}_{description}.rollback.sql
 
NNNN is a zero-padded 4-digit number.
Both files are committed in the same PR.


Migration File Header — Required on Every File

-- migration:      0004
-- description:    add payment_status index to orders
-- author:         name
-- date:           ISO date
-- depends_on:     0003
-- reversible:     YES | NO
-- lock_risk:      LOW | MEDIUM | HIGH
-- rows_affected:  estimated count or schema only
-- reason:         query performance — orders by status scans full table

If reversible is NO, the reason must explain why. If lock_risk is HIGH, the PR body must include a maintenance window plan. depends_on is validated by CI.

Migration Size Limit
A migration that changes more than 3 tables or adds more than 5 columns must be split into smaller migrations. Large migrations cannot be rolled back cleanly.

Migration Testing in CI
Every migration is applied on a clean database in CI before merge.
Every migration is tested in both directions: apply, verify, rollback, verify. Both directions must pass.
Staging receives the migration before production. Must pass on staging before the production deploy begins.

High-Risk Migration Checklist
A migration with lock_risk: HIGH or that performs any of the following requires a maintenance window plan in the PR body:
Locks a table.
Backfills more than 10,000 rows.
Adds a non-nullable column to an existing table.
Rebuilds an index.

The PR body must include:
Estimated lock duration.
Estimated row count affected.
Fallback plan if the migration hangs.
Rollback procedure.
Team notification of the maintenance window.

Safe Column Removal — Three PRs Minimum
PR 1: Mark the column as deprecated in a migration comment. Stop all new writes. Add an alert that fires if the column is read.
PR 2: After one full release cycle is verified, remove all reads from application code.
PR 3: After staging is verified clean, add a DROP COLUMN migration with a rollback file.

Column Rename — Five PRs Minimum
PR 1: Add the new column with the new name.
PR 2: Dual-write to both columns in the application.
PR 3: Backfill old values to new column via migration. Verify row counts match.
PR 4: Remove all reads of the old column from application code.
PR 5: DROP the old column via migration with a rollback file.

Vendor Database Swap — Eight Steps, One PR Each
Write a new adapter implementing database.interface.
Write a vendor migration script in database/migrations/.
Shadow write — write to both old and new stores, read from old.
Run a validation job to compare old and new row by row. Log all diffs.
Flip reads to the new store for 5% of traffic via feature flag.
Scale to 100% reads from new store. Monitor for one full release cycle.
Remove shadow write and the old adapter.
Update .port-registry.

Existing Project Migration — Phases
Phase 0 — Audit, Touch Zero Code
Determine the current stage of every existing package. Write it to .package-meta.yaml.
Generate coupling-map.md entries for every cross-package import, every shared database, every missing contract, every missing migration file, every missing port abstraction, every missing trace instrumentation, and every missing script.
Assign severity, owner, target phase, and target PR to every entry.
Commit coupling-map.md. Add CI check: new entries without a phase plan block the pipeline.
Do not write a single line of implementation code in phase 0.
Do not generate any files speculatively. Only document what is missing.

Phase 1 — Contracts and Ports, No Feature Work
Write missing contracts only for cross-package calls that currently exist.
Write missing port interfaces only for vendors actually used today.
Write 0001_init.sql capturing the current schema state for every package with no migration history.
Write the corresponding rollback file and create schema.lock.
Create .port-registry listing all current infra dependencies.
No feature PRs until phase 1 is fully merged.

Phase 2 — Strangle, One Violation Per PR
Each PR is deployed to staging and verified before the next PR opens.
Every violation category follows its own resolution sequence.
Tracing PRs are the highest priority. Nothing blocks them. They block everything else.
Scripts must be added before phase 2 ends. CI must be calling them.
Tracing must be fully instrumented before phase 2 ends. It is never deferred to phase 3.

Phase 3 — Harden
Enable linter rules blocking all cross-package imports.
Add breaking-change detection to every CI pipeline.
Add coupling-map violation count check — must be 0 on main.
Add schema.lock consistency check to CI.
Add .port-registry sync check to CI.
Add .contract-lock sync check to CI.
Add sunset-registry expiry check to CI.
Add migration rollback test to CI — both directions must pass.
Phase is complete when coupling-map.md is empty and all CI checks are green on main.

Non-Negotiables for Any Migration Work
Never break a running production system.
Never combine more than one violation fix in a single PR.
Never skip the contract step to save time.
Never remove dual-write before the consumer database is verified stable.
Never write a migration without a rollback file.
Never merge a PR that adds a new coupling without a coupling-map entry and phase plan.
Never proceed to the next phase while the current phase has open PRs.
Never rename a column in a single migration.
