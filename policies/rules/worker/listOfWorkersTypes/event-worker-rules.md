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


Event Worker

event-worker/
├── handlers/
│   └── {handler-name}/
│       ├── index
│       ├── handler
│       ├── types
│       └── tests/
│           ├── unit/
│           │   └── handler.test
│           └── integration/
│               └── handler-flow.test
│
├── realtime/
│   ├── websocket/
│   │   ├── index                        ← public surface only, no logic
│   │   ├── client                       ← connect, disconnect, send, close
│   │   ├── reconnect                    ← reconnect loop, delegates to retry only
│   │   ├── heartbeat                    ← ping/pong, close on missed pong
│   │   ├── types
│   │   └── tests/
│   │       ├── unit/
│   │       │   ├── client.test
│   │       │   ├── reconnect.test
│   │       │   └── heartbeat.test
│   │       └── integration/
│   │           ├── ws-flow.test         ← connect → message received → ack sent → disconnect
│   │           └── heartbeat-miss.test  ← missed pong → connection closed → reconnect triggered
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
│   │           └── lifecycle.test       ← connect → heartbeat miss → reconnect → closed
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
│   ├── health-check.sh                  ← verifies broker connection and consumer group registration
│   └── trace-check.sh                   ← confirms spans flowing to collector
│
└── index                                ← worker public surface only


Strict Rules — Event Worker

realtime/ is called from handlers/ only — after message is processed, ack sent, before handler returns
websocket/ is the only transport — SSE forbidden, long-poll forbidden
websocket/heartbeat closes the connection on missed pong — it never silently continues
heartbeat.test must assert connection closes within configured pong timeout — not just that close was called
ws-flow.test must assert ack is sent before realtime/ publish — order is enforced in test
connection/manager is the only file that calls websocket/client — handlers never call client directly
W3C traceparent is extracted from message attributes in handlers/ — injected into realtime/ as span context, never read from global state