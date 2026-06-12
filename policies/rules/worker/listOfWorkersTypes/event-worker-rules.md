Event Worker Rules

Every event handler is idempotent. Duplicate event delivery must not cause duplicate side effects.
Events are consumed in order within a partition. Cross-partition ordering is not guaranteed and is not relied upon.
Consumer group name is declared in contracts/events/{name}.yaml and read from environment config.
Event handlers extract and propagate W3C traceparent from the message attributes before any processing.
Failed event processing is handled via dead-letter topic after max retries. Dead-letter topics are monitored.
Event schema version consumed is pinned in .contract-lock.

Event Worker — Per-Worker Structure
An event worker subscribes to one or more topics or subjects and reacts to incoming events. Each event type has its own handler. The worker does not produce events — it only consumes and reacts.

{lang}/event-{domain}-worker/
│
├── contracts/
│   └── events/
│       ├── {event-name}.yaml        ← event payload schema, consumed version pinned
│       └── changelog.md
│
├── src/
│   ├── worker/
│   │   ├── config                   ← broker address, consumer group, topic list, concurrency
│   │   └── registry                 ← registers all event handlers
│   │
│   ├── handlers/
│   │   └── {event-name}/
│   │       ├── index
│   │       ├── handler              ← event processing logic, idempotent
│   │       ├── types                ← EventPayload, HandlerResult
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

