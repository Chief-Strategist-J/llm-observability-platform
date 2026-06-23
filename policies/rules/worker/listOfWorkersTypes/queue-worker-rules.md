
Queue Worker Rules
Job Processor Rules
Every job processor is idempotent. If the same job is processed twice, the result is identical.
Job payloads are immutable. The processor never modifies the received payload.
Jobs must complete within their declared timeout. Long-running jobs use Temporal instead.
Every job declares its retry policy in contracts/jobs/{name}.yaml.
Every job processor wraps its execution in a trace span.
Failed jobs are moved to a dead-letter queue after max retries. Dead-letter queues are monitored.
Job deduplication IDs are used for jobs that have external side effects.

Queue Worker Configuration Rules
Queue name is declared in contracts/jobs/{name}.yaml and read from environment config — never hardcoded.
Concurrency limit is declared per worker. Workers never auto-scale concurrency without an explicit limit.
Rate limits are declared per worker and per job type when required.
Backoff strategy for failed jobs is declared per job type.

Queue Worker — Per-Worker Structure
A queue worker polls a named queue and processes jobs one at a time or with controlled concurrency. Jobs are short-lived and non-durable compared to Temporal workflows.

{lang}/queue-{domain}-worker/
│
├── contracts/
│   └── jobs/
│       ├── {job-name}.yaml          ← job payload schema, retry policy, timeout
│       └── changelog.md
│
├── src/
│   ├── worker/
│   │   ├── config                   ← queue name, concurrency, rate limit, backoff
│   │   └── registry                 ← registers all job processors
│   │
│   ├── jobs/
│   │   └── {job-name}/
│   │       ├── index                ← public surface only
│   │       ├── processor            ← job execution logic
│   │       ├── types                ← JobPayload, JobResult
│   │       └── tests/
│   │           ├── unit/
│   │           └── integration/
│   │
│   └── shared/
│       ├── types/
│       ├── errors/
│       └── utils/
│
├── database/
│   └── migrations/
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── scripts/
│   ├── run.sh
│   ├── test.sh
│   ├── migrate.sh
│   └── health-check.sh
│
├── deploy/
├── build/
├── .env.example
├── .package-meta.yaml
└── .port-registry

===
Python — Queue Worker (Celery)
SDK: celery with redis or rabbitmq broker.
Job processor: Celery task function in jobs/{name}/processor.
Worker config: Celery app configuration in worker/config.
Registry: task autodiscovery or explicit task registration in worker/registry.
Retry policy: declared per-task in contracts/jobs/{name}.yaml and applied in processor.
OTEL: opentelemetry-instrumentation-celery for automatic task spans.
==
Python — Queue Worker (RQ)
SDK: rq with redis broker.
Job processor: plain function in jobs/{name}/processor.
Worker config: Queue name and connection in worker/config.
OTEL: manual span wrapping in activity processor.
==
Node / TypeScript — Queue Worker (BullMQ)
SDK: bullmq with ioredis.
Job processor: Worker class with a process function in jobs/{name}/processor.
Worker config: Queue name, concurrency, rate limiter in worker/config.
Registry: Worker instances created and registered in worker/registry.
OTEL: opentelemetry-instrumentation-bull or manual span wrapping per job.
===
Go — Queue Worker (Asynq)
SDK: github.com/hibiken/asynq with redis.
Task handler: implements asynq.HandlerFunc in jobs/{name}/processor.go.
Worker config: Concurrency, queues, retry in worker/config.go.
Registry: mux.HandleFunc registrations in worker/registry.go.
OTEL: manual span wrapping per task processor.
===
Java — Queue Worker (Spring Batch / Custom)
SDK: Spring Batch or custom queue consumer.
Job processor: ItemProcessor implementation in jobs/{name}/processor.
Worker config: Queue and thread pool configuration in worker/config.
OTEL: opentelemetry-java-instrumentation agent handles auto-instrumentation.
===
Queue Worker

queue-worker/
├── processors/
│   └── {processor-name}/
│       ├── index
│       ├── processor
│       ├── types
│       └── tests/
│           ├── unit/
│           │   └── processor.test
│           └── integration/
│               └── processor-flow.test
│
├── realtime/
│   ├── sse/
│   │   ├── index                        ← public surface only, no logic
│   │   ├── client                       ← connect, disconnect, send Last-Event-ID
│   │   ├── reconnect                    ← reconnect loop, delegates to retry only
│   │   ├── last-event-id                ← read, store, inject into reconnect header
│   │   ├── types
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── client.test
│   │       │   ├── reconnect.test
│   │       │   └── last-event-id.test
│   │       └── integration/
│   │           └── sse-flow.test        ← connect → job dequeued → status pushed → disconnect
│   │
│   ├── connection/
│   │   ├── index                        ← public surface only, no logic
│   │   ├── manager                      ← owns full connect/disconnect lifecycle
│   │   ├── state                        ← connected | connecting | reconnecting | closed
│   │   ├── types
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── manager.test
│   │       │   └── state.test
│   │       └── integration/
│   │           └── lifecycle.test       ← connect → job processed → disconnect
│   │
│   ├── retry/
│   │   ├── index                        ← public surface only, no logic
│   │   ├── backoff                      ← exponential + jitter, returns delay value only
│   │   ├── policy                       ← max attempts, max delay, reset on success
│   │   ├── types
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── backoff.test
│   │       │   └── policy.test
│   │       └── integration/
│   │           └── retry-exhaust.test   ← exhaust all attempts → final error emitted
│   │
│   └── index                            ← re-exports feature indexes only, no logic
│
├── scripts/
│   ├── health-check.sh                  ← verifies broker connection and queue accessibility
│   └── trace-check.sh                   ← confirms spans flowing to collector
│
└── index                                ← worker public surface only

Strict Rules — Queue Worker

realtime/ is called from processors/ only — after job completes or fails, never mid-execution
Root span is created when job is dequeued — before processor is called, carried into realtime/
sse/ is the only transport — no WebSocket, no long-poll ever added to queue worker
processor-flow.test must assert realtime/sse/client is called on both job success and job failure — both paths tested
last-event-id must be stored durably enough to survive a processor restart — tested in last-event-id.test
connection/manager is the only file that calls sse/client — processors never call client directly

