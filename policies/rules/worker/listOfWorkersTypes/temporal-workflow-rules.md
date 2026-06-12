Worker Code Guidelines + Workflow & Migration Guide



Part A — Worker Code Guidelines

Temporal Workflow Rules
Workflow Rule Zero
A workflow definition must be deterministic. The same history must always produce the same sequence of commands. Any non-deterministic code in a workflow breaks replay and makes the workflow unrecoverable.

What Is Forbidden Inside a Workflow
Any IO — no network calls, no database queries, no file reads or writes.
Non-deterministic functions — no random number generation, no UUID generation, no current time via system clock.
Goroutines or threads spawned outside of the workflow SDK's coroutine model.
Global mutable state.
Direct calls to activity functions — activities must be called via the SDK's activity execution API.
Any SDK or library that is not workflow-safe.

What Is Required Inside a Workflow
Time via workflow.Now() or sdk equivalent — never via system clock.
Random values via workflow.GetRandom() or sdk equivalent — never via math/rand or random module.
All IO delegated to activities via the SDK's activity scheduling API.
All waits expressed via SDK timer, signal channel, or selector — never via sleep.
All concurrent execution via the SDK's goroutine or coroutine model.
Every workflow has a defined timeout at the workflow level and at the activity schedule level.

Signal Handler Rules
Signal handlers must be idempotent — the same signal delivered twice must not change final state.
Signal handlers must complete quickly — no blocking IO inside a signal handler.
Signal names are defined in the workflow interface contract. Changing a signal name is a breaking change.
Signal payloads are typed and documented in contracts/workflows/{name}.yaml.

Query Handler Rules
Query handlers must be side-effect-free — no state mutation inside a query handler.
Query handlers must return immediately — no waiting on signals or timers.
Query names are defined in the workflow interface contract. Changing a query name is a breaking change.

Activity Rules
Activity Rule Zero
Every activity must be idempotent. If an activity is retried after a failure, the second execution must produce the same result or safely detect and skip duplicate work.

Activity Requirements
All IO lives in activities — database queries, HTTP calls, file operations, queue publishes.
Every activity declares its StartToCloseTimeout. No activity runs without a timeout.
Every activity that runs longer than 10 seconds must call heartbeat on a regular interval.
Heartbeat carries the last checkpoint so that the activity can resume from that point on retry.
Activities are retried automatically by the Temporal server. Code must be safe to retry.
Idempotency keys or deduplication IDs are used for all external side effects — payments, emails, external API calls.
Activity errors are classified: non-retryable errors stop the retry loop, retryable errors allow retry.
Every activity wraps its execution in a trace span. The span includes the activity type and workflow ID.

Retry Policy Rules
Every activity has an explicit retry policy — never rely on the Temporal default.
MaxAttempts is always declared. Unbounded retries are forbidden without a compensating mechanism.
BackoffCoefficient and MaxInterval are always declared.
NonRetryableErrorTypes lists every error that should not be retried.
Retry policy is documented in contracts/workflows/{name}.yaml alongside the activity it applies to.


Temporal Worker — Per-Worker Structure
A Temporal worker hosts workflow definitions and activity implementations. Workflows contain only deterministic orchestration logic. Activities contain all IO, side effects, and external calls.

{lang}/temporal-{domain}-worker/
│
├── contracts/
│   └── workflows/
│       ├── {workflow-name}.yaml     ← input/output type, signal/query names
│       └── changelog.md             ← every interface change documented here
│
├── src/
│   ├── worker/
│   │   ├── config  ← task queue name, max concurrent wf, max concurrent act
│   │   └── registry  ← registers all workflows and activities with the worker
│   │
│   ├── workflows/
│   │   └── {workflow-name}/
│   │       ├── index          ← public surface only — workflow type export
│   │       ├── workflow       ← deterministic logic only, zero IO
│   │       ├── signals/       ← one file per signal handler
│   │       │   └── {signal-name}
│   │       ├── queries/             ← one file per query handler
│   │       │   └── {query-name}
│   │       ├── types   ← WorkflowInput, WorkflowOutput, all signal and query types
│   │       └── tests/
│   │           ├── unit/
│   │           └── replay/          ← history replay tests — run on every PR
│   │
│   ├── activities/
│   │   └── {activity-name}/
│   │       ├── index  ← public surface only — activity function export
│   │       ├── activity ← actual work — IO allowed, side effects allowed
│   │       ├── types  ← ActivityInput, ActivityOutput
│   │       └── tests/
│   │           ├── unit/
│   │           └── integration/
│   │
│   ├── schedules/   ← cron and scheduled workflow definitions
│   │   └── {schedule-name}
│   │
│   └── shared/
│
├── database/
│   ├── migrations/
│   │   ├── 0001_init.sql
│   │   └── 0001_init.rollback.sql
│   └── schema.lock
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── replay/                      ← workflow history replay test suite
│   └── e2e/
│
├── scripts/
├── deploy/
│   ├── docker/
│   └── kubernetes/                  ← stage 3 only
│
├── build/
│   └── Dockerfile
│
├── .env.example
├── .package-meta.yaml
└── .port-registry

=====
Python — Temporal Worker
SDK: temporalio (official Python SDK).
Worker entrypoint: src/worker/config and src/worker/registry wired together in run.sh.
Workflow class: decorated with @workflow.defn. Lives in workflows/{name}/workflow.
Activity function: decorated with @activity.defn. Lives in activities/{name}/activity.
Signal handlers: decorated with @workflow.signal. One file per signal in workflows/{name}/signals/.
Query handlers: decorated with @workflow.query. One file per query in workflows/{name}/queries/.
Types: Pydantic dataclasses or dataclasses. Serializable to JSON.
Linter: ruff --select ALL, zero warnings.
Types: mypy --strict, zero errors.
Test runner: pytest with pytest-cov, minimum 80% coverage.
Replay tests: temporalio.testing.WorkflowEnvironment with saved history JSON files.
Migrations: alembic or raw SQL via migrate.sh.
OTEL: opentelemetry-sdk with temporalio interceptors for workflow and activity spans.
====
Node / TypeScript — Temporal Worker
SDK: @temporalio/worker, @temporalio/workflow, @temporalio/activity, @temporalio/client.
Workflow functions: live in workflows/{name}/workflow. Sandboxed — no Node.js built-ins.
Activity functions: live in activities/{name}/activity. Full Node.js access.
Signal handlers: defined inside workflow function using setHandler. One file per signal.
Query handlers: defined inside workflow function using setHandler. One file per query.
Types: TypeScript interfaces or Zod schemas. Must be JSON-serializable.
Linter: eslint --max-warnings 0 and prettier.
Types: tsc --strict, no any without justification.
Test runner: vitest, minimum 80% coverage.
Replay tests: TestWorkflowEnvironment with history files in tests/replay/.
OTEL: @opentelemetry/sdk-node with @temporalio/interceptors-opentelemetry.
===
Go — Temporal Worker
SDK: go.temporal.io/sdk.
Workflow function: registered with worker.RegisterWorkflow. Lives in workflows/{name}/workflow.go.
Activity function: registered with worker.RegisterActivity. Lives in activities/{name}/activity.go.
Signal and query handlers: defined inside workflow function using workflow.GetSignalChannel and workflow.SetQueryHandler.
Types: plain Go structs with json tags. Must be serializable.
Linter: golangci-lint strict config, zero warnings.
Test runner: go test ./..., minimum 80% coverage.
Replay tests: worker.WorkflowReplayer with saved history files.
OTEL: go.opentelemetry.io/otel with go.temporal.io/sdk/interceptor for spans.
Migrations: golang-migrate with raw SQL files.
===
Java — Temporal Worker
SDK: io.temporal:temporal-sdk.
Workflow interface: annotated with @WorkflowInterface and @WorkflowMethod. Lives in workflows/{name}/index.
Workflow implementation: implements the workflow interface. Lives in workflows/{name}/workflow.
Activity interface: annotated with @ActivityInterface. Lives in activities/{name}/index.
Activity implementation: implements the activity interface. Lives in activities/{name}/activity.
Signal handlers: annotated with @SignalMethod on the workflow interface.
Query handlers: annotated with @QueryMethod on the workflow interface.
Types: Java POJOs with Jackson annotations. Must be JSON-serializable.
Linter: checkstyle, pmd, spotbugs, zero violations.
Test runner: junit5 with jacoco, minimum 80% coverage.
Replay tests: WorkflowReplayer.replayWorkflowExecutionFromResource with history files.
OTEL: opentelemetry-java-instrumentation with temporal-opentelemetry interceptor.
Migrations: flyway or liquibase, SQL files only.
