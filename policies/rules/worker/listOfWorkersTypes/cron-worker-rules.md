Cron Worker Rules

Every cron handler is idempotent. If the same schedule fires twice in the same window, the second run is safe.
Overlap policy is declared — what happens if a previous run is still running when the next fires.
Cron expressions are declared in contracts/schedules/{name}.yaml — never hardcoded in source.
Timezone is explicit. UTC is preferred. Local time zones are documented with justification.
Every cron handler wraps its execution in a trace span with the schedule name as an attribute.
Long-running cron tasks are delegated to Temporal workflows — not executed inline in the cron handler.

Cron Worker — Per-Worker Structure
A cron worker runs tasks on a defined schedule. Each scheduled task is a named handler with its own types and tests. Cron workers do not poll queues — they are triggered by a scheduler.



{lang}/cron-{domain}-worker/
│
├── contracts/
│   └── schedules/
│       ├── {schedule-name}.yaml     ← cron expression, input type, timeout
│       └── changelog.md
│
├── src/
│   ├── worker/
│   │   ├── config                   ← timezone, lock timeout, overlap policy
│   │   └── registry                 ← registers all schedule handlers
│   │
│   ├── schedules/
│   │   └── {schedule-name}/
│   │       ├── index
│   │       ├── handler              ← task logic, idempotent by design
│   │       ├── types
│   │       └── tests/
│   │           ├── unit/
│   │           └── integration/
│   │
│   └── shared/
│       ├── types/
│       └── utils/
│
├── database/migrations/
├── tests/
├── scripts/
├── deploy/
├── build/
├── .env.example
└── .package-meta.yaml

Cron Worker

cron-worker/
├── schedules/
│   └── {schedule-name}/
│       ├── index
│       ├── schedule
│       ├── types
│       └── tests/
│           ├── unit/
│           │   └── schedule.test
│           └── integration/
│               └── schedule-fire.test
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
│   │           └── sse-flow.test        ← connect → schedule fires → event pushed → disconnect
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
│   │           └── lifecycle.test       ← connect → reconnect → closed
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
│   ├── health-check.sh                  ← verifies scheduler connection, exits 0 if healthy
│   └── trace-check.sh                   ← confirms spans flowing to collector
│
└── index                                ← worker public surface only

Strict Rules — Cron Worker

realtime/ is called from schedules/ handler only — after schedule fires, before handler returns
sse/ is the only transport — no WebSocket, no long-poll ever added to cron worker
realtime/ never imports from schedules/ — one direction only, schedules/ imports realtime/
sse/reconnect delegates to retry/backoff and retry/policy only — no inline backoff logic
connection/state is mutated by connection/manager only — read-only everywhere else
Every test in sse/tests/unit/ mocks the network — no real connections in unit tests
sse-flow.test is the only file allowed to open a real SSE connection — integration only
schedule-fire.test must assert that realtime/sse/client is called exactly once per schedule fire