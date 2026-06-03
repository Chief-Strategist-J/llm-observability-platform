ARCHITECTURE MEMORY MODEL — Complete Pattern Reference
══════════════════════════════════════════════════════

━━━ 1. CONNASCENCE — Coupling Strength Spectrum ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COLDEST (change one side, tooling catches the other)
  │
  ├── CoN  — Name          → A calls B.processOrder()   rename = find+replace
  ├── CoT  — Type          → A and B agree on OrderId type
  ├── CoM  — Meaning       → 0=success, 1=error         fix: use enums
  ├── CoP  — Position      → fn(userId, orderId)         fix: named params / param object
  ├── CoA  — Algorithm     → both sides must bcrypt      fix: shared port/interface
  ├── CoE  — Execution     → A must run before B         fix: event-driven
  ├── CoTm — Timing        → A and B must run together   fix: async queues
  ├── CoV  — Value         → shared mutable state        fix: immutable value objects
  └── CoI  — Identity      → same object in memory       fix: IDs not references
  │
HOTTEST (change one side, the other breaks silently)

  DEGREE RULE:   CoI between 2 modules = manageable
                 CoI between 20 modules = system-wide catastrophe
  LOCALITY RULE: hottest coupling must be most local
                 CoI inside one class = fine
                 CoI across service boundary = critical failure


━━━ 2. SOLID — Class-Level Design Rules ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SAFEST application of each
  │
  ├── S — Single Responsibility
  │         one class = one reason to change
  │         smell: class name contains "And", "Manager", "Helper"
  │         fix:   split by axis of change, not by layer
  │
  ├── O — Open / Closed
  │         open for extension, closed for modification
  │         smell: switch/if-else on type throughout codebase
  │         fix:   Strategy pattern, polymorphism at the seam
  │
  ├── L — Liskov Substitution
  │         subtype must be usable anywhere parent is used
  │         smell: subclass throws NotImplementedException
  │         smell: subclass weakens preconditions or strengthens postconditions
  │         fix:   composition over inheritance
  │
  ├── I — Interface Segregation
  │         callers must not depend on methods they don't use
  │         smell: implementing interface forces empty method bodies
  │         fix:   split fat interfaces into role interfaces
  │
  └── D — Dependency Inversion
            high-level module owns the abstraction
            low-level module implements it
            smell: domain imports infrastructure package
            fix:   port defined in domain, adapter in infrastructure
            CRITICAL: the abstraction belongs to the CALLER not the IMPLEMENTER


━━━ 3. PACKAGE COHESION PRINCIPLES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ├── REP — Release Reuse Equivalency
  │         only package together what you release together
  │         smell: consumers import one util but get 40 unrelated classes
  │
  ├── CCP — Common Closure Principle
  │         things that change together live together
  │         smell: one business rule change touches 4 packages
  │         fix:   group by axis of change, not by type
  │
  └── CRP — Common Reuse Principle
            things reused together live together
            smell: importing Money forces dependency on InvoicePdf
            fix:   split so consumers only depend on what they use

  TENSION: CCP pulls related things together
           CRP pushes unrelated things apart
           your package boundaries are the resolution of this tension


━━━ 4. PACKAGE DEPENDENCY PRINCIPLES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ├── ADP — Acyclic Dependencies Principle
  │         no cycles in the package dependency graph
  │         smell: cannot release A without releasing B without releasing A
  │         fix:   extract package C that both A and B depend on
  │         fix:   invert one dependency with an interface
  │
  ├── SDP — Stable Dependencies Principle
  │         depend in the direction of stability
  │         instability = outgoing / (incoming + outgoing)
  │         0 = maximally stable   1 = maximally unstable
  │         smell: stable package depends on volatile package
  │         fix:   introduce abstraction owned by the stable package
  │
  └── SAP — Stable Abstractions Principle
            stable packages should be abstract
            unstable packages should be concrete
            the more depended-on a package is → the more abstract it must be
            domain core: abstract, stable, near 0
            infrastructure adapters: concrete, volatile, near 1


━━━ 5. DDD TACTICAL PATTERNS — Coupling Strength per Pattern ━━━━━━━━━━━━━━━

LOOSEST coupling (safest to change independently)
  │
  ├── Value Object
  │     defined by value, not identity
  │     immutable, validated in constructor
  │     operations return new instances
  │     no ID, no lifecycle, no repository
  │     coupling type: CoT (type agreement only)
  │
  ├── Domain Event
  │     past tense fact, immutable after creation
  │     carries enough data for consumer to act without querying back
  │     schema-versioned, upcast at read time not write time
  │     coupling type: CoN + CoT (name of event, shape of payload)
  │
  ├── Specification
  │     named, composable business rule object
  │     combinable: and / or / not
  │     testable in complete isolation
  │     coupling type: CoN only (caller knows rule name)
  │
  ├── Repository (interface)
  │     interface defined in domain, owned by domain
  │     implementation in infrastructure
  │     one per aggregate root, never per entity
  │     coupling type: CoT (type of aggregate returned)
  │
  ├── Domain Service
  │     stateless, spans multiple aggregates
  │     injected, never instantiated inside domain logic
  │     coupling type: CoN + CoT
  │
  ├── Aggregate Root
  │     consistency boundary
  │     only entry point from outside
  │     references other aggregates by ID only, never by object
  │     raises domain events, does not publish them
  │     coupling type: CoI only inside its own boundary (acceptable)
  │
  └── Process Manager / Saga
        stateful, persisted, versioned like an aggregate
        owns the sequencing of a multi-step business process
        stores compensations before taking next step
        coupling type: CoE (execution order) — contained inside the saga only
  │
TIGHTEST coupling (change one, change all)


━━━ 6. ARCHITECTURAL LAYERS — Dependency Direction ━━━━━━━━━━━━━━━━━━━━━━━━━

INNERMOST (no dependencies on anything outside)
  │
  ├── Zone 1 — Domain Core
  │     imports: nothing external
  │     contains: aggregates, value objects, domain events,
  │               domain services, ports (interfaces), specifications
  │     change trigger: business rule changes only
  │
  ├── Zone 2 — Application Shell
  │     imports: domain core only
  │     contains: use cases, sagas, policies, process managers
  │     change trigger: new user-facing capability
  │
  ├── Zone 3 — Ports (the inversion boundary)
  │     defined by: inner zone (domain or application)
  │     implemented by: outer zone (infrastructure)
  │     this is where dependency inversion is physically realised
  │
  └── Zone 4 — Infrastructure
        imports: everything inside
        contains: DB adapters, message bus adapters, HTTP handlers,
                  ACL translators, outbox relay, email, payment SDKs
        change trigger: technology changes, not business changes
  │
OUTERMOST (knows everything, owned by no one)

  ABSOLUTE RULE: zone number only increases outward
                 a lower zone NEVER imports a higher zone
                 enforce with fitness functions in CI


━━━ 7. BOUNDED CONTEXT RELATIONSHIPS — Strategic Coupling Spectrum ━━━━━━━━━

LOOSEST (maximum autonomy)
  │
  ├── Separate Ways
  │     no integration, deliberate duplication
  │     justified when: integration cost > integration value
  │     coupling: zero
  │
  ├── Published Language
  │     upstream publishes versioned formal schema
  │     any downstream consumes without coordination
  │     coupling: CoN + CoT on event schema only
  │
  ├── Open Host Service
  │     upstream exposes stable API, downstream consumes freely
  │     upstream owns the API contract
  │     coupling: CoN + CoT on API contract
  │
  ├── Anti-Corruption Layer (ACL)
  │     downstream translates upstream model at the boundary
  │     domain never sees external types
  │     coupling: CoN only (downstream knows upstream's name, ACL absorbs shape)
  │
  ├── Customer / Supplier
  │     downstream has input into upstream's API design
  │     contract negotiated, both teams sign off
  │     coupling: CoT on negotiated contract
  │
  ├── Conformist
  │     downstream adopts upstream model wholesale
  │     no translation layer
  │     justified: upstream model is well-designed, you have no leverage
  │     coupling: CoT + CoM (meaning of upstream concepts leaks in)
  │
  └── Shared Kernel
        tiny shared model, co-owned, both teams must sign off on changes
        only IDs and primitive value types should ever be here
        coupling: CoN + CoT + CoA (most coupled strategic pattern)
  │
TIGHTEST (change upstream = change downstream)


━━━ 8. DATA CONSISTENCY MODELS — Coupling vs Availability Tradeoff ━━━━━━━━━

MOST DECOUPLED (services can fail independently)
  │
  ├── Eventual Consistency + Idempotent Consumers
  │     events published async, consumers process when ready
  │     duplicate delivery guaranteed → consumer must handle it
  │     coupling: temporal decoupling (CoE eliminated)
  │
  ├── CRDT — Conflict-free Replicated Data Types
  │     merge function baked into data structure
  │     concurrent writes always merge without coordination
  │     coupling: CoA on merge function only
  │
  ├── Causal Consistency
  │     if B depends on A, any reader of B has also seen A
  │     stronger than eventual, weaker than strong
  │     coupling: CoE within a causal chain only
  │
  ├── Read-Your-Writes Consistency
  │     after a write, the same client always reads that write
  │     other clients may still be stale
  │     coupling: session-scoped CoV
  │
  └── Strong Consistency
        every read reflects most recent write
        requires synchronous coordination
        coupling: CoTm (timing) + CoE (execution order)
        use only where stale read causes real-world harm
  │
MOST COUPLED (all nodes must agree before responding)


━━━ 9. MESSAGING PATTERNS — Delivery Guarantee Spectrum ━━━━━━━━━━━━━━━━━━━━

LEAST RELIABLE → MOST RELIABLE
  │
  ├── Fire and Forget (at-most-once)
  │     message may be lost
  │     no retry, no ack
  │     use: non-critical analytics, metrics sampling
  │
  ├── At-Least-Once
  │     message will be delivered, may duplicate
  │     consumer MUST be idempotent
  │     this is the safe default for all systems
  │     implement: outbox pattern + consumer processed_events table
  │
  ├── Exactly-Once (within one system boundary)
  │     local transaction + outbox achieves this within one DB
  │     impossible to guarantee across a network in the general case
  │     "exactly-once" across services = at-least-once + idempotency
  │
  └── Transactional Outbox (the pattern that makes at-least-once safe)
        write event to outbox table in same DB transaction as state change
        relay reads outbox, publishes to bus, marks published
        if relay crashes → replays on restart → idempotency handles duplicate
  │
  DEAD LETTER QUEUE sits at the end of all of these
    permanent failure   → fix consumer code, then reprocess manually
    transient failure   → retry with exponential backoff + jitter
    poison pill         → isolate immediately, alert, never retry blindly


━━━ 10. SAGA PATTERNS — Long-Running Process Coupling ━━━━━━━━━━━━━━━━━━━━━━

  ├── Choreography
  │     each service reacts to previous event autonomously
  │     no central coordinator
  │     coupling: CoN on event names only
  │     use when: simple linear flows, maximum decoupling matters
  │     danger: process flow is implicit, spread across N services
  │
  └── Orchestration
        central process manager holds explicit state machine
        issues commands, reacts to responses
        coupling: CoN + CoE (orchestrator knows step order)
        use when: complex flows, many failure paths, timeout logic
        danger: orchestrator is a coordination point — must be persisted

  COMPENSATION RULE: store compensations BEFORE taking next step
                     compensate in reverse order
                     every step handler must be idempotent


━━━ 11. TDD LAYER MAPPING — Test Type per Coupling Surface ━━━━━━━━━━━━━━━━━

  ├── Aggregate / Value Object / Domain Service
  │     test type: pure unit test
  │     no fakes, no mocks — pure input → pure output
  │     if you need a fake here: domain has a dependency problem
  │
  ├── Use Case / Application Service
  │     test type: unit test with injected fakes
  │     fake all ports (repos, buses, external services)
  │     assert on observable output not internal calls
  │
  ├── Repository / Adapter
  │     test type: narrow integration test
  │     real DB in Docker (TestContainers)
  │     fake everything outside the adapter under test
  │
  ├── Event Schema / Context Boundary
  │     test type: consumer-driven contract test (Pact)
  │     consumer publishes contract
  │     provider CI verifies it independently
  │     no shared environment needed
  │
  ├── Full Use Case Slice
  │     test type: acceptance test
  │     real use case, real domain, fake infrastructure
  │     one per capability not per class
  │
  └── Architectural Constraints
        test type: fitness function in CI
        no domain imports infrastructure
        no package cycles
        instability only increases outward
        fails the build, not a code review comment


━━━ 12. PLANES — Runtime Separation of Concerns ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ├── Control Plane
  │     what it decides: is this request allowed to enter the system?
  │     auth, authz, rate limit, schema validation, routing, idempotency key
  │     stateless decisions from stateful policy stores
  │     coupling to domain: zero — it knows nothing about business rules
  │
  ├── Data Plane
  │     what it owns: durable storage, ordering, replication
  │     append-only for events — never update, never delete stored events
  │     ordering guaranteed within a partition
  │     source of truth — all other state is derived
  │
  ├── Messaging Plane
  │     what it does: fans out events from producers to consumers
  │     at-least-once is the contract
  │     dead letter queue is mandatory
  │     back-pressure is mandatory — unbounded queues crash under load
  │     consumer group offset tracking — commit AFTER processing, never before
  │
  └── Query Plane
        what it serves: pre-computed read models
        fully disposable — rebuild from data plane at any time
        never writes, never enforces invariants
        schema optimised per query, not per domain model


━━━ 13. THE MASTER DECISION TREE — Where Does This Code Live? ━━━━━━━━━━━━━━

  Is it a business rule or invariant?
  │
  ├── YES → does it belong to one concept?
  │           ├── YES, and that concept has identity → Aggregate Root method
  │           ├── YES, but it is defined by value → Value Object
  │           ├── YES, and it is a named composable rule → Specification
  │           └── NO, it spans multiple aggregates → Domain Service
  │
  ├── NO → does it orchestrate a sequence of business steps?
  │           ├── YES, short-lived → Use Case
  │           └── YES, long-lived with state → Process Manager / Saga
  │
  ├── NO → does it move or store data?
  │           ├── stores domain aggregates → Repository (interface in domain)
  │           ├── stores raw data (DB, cache, queue) → Infrastructure Adapter
  │           └── translates between two models → Anti-Corruption Layer
  │
  └── NO → does it observe the system?
              ├── logs, metrics, traces → Observability Infrastructure (always-on)
              └── read-optimised views → Projection / Read Model


━━━ 14. THE COUPLING AUDIT CHECKLIST — Apply to Every Arrow ━━━━━━━━━━━━━━━━

  For every dependency in your system, answer:

  ├── Q1: Is there exactly ONE service that writes to this store?
  │         NO → extract a service that owns it exclusively
  │
  ├── Q2: Does this call cross a service boundary synchronously?
  │         YES → replace with event unless user is waiting on screen
  │
  ├── Q3: If this dependency goes down, does my service go down?
  │         YES → introduce async queue between them
  │
  ├── Q4: Can I deploy this service without redeploying its dependency?
  │         NO → find the shared config, shared schema, or shared import
  │
  ├── Q5: Can I test this service without starting its dependency?
  │         NO → the dependency is not behind a port — add an interface
  │
  └── Q6: Does a change to this dependency require me to change this service?
            YES → the coupling is too hot — push it toward CoN or CoT

  EVERY "NO" or "YES" in the wrong column = one piece of coupling to remove
  Work through these in order — Q1 through Q6 — highest impact firstcomm