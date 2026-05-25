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

