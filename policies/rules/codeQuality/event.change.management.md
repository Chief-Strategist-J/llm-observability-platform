# Event Sourcing, Change Processing, and State Management Algorithms

*Storing what happened, not just what is — and deriving every state that ever existed from a single immutable log.*

---

## 1. What Is This?

**Event Sourcing** is a persistence model where the system of record is not "the current value of a thing" but **the complete, ordered, immutable sequence of events that led to it**. Current state is never stored as ground truth — it is always a *derived value*, computed by replaying (folding over) the event log.

Formally:

```
State(t) = fold(apply, Events[0 .. t], InitialState)
```

**Change Processing** is everything that happens *after* an event is durably recorded: propagating it to other systems, computing derived views (projections), triggering side effects, feeding downstream consumers (search indexes, caches, analytics, other services) — usually via a stream-processing or CDC layer.

**State Management Algorithms** are the techniques used to make replaying a potentially infinite log tractable and fast: snapshotting, incremental projections, checkpointing, and windowed aggregation.

The three are one continuous pipeline: **Event Sourcing** decides what gets written and how it's structured; **Change Processing** decides how it moves; **State Management Algorithms** decide how state gets efficiently reconstructed from it.

**What it is not:**
- Not "just logging." Logs are usually for humans/debugging and are best-effort. An event store is a *primary, authoritative* data store — losing it loses the actual data, not just a trace of it.
- Not the same as an audit log bolted onto a CRUD system. In true event sourcing, there is no separate "current state" table that could ever disagree with the log — the log is the *only* durable truth; everything else is a cache.
- Not CDC by itself. CDC (tailing a database's change log) can be used to *approximate* event sourcing after the fact, but it captures "what changed in storage," not "what business event caused it" — a subtle but important difference addressed in §5.

---

## 2. Why? — From First Principles

### 2.1 The core problem this solves

A traditional CRUD system stores only the **latest value**. Every `UPDATE` destroys the information needed to answer:

- "What was this worth an hour/week/year ago?"
- "What sequence of actions led to this specific value?"
- "Why did this change — what was the intent, not just the delta?"

This is not a missing feature you can patch in later — it's structural. Once you `UPDATE row SET value = X`, the prior value and the *reason* for the change are gone unless you separately, deliberately, preserved them.

### 2.2 The first-principles fix: store intent, derive fact

If instead you record **`OrderShipped(order_id, timestamp, carrier)`** rather than mutating `orders.status = 'shipped'`, you have captured:

1. **What happened** (the fact, permanently, unforgeable after the fact)
2. **When it happened** (total or partial order in the log)
3. **Why the current state is what it is** (the full causal chain of events that produced it)

Current state becomes a pure, deterministic function of the event log — which yields the same benefits immutability gave the GitOps/Replication patterns already covered: **reproducibility** (replay the log anywhere, get the same state), and **time-travel** (replay only up to event N to see historical state), for free, as a structural consequence rather than a bolted-on feature.

### 2.3 Why "append-only" is the load-bearing physical property

Append-only writes are the cheapest possible disk operation (sequential write, no seek, no read-modify-write, no lock contention on existing rows) — this is not an incidental performance win, it's *why* event-sourced systems can sustain extremely high write throughput compared to update-heavy relational designs, and *why* the pattern composes so naturally with log-structured storage engines (LSM-trees, Kafka's own on-disk format) that share the same physical assumption.

### 2.4 The formal consequence: CQRS falls out naturally

Once writes are events and reads need *current, queryable* state, you are structurally forced to separate the write model (append the event) from the read model (a materialized, query-optimized projection built by folding events). This is not a stylistic choice — it's the direct consequence of §2.2: an event log is a terrible thing to query directly (you'd have to replay from the beginning every time), so a derived, continuously-updated read-side view becomes mandatory, not optional. This is why Event Sourcing and CQRS are almost always discussed together.

---

## 3. Core Architecture — Full Decision Trees

### 3.1 Decision Point 1 — How Are Events Stored?

```log
└── Q1: What is the physical/logical shape of the event store?
    ├── Per-Aggregate Stream
    │   ├── Each entity (order, account, cart) has its own append-only event stream
    │   ├── Strong ordering guarantee within one stream, none guaranteed across streams
    │   └── Natural fit for optimistic concurrency (§3.5) scoped to one aggregate
    ├── Global Append Log
    │   ├── All events across all aggregates land in one physically ordered log (Kafka-style)
    │   ├── Cross-aggregate ordering becomes possible (single global sequence number)
    │   └── Trade-off: single log becomes a scaling bottleneck without partitioning
    ├── Partitioned Log (hybrid)
    │   ├── Log is sharded by aggregate ID / partition key
    │   ├── Strong order within a partition, no order guarantee across partitions
    │   └── Most production systems (Kafka + event sourcing) land here
    └── Hybrid Store + Cache
        ├── Durable event store (Postgres table, EventStoreDB, Kafka) as source of truth
        └── In-memory or Redis cache of "current state per aggregate" for read-path speed
```

### 3.2 Decision Point 2 — How Is Current State Derived?

```log
└── Q2: How do you turn a log of events into a usable "current state"?
    ├── Full Replay From Genesis
    │   ├── Load ALL events for an aggregate, fold from InitialState
    │   ├── Correctness: always exactly right, by construction
    │   └── Cost: grows unboundedly with event count — unusable past a few thousand events
    ├── Snapshot + Replay Tail
    │   ├── Periodically persist (state, last_event_id) as a snapshot
    │   ├── On load: fetch latest snapshot, replay only events AFTER it
    │   └── Bounds replay cost to "events since last snapshot," not "events since forever"
    ├── Continuous Projection (Materialized View)
    │   ├── A separate process folds events incrementally as they arrive, keeping a live queryable table
    │   ├── Read path never replays anything — it just queries the already-folded view
    │   └── Requires a consistency-lag decision (§3.6)
    └── On-Demand Rebuild
        ├── Projection is deleted/corrupted → rebuilt by replaying the entire log from scratch into a fresh table
        └── The ultimate correctness backstop: if you trust the log, you can always regenerate any derived view
```

### 3.3 Decision Point 3 — How Are Events Processed Downstream?

```log
└── Q3: How does an event get from "written" to "used elsewhere"?
    ├── Synchronous In-Process Projection
    │   ├── Same transaction/process that writes the event also updates the read model
    │   ├── Strongest consistency (no lag) but couples write and read-model availability
    │   └── Risk: read-model update failure can block/rollback the write itself
    ├── Asynchronous Stream Processing
    │   ├── Event published to a broker (Kafka/Pulsar); consumers process independently
    │   ├── Read models become eventually consistent (bounded lag, not zero lag)
    │   └── Decouples write availability from read-model health entirely
    ├── Change Data Capture (CDC) as a Bridge
    │   ├── Tail the event store's own underlying storage log (WAL/binlog) instead of publishing explicitly
    │   ├── Useful for retrofitting event-driven behavior onto an existing CRUD database
    │   └── Captures storage-level change, not business-level intent (see §5)
    └── Batch Processing
        ├── Events accumulated and processed in scheduled batches (e.g., nightly aggregation)
        └── Highest latency, lowest per-event overhead — appropriate for analytics, not operational reads
```

### 3.4 Decision Point 4 — How Is Event Schema Evolution Handled?

```log
└── Q4: The business logic changed — how do old events stay interpretable?
    ├── Weak Schema (schemaless / JSON blob)
    │   ├── Add fields freely, consumers ignore unknown fields
    │   └── Risk: no compile-time safety, silent misinterpretation across versions
    ├── Versioned Event Types
    │   ├── OrderPlacedV1, OrderPlacedV2 as explicitly distinct types
    │   └── Consumers must handle every version they might ever see, forever
    ├── Upcasting
    │   ├── A transformation layer converts old-version events into the current version's shape on read
    │   ├── Old events on disk are NEVER rewritten — only their in-memory representation is upgraded
    │   └── Keeps the append-only/immutability guarantee intact (§2.2) while letting business logic evolve
    └── Weak Schema + Contract Testing
        ├── Combine schemaless storage with a consumer-driven contract test suite
        └── Trades runtime safety for deployment flexibility, catches breakage at CI time instead
```

### 3.5 Decision Point 5 — How Is Write Consistency Guaranteed?

```log
└── Q5: Two commands try to modify the same aggregate concurrently — what happens?
    ├── Optimistic Concurrency Control
    │   ├── Every command reads the aggregate's current version number
    │   ├── On write, checks that no other event was appended since that version
    │   └── Conflict → command rejected, caller retries against the new current version
    ├── Pessimistic Locking
    │   ├── Aggregate locked for the duration of command processing
    │   ├── Simpler reasoning, but kills throughput under contention
    │   └── Rare in practice for event-sourced systems (fights the append-only design)
    └── Single-Writer-Per-Aggregate (actor model)
        ├── Each aggregate instance is owned by exactly one in-memory actor/process at a time
        └── Serializes all commands for that aggregate through one execution context, eliminating races by construction
```

### 3.6 Decision Point 6 — How Are Read Models Kept in Sync?

```log
└── Q6: What's the consistency contract between the write side and the read side?
    ├── Synchronous Update
    │   ├── Read model updated in the same transaction as the event write
    │   └── Zero lag, but couples the two — a read-model outage can block writes
    ├── Asynchronous Eventual Consistency
    │   ├── Read model updated by a downstream consumer after the write commits
    │   ├── Bounded staleness window (milliseconds to seconds, typically)
    │   └── Requires the application/UI to tolerate "read-your-write" gaps (§4)
    └── Rebuild-on-Demand
        ├── Read model is not continuously maintained; it's computed fresh when queried (or on a cache-miss)
        └── Appropriate for rarely-queried or historical/analytical views where staleness doesn't matter
```

---

## 4. Edge Cases

- **Read-your-writes violation**: a user submits a command, then immediately queries a read model that hasn't caught up yet, and sees stale/absent data — the single most common event-sourcing UX bug.
- **Schema drift without upcasting discipline**: a field's meaning quietly changes between event versions, and a consumer written for the old meaning silently misinterprets historical events instead of erroring loudly.
- **Snapshot staleness / snapshot-log divergence**: a bug in the fold function is fixed, but existing snapshots were built with the buggy logic — replaying "since the snapshot" now produces a state that never would have existed if you'd replayed from genesis with the fixed logic.
- **Out-of-order delivery in distributed streaming**: partitioned logs guarantee order only within a partition; if related events land in different partitions, consumers can process them out of causal order unless explicit sequencing (causation IDs, vector clocks) is layered on.
- **Duplicate delivery / non-idempotent projections**: at-least-once delivery (the norm in distributed brokers) means the same event can be processed twice; a projection that isn't idempotent double-counts, double-charges, or double-sends.
- **Unbounded log growth**: an aggregate that lives for years (a long-running bank account) accumulates enormous event counts; without snapshotting (§3.2) replay time grows without bound.
- **Poison-pill events**: a single malformed or unexpectedly-shaped event crashes every consumer that tries to process it, potentially halting an entire partition's processing until manually skipped or fixed.
- **The "you can't fix history" trap**: a bug caused a wrong event to be recorded; you cannot ethically or safely mutate/delete it (that defeats the whole model) — the only correct fix is a **compensating event** that records the correction as a new fact, not an edit to the old one.
- **Cross-aggregate consistency without distributed transactions**: a business process spanning multiple aggregates (place order → reserve inventory → charge payment) has no single ACID transaction to rely on; failures mid-sequence require sagas/process managers (§8.8/§8.9), and getting the compensation logic wrong leaves the system in a state no one designed for.
- **Replay storms**: rebuilding a projection from genesis after a schema change or corruption can spike load dramatically if many projections rebuild simultaneously, potentially overwhelming the event store itself.

---

## 5. The Hardest / Most Difficult Thing

**Interpreting immutable historical facts correctly as the business rules that gave them meaning keep changing — without ever rewriting the facts themselves.**

An event like `DiscountApplied(order_id, percent=10)` was recorded under a specific, historical understanding of "how discounts work." Two years later, the discount *policy* has changed twice, the currency the percentage applied to has been redenominated, and a new team is trying to compute "what did this customer actually pay" for a historical report. The event is a permanent, correct record of *what happened* — but the *meaning* of that fact depends on business context that is not stored in the event itself and may no longer exist anywhere in living memory.

This is structurally different from (and arguably harder than) the replication/GitOps "immutability" problems already discussed, because those are about **agreeing on which fact is current**. This one is about **an agreed-upon, permanent fact whose interpretation function has silently changed underneath it** — upcasting (§3.4) can translate an event's *shape*, but it cannot resurrect *business context* that was never captured in the first place. The only real defense is capturing enough context *in* the event at write time (the policy version in effect, not just its result) — which requires anticipating, at the moment you design an event, which pieces of "current business context" future readers will need to correctly interpret a fact you're about to make permanent.

---

## 6. The Most Complex Part

**Coordinating a long-running business process across multiple independent aggregates using only events, with no distributed transaction to fall back on, while guaranteeing idempotent, correctly-ordered, exactly-once-effect processing at scale.**

This decomposes into three simultaneously-hard sub-problems that all have to be solved together:

1. **Process coordination without 2PC**: a saga/process manager must track "which step are we on" as its own piece of durable state, react to each step's success/failure event, and issue the next command or trigger a compensating action — essentially hand-rolling a tiny state machine per business process, replicated across however many concurrent instances of that process are in flight.
2. **Idempotency under at-least-once delivery**: every consumer in the pipeline must be written so that processing the same event twice produces the same result as processing it once (deduplication via idempotency keys, upserts instead of increments, etc.) — a property that is easy to state and surprisingly easy to violate accidentally (e.g., an innocent-looking `balance += amount` is *not* idempotent).
3. **Exactly-once *effect*, not exactly-once *delivery***: true exactly-once delivery across a network is provably impossible (a variant of the two-generals problem) — real systems instead achieve exactly-once *effect* by combining at-least-once delivery with idempotent processing and transactional checkpointing (commit "I processed event N" atomically with the side effect it caused).

The reason this is the single hardest part of the whole space: unlike Raft's consensus problem (which has a closed-form, provably-correct algorithm), saga/process-manager correctness is **domain-specific** — there is no generic algorithm that hands you the right compensating actions; you have to design them correctly for every business process, and get every idempotency boundary right, with no formal proof available to check your work.

---

## 7. Relation to Data and Modern AI

- **Feature stores as event-sourced systems**: many modern feature stores model feature values as a stream of point-in-time facts (`user_clicked(feature=x, ts=t)`) rather than mutable rows precisely so that training data can be reconstructed *as it looked at training time* — avoiding "feature leakage" from future information, a direct application of §2.2's time-travel property.
- **Training data reproducibility**: treating a training dataset as the result of folding an event log (raw ingestion events → cleaning/labeling events → final dataset) lets a team reproduce *exactly* which transformations produced a given training run, which is increasingly required for model audit and regulatory explainability.
- **Agent action logs as event sourcing**: autonomous/agentic AI systems that take real-world actions (send an email, place an order, call an API) are increasingly logged as an immutable event stream of "intents" and "effects," specifically so a bad agent decision can be audited, replayed, and — where possible — compensated for (§8.16 in the prior GitOps article; §8.16-equivalent here is the Compensating Event pattern, §8.16 below).
- **Real-time feature engineering via stream processing**: Flink/Kafka Streams-style windowed aggregation (§8.13) computes features like "purchases in the last 10 minutes" directly off an event stream, feeding low-latency inference — this is Change Processing (§1) applied directly to ML serving.
- **Vector index synchronization via CDC**: RAG systems commonly use CDC (§3.3) to detect document changes in a source-of-truth store and push corresponding re-embedding events into the vector index pipeline — the same drift/consistency problem noted in the Replication article's §7, approached here from the event-processing side.
- **Model retraining pipelines triggered by event thresholds**: drift-detection systems watch a stream of prediction/outcome events and emit a `RetrainingTriggered` event once a statistical threshold is crossed, turning MLOps retraining into just another event-sourced business process, governed by the same saga/process-manager machinery as any other multi-step workflow (§8.8/§8.9).

---

## 8. 17 Design Patterns Related to Event Sourcing and Change Processing

Each pattern is broken into **Definition**, **When to Use**, **Who**, and **How It Works Internally** to build a real mental model rather than a label.

### 8.1 Event Sourcing (Append-Only Event Log as Source of Truth)

- **Definition**: Persisting all changes to application state as a sequence of immutable, timestamped events, and treating current state as a value derived from that sequence rather than storing it directly.
- **When to Use**: When audit history, time-travel queries, or the ability to reconstruct "why" a state exists (not just "what" it is) are business requirements, not nice-to-haves.
- **Who**: The domain/aggregate layer of the application — the code that decides "this command results in these events" owns this pattern.
- **How It Works Internally**: A command handler validates a request against the current state (itself derived by folding prior events), and on success appends one or more new events to that aggregate's stream. No table is ever updated in place; the event log is the only write target.

### 8.2 CQRS (Command Query Responsibility Segregation)

- **Definition**: Splitting the write model (which processes commands and appends events) from the read model (which serves queries from a separately maintained, query-optimized view) into two distinct code paths.
- **When to Use**: Whenever the shapes needed for efficient writing (append an event) and efficient reading (a denormalized, indexed view) are different enough that one model can't serve both well — which is almost always true once Event Sourcing is in play (§2.4).
- **Who**: The write-side command handlers and the read-side projection builders — usually entirely separate services/modules.
- **How It Works Internally**: Commands flow into the write model and produce events; those events flow (synchronously or asynchronously, §3.6) into one or more projections that maintain denormalized, purpose-built tables for specific queries. A query never touches the write model at all.

### 8.3 Event Store / Event Stream per Aggregate

- **Definition**: A storage abstraction that groups all events for one entity instance into its own ordered, appendable stream, addressable by that entity's ID.
- **When to Use**: Whenever you need strong, guaranteed ordering for one entity's history, and clean isolation between unrelated entities' event histories.
- **Who**: The event store infrastructure (EventStoreDB, a Postgres table keyed by aggregate_id + sequence_number, or a Kafka topic partitioned by aggregate_id).
- **How It Works Internally**: Each append operation targets a specific stream ID and includes an expected version number (§8.7); the store guarantees events within one stream are read back in exactly the order they were written, while making no ordering promise across different streams.

### 8.4 Snapshotting

- **Definition**: Periodically persisting a fully-folded state (plus the event sequence number it corresponds to) so that future reconstructions don't need to replay from the very first event.
- **When to Use**: Whenever an aggregate's event count grows large enough that full replay becomes a measurable latency or cost problem — a threshold, not a default.
- **Who**: A background job or the aggregate-loading code path itself, triggered every N events or on a time interval.
- **How It Works Internally**: After every Nth event (or on a schedule), the current folded state is serialized and stored keyed by (aggregate_id, last_event_sequence). On load, the loader fetches the latest snapshot, then replays only the events with a sequence number greater than the snapshot's, folding them onto the snapshot's state instead of `InitialState`.

### 8.5 Projection / Materialized View

- **Definition**: A continuously-updated, query-optimized data structure built by folding a stream of events, kept separate from the event store itself.
- **When to Use**: Any time you need to query "current state" efficiently without replaying the log on every read — which is to say, on essentially every read path in a real system.
- **Who**: A projection worker/consumer process, subscribed to the relevant event stream(s).
- **How It Works Internally**: The worker consumes events in order, applies each one to an in-memory or database-backed view using a fold function specific to that view's shape, and commits the updated view (often alongside a checkpoint of "last event processed") so it can resume correctly after a restart.

### 8.6 Event Upcasting / Schema Versioning

- **Definition**: A translation layer that converts an old-version event's stored shape into the current version's shape at read time, without ever modifying the event as stored.
- **When to Use**: Whenever the business logic or event schema evolves and old, already-persisted events need to remain interpretable by code that only understands the newest schema.
- **Who**: A dedicated upcasting/deserialization layer sitting between the event store and every consumer (projections, command handlers).
- **How It Works Internally**: On read, each event's stored schema version is checked; if it's older than current, a chain of pure transformation functions (`V1→V2`, `V2→V3`) is applied in sequence before the event reaches application code, so business logic only ever has to reason about the latest shape.

### 8.7 Optimistic Concurrency Control (Expected Version Check)

- **Definition**: A conflict-detection mechanism where a write includes the version number it expects the target stream to currently be at, and is rejected if that expectation doesn't hold.
- **When to Use**: Whenever multiple commands might concurrently target the same aggregate and you need to detect (not prevent) conflicting concurrent writes cheaply, without locking.
- **Who**: The event store's append API, enforcing the check atomically at write time.
- **How It Works Internally**: The command handler loads an aggregate at version V, processes the command, and attempts to append new events with `expected_version = V`. The store atomically checks the stream's actual current version against V before appending; a mismatch means someone else wrote in between, and the append is rejected so the caller can reload and retry.

### 8.8 Saga Pattern (Choreography-Based)

- **Definition**: A way of coordinating a multi-step business process across services/aggregates where each service reacts to events published by the previous step and publishes its own event in turn, with no central coordinator.
- **When to Use**: When a business process spans multiple aggregates/services, no distributed transaction is available, and the steps' coordination logic is simple enough to be safely distributed across each participant.
- **Who**: Each individual service involved in the process, each independently subscribing to the events it cares about.
- **How It Works Internally**: Service A completes its step and emits `StepACompleted`; Service B is subscribed to that event, performs its own step, and emits `StepBCompleted` (or `StepBFailed`); a failure event triggers previously-completed services to run their own compensating logic in response — coordination emerges from a chain of event reactions, with no single piece of code that "knows" the whole process.

### 8.9 Process Manager (Orchestration-Based Saga)

- **Definition**: A dedicated, stateful component that explicitly tracks the progress of one multi-step business process instance and issues the next command based on which events it has seen so far.
- **When to Use**: When a business process is complex enough (many steps, branching logic, timeouts) that distributing its coordination logic across participants (§8.8) becomes hard to reason about or debug.
- **Who**: A dedicated process-manager service/aggregate, itself often event-sourced (its own state = fold of the events it has observed and the commands it has issued).
- **How It Works Internally**: The process manager subscribes to all events relevant to processes it tracks, maintains its own state machine (current step, timeout deadlines) per process instance, and on each relevant event, decides and issues the next command (or a compensating command) explicitly — all coordination logic lives in one place, unlike choreography.

### 8.10 Change Data Capture (CDC) as Event Source

- **Definition**: Deriving a stream of change events by tailing an existing database's internal change log (WAL/binlog), rather than the application explicitly publishing business events.
- **When to Use**: When retrofitting event-driven behavior onto an existing CRUD system where rewriting the write path to explicitly emit events isn't feasible.
- **Who**: A CDC connector/agent (Debezium and similar) running alongside the source database.
- **How It Works Internally**: The connector reads the database's low-level replication log (the same mechanism used for physical replication, §3.5 of the Replication article) and translates each row-level change into a structured change event, published to a broker — capturing "what changed in storage" rather than "what business event caused it" (the distinction flagged in §5).

### 8.11 Outbox Pattern (Transactional Outbox)

- **Definition**: A technique for reliably publishing an event to a broker *exactly when* a related database transaction commits, by writing the event to an "outbox" table in the same transaction, then relaying it separately.
- **When to Use**: Whenever a command needs to both update local state and publish an event, and you need to guarantee both happen or neither does — without a distributed transaction across the database and the broker.
- **Who**: The application's write path (writes to the outbox table) and a separate relay process (reads and publishes from the outbox).
- **How It Works Internally**: The command handler writes both its domain state change and a row representing the event to be published within one atomic local database transaction. A separate poller (or CDC connector, §8.10, tailing the outbox table specifically) reads unpublished rows and publishes them to the broker, marking them published — guaranteeing the event is never lost or published without the corresponding state change actually having committed.

### 8.12 Idempotent Consumer Pattern

- **Definition**: A consumer design that guarantees processing the same event more than once produces the same effect as processing it exactly once.
- **When to Use**: On every consumer in a system where the message broker offers at-least-once delivery (nearly universal in distributed streaming), which is to say, essentially always.
- **Who**: Every event-consuming service/projection in the pipeline, individually responsible for its own idempotency.
- **How It Works Internally**: Before applying an event's effect, the consumer checks a durable record of "have I already processed this event's unique ID?" (often the event ID itself, stored alongside the effect in the same transaction). If already processed, the event is silently skipped; if not, the effect is applied and the ID recorded atomically with it.

### 8.13 Stream Processing / Windowed Aggregation

- **Definition**: Continuously computing aggregate values (counts, sums, averages) over a moving time window of an event stream, rather than over a static, complete dataset.
- **When to Use**: Whenever you need up-to-date derived metrics (e.g., "purchases in the last 10 minutes") that must stay current as new events arrive, without recomputing from the entire history each time.
- **Who**: A stream-processing engine (Kafka Streams, Flink, Spark Streaming) running continuously alongside the event pipeline.
- **How It Works Internally**: Incoming events are grouped by a key and assigned to one or more time windows (tumbling, sliding, or session windows); an aggregation function updates each window's running value incrementally as events arrive, and emits the window's result either continuously or when the window closes.

### 8.14 Event-Carried State Transfer

- **Definition**: A pattern where events carry enough of the changed entity's state directly in their payload that downstream consumers never need to call back to the originating service to get more detail.
- **When to Use**: When downstream services need reasonably current data about an entity but you want to avoid tight synchronous coupling (a network call back to the source service for every event).
- **Who**: The publishing service (decides how much state to embed) and every downstream consumer that would otherwise need to query back.
- **How It Works Internally**: Instead of publishing a thin `CustomerUpdated(id)` event forcing consumers to fetch the customer record separately, the event itself includes the relevant fields (`CustomerUpdated(id, name, address, tier)`), letting consumers update their own local copies directly from the event payload with no additional network round trip.

### 8.15 Time-Travel / Temporal Query

- **Definition**: The ability to reconstruct and query the exact state of an aggregate (or the whole system) as of any specific past point in time, by replaying events only up to that point.
- **When to Use**: For audit/compliance requirements, debugging ("what did the system believe at 3:04am when this bug occurred"), or retraining ML models on historically-accurate feature snapshots (§7).
- **Who**: A query/tooling layer built on top of the event store, usually distinct from the normal real-time projections.
- **How It Works Internally**: Given a target timestamp or event sequence number, the replay engine folds events for the relevant aggregate(s) starting from `InitialState` (or the nearest snapshot before that point, §8.4) up to — but not past — the target point, producing state exactly as it existed at that moment.

### 8.16 Compensating Event (Correction Event, Not Mutation)

- **Definition**: A new event that records a correction to a past mistake as an explicit, honest fact ("this earlier event was wrong, here is the correction"), rather than editing or deleting the original event.
- **When to Use**: Any time a past event turns out to have been incorrect (a bug, a fraud reversal, a data-entry mistake) and the immutability guarantee (§2.2) must be preserved.
- **Who**: The domain/business logic layer — deciding what a correct compensating event *means* is a business decision, not a mechanical one (§6).
- **How It Works Internally**: Rather than deleting `PaymentCharged(amount=100)`, the system appends `PaymentCorrected(original_event_id, corrected_amount=90, reason=...)`. Every projection that folds this stream must know how to interpret correction events relative to the ones they correct — the history keeps both facts, permanently, and the current state reflects the correction without erasing the record that a mistake happened.

### 8.17 Checkpointing & Exactly-Once Processing

- **Definition**: A mechanism where a stream consumer atomically records "the last event I successfully processed" alongside the effect of processing it, so that a restart after a crash resumes from exactly the right point without reprocessing or skipping events.
- **When to Use**: In any long-running stream-processing job where crashes, restarts, and rebalances are expected operational events, not exceptions — which is to say, in essentially every production stream processor.
- **Who**: The stream-processing framework's runtime (Kafka Streams, Flink) in cooperation with the consumer's own state store.
- **How It Works Internally**: The consumer's offset (its position in the stream) is committed in the *same atomic transaction* as the state update it caused — either both happen or neither does. On restart, the consumer resumes from the last committed offset, and because the corresponding state update was committed atomically with it, no event is ever double-applied or silently skipped, achieving exactly-once *effect* even though delivery itself remains at-least-once.

---

## 9. Relationship Between the Patterns (Full Tree)

```log
└── Event Sourcing & Change Processing
    ├── Foundation Layer
    │   ├── Event Sourcing (1)
    │   │   ├── requires → Event Store per Aggregate (3)
    │   │   └── requires → Optimistic Concurrency Control (7)
    │   └── CQRS (2)
    │       └── consumes-output-of → Event Sourcing (1) to build Projections (5)
    ├── State Reconstruction Layer
    │   ├── Snapshotting (4)
    │   │   └── accelerates → full replay used by Time-Travel (15)
    │   ├── Projection / Materialized View (5)
    │   │   └── fed-by → Stream Processing (13) or synchronous update (§3.6)
    │   └── Time-Travel / Temporal Query (15)
    │       └── built-on → Snapshotting (4) + raw Event Store (3)
    ├── Evolution & Correction Layer
    │   ├── Event Upcasting (6)
    │   │   └── required-when → business logic changes but events (1) must stay immutable
    │   └── Compensating Event (16)
    │       └── required-when → a past event was factually wrong (never edit, only correct)
    ├── Cross-Aggregate Coordination Layer
    │   ├── Saga (Choreography) (8)
    │   │   └── alternative-to → Process Manager (9)
    │   └── Process Manager (Orchestration) (9)
    │       └── itself-often-implemented-as → Event Sourcing (1), recursively
    ├── Ingestion & Reliability Layer
    │   ├── Outbox Pattern (11)
    │   │   └── guarantees → events (1) are never lost relative to their causing transaction
    │   ├── Change Data Capture (10)
    │   │   └── alternative-source-of-events-to → explicit Event Sourcing (1) when retrofitting legacy systems
    │   ├── Idempotent Consumer (12)
    │   │   └── required-by → every consumer of (1), (10), or (13), given at-least-once delivery
    │   └── Checkpointing & Exactly-Once Processing (17)
    │       └── works-with → Idempotent Consumer (12) to achieve exactly-once effect
    └── Downstream Consumption Layer
        ├── Stream Processing / Windowed Aggregation (13)
        │   └── feeds → real-time Projections (5) and ML feature pipelines (§7)
        └── Event-Carried State Transfer (14)
            └── reduces-coupling-between → publishers of (1)/(10) and downstream consumers
```

---

## 10. Per-Pattern Pseudocode (Python-style, no comments, separated by topic)

### 10.1 Event Sourcing (Append + Fold)

```python
def append_event(event_store, stream_id, event, expected_version):
    return event_store.append(stream_id, event, expected_version)


def load_aggregate(event_store, stream_id, initial_state, apply_fn):
    events = event_store.read_stream(stream_id)
    state = initial_state
    for event in events:
        state = apply_fn(state, event)
    return state


def handle_command(event_store, stream_id, command, initial_state, apply_fn, decide_fn):
    current_state = load_aggregate(event_store, stream_id, initial_state, apply_fn)
    current_version = event_store.get_stream_version(stream_id)
    new_events = decide_fn(current_state, command)
    append_event(event_store, stream_id, new_events, current_version)
    return new_events
```

### 10.2 CQRS

```python
def dispatch_command(command_bus, command):
    handler = command_bus.resolve_handler(type(command))
    return handler.handle(command)


def dispatch_query(query_bus, query):
    handler = query_bus.resolve_handler(type(query))
    return handler.handle(query)


def register_projection_from_events(event_subscriber, projection_store, apply_fn):
    for event in event_subscriber.stream():
        current_view = projection_store.get(event.aggregate_id)
        updated_view = apply_fn(current_view, event)
        projection_store.put(event.aggregate_id, updated_view)
```

### 10.3 Event Store / Event Stream per Aggregate

```python
def append_to_stream(store_backend, stream_id, events, expected_version):
    actual_version = store_backend.get_version(stream_id)
    if actual_version != expected_version:
        raise ConcurrencyConflict(expected_version, actual_version)
    for event in events:
        store_backend.write(stream_id, event)
    return actual_version + len(events)


def read_stream(store_backend, stream_id, from_version=0):
    return store_backend.read(stream_id, from_version)
```

### 10.4 Snapshotting

```python
def maybe_snapshot(snapshot_store, stream_id, current_state, current_version, interval):
    if current_version % interval == 0:
        snapshot_store.put(stream_id, current_state, current_version)


def load_with_snapshot(event_store, snapshot_store, stream_id, apply_fn, initial_state):
    snapshot = snapshot_store.get_latest(stream_id)
    if snapshot is None:
        state, from_version = initial_state, 0
    else:
        state, from_version = snapshot.state, snapshot.version
    tail_events = event_store.read_stream(stream_id, from_version)
    for event in tail_events:
        state = apply_fn(state, event)
    return state
```

### 10.5 Projection / Materialized View

```python
def run_projection_worker(consumer, view_store, checkpoint_store, apply_fn):
    last_offset = checkpoint_store.get_offset()
    for event in consumer.poll_from(last_offset):
        current_view = view_store.get(event.aggregate_id)
        updated_view = apply_fn(current_view, event)
        view_store.put(event.aggregate_id, updated_view)
        checkpoint_store.set_offset(event.offset)


def rebuild_projection_from_scratch(event_store, view_store, apply_fn):
    view_store.clear_all()
    for event in event_store.read_all_events_in_order():
        current_view = view_store.get(event.aggregate_id)
        updated_view = apply_fn(current_view, event)
        view_store.put(event.aggregate_id, updated_view)
```

### 10.6 Event Upcasting / Schema Versioning

```python
def upcast_event(raw_event, upcast_chain):
    event = raw_event
    for upcaster in upcast_chain:
        if event.schema_version == upcaster.from_version:
            event = upcaster.transform(event)
    return event


def load_and_upcast(event_store, stream_id, upcast_chain):
    raw_events = event_store.read_stream(stream_id)
    return [upcast_event(e, upcast_chain) for e in raw_events]
```

### 10.7 Optimistic Concurrency Control

```python
def append_with_expected_version(store_backend, stream_id, events, expected_version):
    current_version = store_backend.get_version(stream_id)
    if current_version != expected_version:
        raise OptimisticConcurrencyError(expected_version, current_version)
    store_backend.append(stream_id, events)
    return current_version + len(events)


def retry_on_conflict(command_fn, max_retries):
    attempt = 0
    while attempt < max_retries:
        try:
            return command_fn()
        except OptimisticConcurrencyError:
            attempt += 1
    raise MaxRetriesExceeded(max_retries)
```

### 10.8 Saga Pattern (Choreography)

```python
def on_step_a_completed(event, event_bus):
    result = process_step_b(event.payload)
    if result.success:
        event_bus.publish(StepBCompleted(order_id=event.order_id, payload=result.payload))
    else:
        event_bus.publish(StepBFailed(order_id=event.order_id, reason=result.reason))


def on_step_b_failed(event, event_bus, compensation_fn):
    compensation_fn(event.order_id)
    event_bus.publish(StepACompensated(order_id=event.order_id))
```

### 10.9 Process Manager (Orchestration)

```python
def handle_process_event(process_store, command_bus, event):
    process_state = process_store.get(event.process_id)
    process_state.record_event(event)
    next_command = process_state.decide_next_step()
    if next_command is not None:
        command_bus.dispatch(next_command)
    process_store.put(event.process_id, process_state)


def start_process(process_store, process_id, initial_command, command_bus):
    process_state = ProcessState(process_id=process_id, step="started")
    process_store.put(process_id, process_state)
    command_bus.dispatch(initial_command)
```

### 10.10 Change Data Capture (CDC) as Event Source

```python
def cdc_tail_wal(wal_reader, event_publisher, checkpoint_store):
    last_offset = checkpoint_store.get_offset()
    for change_record in wal_reader.stream_from(last_offset):
        derived_event = translate_change_to_event(change_record)
        event_publisher.publish(derived_event)
        checkpoint_store.set_offset(change_record.offset)


def translate_change_to_event(change_record):
    return DomainEvent(
        aggregate_id=change_record.row_id,
        event_type=infer_event_type(change_record),
        payload=change_record.new_values,
    )
```

### 10.11 Outbox Pattern

```python
def write_with_outbox(db_transaction, aggregate_update, event):
    db_transaction.execute(aggregate_update)
    db_transaction.insert_outbox_row(event)
    db_transaction.commit()


def relay_outbox(outbox_reader, event_publisher):
    for outbox_row in outbox_reader.fetch_unpublished():
        event_publisher.publish(outbox_row.event)
        outbox_reader.mark_published(outbox_row.id)
```

### 10.12 Idempotent Consumer

```python
def idempotent_process(event, processed_id_store, apply_fn, state_store):
    if processed_id_store.contains(event.id):
        return state_store.get(event.aggregate_id)
    updated_state = apply_fn(state_store.get(event.aggregate_id), event)
    state_store.put(event.aggregate_id, updated_state)
    processed_id_store.add(event.id)
    return updated_state
```

### 10.13 Stream Processing / Windowed Aggregation

```python
def assign_to_window(event, window_size_seconds):
    window_start = (event.timestamp // window_size_seconds) * window_size_seconds
    return window_start


def update_windowed_aggregate(window_store, event, window_size_seconds, aggregate_fn):
    window_key = (event.key, assign_to_window(event, window_size_seconds))
    current_value = window_store.get(window_key)
    updated_value = aggregate_fn(current_value, event)
    window_store.put(window_key, updated_value)
    return updated_value


def close_expired_windows(window_store, current_time, window_size_seconds, emit_fn):
    for window_key, value in window_store.items_older_than(current_time - window_size_seconds):
        emit_fn(window_key, value)
        window_store.remove(window_key)
```

### 10.14 Event-Carried State Transfer

```python
def build_state_carrying_event(entity, event_type):
    return DomainEvent(
        aggregate_id=entity.id,
        event_type=event_type,
        payload=entity.to_dict(),
    )


def consume_state_carrying_event(local_store, event):
    local_store.put(event.aggregate_id, event.payload)
```

### 10.15 Time-Travel / Temporal Query

```python
def state_as_of(event_store, snapshot_store, stream_id, target_sequence, apply_fn, initial_state):
    snapshot = snapshot_store.get_latest_before(stream_id, target_sequence)
    if snapshot is None:
        state, from_sequence = initial_state, 0
    else:
        state, from_sequence = snapshot.state, snapshot.version
    events = event_store.read_stream_range(stream_id, from_sequence, target_sequence)
    for event in events:
        state = apply_fn(state, event)
    return state
```

### 10.16 Compensating Event

```python
def apply_correction(event_store, stream_id, original_event_id, corrected_payload, reason, expected_version):
    correction_event = DomainEvent(
        aggregate_id=stream_id,
        event_type="CorrectionRecorded",
        payload={"original_event_id": original_event_id, "corrected": corrected_payload, "reason": reason},
    )
    return append_event(event_store, stream_id, [correction_event], expected_version)


def fold_with_corrections(state, event, apply_fn):
    if event.event_type == "CorrectionRecorded":
        return apply_correction_to_state(state, event.payload)
    return apply_fn(state, event)
```

### 10.17 Checkpointing & Exactly-Once Processing

```python
def process_with_checkpoint(consumer, state_store, checkpoint_store, apply_fn, transactional_commit_fn):
    last_offset = checkpoint_store.get_offset()
    for event in consumer.poll_from(last_offset):
        current_state = state_store.get(event.aggregate_id)
        updated_state = apply_fn(current_state, event)
        transactional_commit_fn(state_store, event.aggregate_id, updated_state, checkpoint_store, event.offset)
```

---

## 11. Flow of Execution (End-to-End List)

1. A command arrives at the write model (10.1) and is validated against the aggregate's current folded state
2. Current state is loaded either by full replay, snapshot + tail (10.4), or an in-memory single-writer actor (10.7's concurrency scope)
3. Command handler decides which new event(s) result, and appends them with an expected-version check (10.7)
4. The append is written transactionally alongside an outbox row (10.11) to guarantee the event is never lost relative to the state change that caused it
5. A relay/CDC process (10.10, 10.11) publishes the event to a broker
6. Downstream consumers process the event idempotently (10.12), each tracking its own checkpoint (10.17)
7. Projection workers fold the event into materialized views (10.5), making it queryable on the read side
8. Stream processors compute windowed aggregates for real-time metrics/features (10.13)
9. Saga participants or a process manager react to the event to advance a cross-aggregate business process (10.8, 10.9)
10. If the event's schema is old, an upcasting chain (10.6) transforms it before any consumer touches its business meaning
11. If a past event turns out to be wrong, a compensating event is appended (10.16) — never an edit to history
12. Historical/audit queries reconstruct state as of any past point via snapshot + partial replay (10.15)
13. If a projection is lost or a schema changes meaning, it is rebuilt entirely from the immutable log (10.5's rebuild path)

---

## 12. References

- Fowler, M. — *Event Sourcing*, martinfowler.com, 2005
- Young, G. — *CQRS Documents*, cqrs.wordpress.com / cqrs.nu
- Kleppmann, M. — *Designing Data-Intensive Applications*, O'Reilly, 2017 (Ch. 11: Stream Processing)
- Vernon, V. — *Implementing Domain-Driven Design*, Addison-Wesley, 2013 (Aggregates, Event Sourcing, Sagas)
- Richardson, C. — *Microservices Patterns* (Saga, Outbox, CQRS), Manning, 2018
- Kreps, J. — *The Log: What every software engineer should know about real-time data's unifying abstraction*, engineering.linkedin.com, 2013
- Debezium Project — *Change Data Capture for Databases*, debezium.io
- Akidau, T. et al. — *The Dataflow Model* (windowing/watermarks in stream processing), VLDB, 2015
- Helland, P. — *Life Beyond Distributed Transactions: An Apostate's Opinion*, CIDR, 2007

---

*Event Sourcing turns "what is true now" from a stored fact into a computed one — every pattern above exists either to make that computation fast (snapshots, projections), safe under concurrency and evolution (optimistic concurrency, upcasting), reliable in transit (outbox, idempotent consumers, checkpointing), or coordinated across the many aggregates a real business process actually spans (sagas, process managers). The one thing none of them can ever do is edit the log itself — every correction is a new fact, never a rewritten one.*