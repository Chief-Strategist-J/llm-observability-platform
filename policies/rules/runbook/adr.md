╔══════════════════════════════════════════════════════════════════════════════════════╗
║   FAILURE-FIRST APPROACH — COMPLETE MEMORY MODEL                                   ║
║   ADR Format · Nygard · MADR · When · Why · How · Failure Modes                   ║
╚══════════════════════════════════════════════════════════════════════════════════════╝


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT FAILURE-FIRST ACTUALLY MEANS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Most engineers design for the happy path.
They ask: "how does this work when everything goes right?"

Failure-first engineers design for every failure path first.
They ask: "in how many ways can this be wrong before it is right?"

The mental inversion:

  HAPPY-FIRST THINKING (wrong order)
    Step 1 → design the happy path
    Step 2 → build the happy path
    Step 3 → discover failure paths in production
    Step 4 → patch failure handling under pressure
    Result → duct-tape architecture, hidden assumptions everywhere

  FAILURE-FIRST THINKING (right order)
    Step 1 → enumerate every failure mode before writing a line
    Step 2 → design the system so each failure mode is handled explicitly
    Step 3 → build the happy path inside that failure-safe structure
    Step 4 → production failures are expected, bounded, recoverable
    Result → architecture where failure is a first-class citizen

The reason this matters statistically:
  Google SRE data → 70% of production incidents caused by
                    assumptions that were never made explicit
  AWS post-mortems → 92% of catastrophic failures preceded
                     by signals the system was not designed to detect
  Netflix chaos data → systems designed failure-first recover
                       in average 4 minutes vs 47 minutes for systems
                       where failure was an afterthought


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE FAILURE-FIRST DECISION FRAMEWORK
Before any design decision — run it through this exact sequence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For every component, integration, or decision:

  QUESTION 1 — FAILURE ENUMERATION
  │  In how many ways can this fail?
  │  Not "can this fail?" — everything can fail
  │  The question is: enumerate ALL modes
  │
  │  Mode A → it is completely unavailable (crashed, network dead)
  │  Mode B → it is slow (latency 10x normal)
  │  Mode C → it returns wrong data silently (worst — no error signal)
  │  Mode D → it works but corrupts downstream state
  │  Mode E → it works intermittently (flapping)
  │  Mode F → it works but fails under specific conditions (load, time, data shape)
  │
  │  WRONG → "it might go down"
  │  RIGHT  → "it can fail in 6 distinct modes each with different detection
  │             and recovery characteristics"

  QUESTION 2 — DETECTION
  │  How will you know each failure mode has occurred?
  │  Before users tell you?
  │
  │  WRONG → alert when error rate exceeds 5%  (lagging, users already hurt)
  │  RIGHT  → alert when error budget burn rate exceeds 10x normal (leading)
  │            alert when p99 latency exceeds 2x baseline (before errors appear)
  │            alert when queue depth exceeds 80% of max (before backpressure)

  QUESTION 3 — BLAST RADIUS
  │  If this fails — what else fails with it?
  │  Draw the propagation path, not just the component
  │
  │  WRONG → "this service will be down"
  │  RIGHT  → "this service failing causes:
  │             → upstream callers to block on timeout (60 seconds each)
  │             → upstream thread pools to exhaust after N blocked calls
  │             → upstream to start rejecting all requests, not just this path
  │             → the user sees a completely unrelated error message"

  QUESTION 4 — RECOVERY
  │  How does the system recover — automatically or manually?
  │  What is the maximum acceptable recovery time?
  │
  │  WRONG → "we will restart the service"
  │  RIGHT  → "automatic: circuit breaker opens after 5 failures in 10s
  │              half-open probe every 30s
  │              closes when 3 consecutive probes succeed
  │             manual: runbook at docs/runbooks/service-x-recovery.md
  │             maximum tolerable downtime: 4 minutes per SLO"

  QUESTION 5 — PREVENTION
  │  What design decision eliminates this failure mode entirely
  │  instead of just handling it after it occurs?
  │
  │  WRONG → add retry logic to the caller
  │  RIGHT  → ask why the call needs to be synchronous at all
  │            if async is possible → the failure mode disappears
  │            async + idempotent consumer → retry is built into the model


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE SIX FAILURE ARCHETYPES
Every system failure is one of these six — know them before designing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ARCHETYPE 1 — CASCADE FAILURE
  What it is:   one component fails, callers block, their callers block,
                entire system hangs despite 99% of components being healthy
  Root cause:   synchronous call chains without timeout or circuit breaker
  Detection:    latency increases before error rate increases — watch p99
  Prevention:   async where possible, circuit breaker where sync required,
                bulkhead (isolated thread pool) per downstream dependency
  Wrong fix:    add more retries  ← makes cascade worse, amplifies load
  Right fix:    timeout fast, circuit break, return degraded response

ARCHETYPE 2 — SPLIT BRAIN
  What it is:   two nodes both believe they are the leader
                both accept writes, data diverges silently
  Root cause:   network partition with no fencing mechanism
  Detection:    data inconsistency discovered during reads — too late
  Prevention:   distributed consensus (Raft, Paxos) for leader election
                fencing tokens to invalidate stale leaders
                optimistic concurrency on all writes (version check)
  Wrong fix:    "our network is reliable, this won't happen"
  Right fix:    design assuming partition will occur, verify with chaos tests

ARCHETYPE 3 — THUNDERING HERD
  What it is:   a resource becomes available after being unavailable
                all waiting clients rush it simultaneously
                resource fails again immediately under the flood
  Root cause:   no jitter on retry, no rate limiting on reconnection
  Detection:    spike in requests immediately after recovery → second failure
  Prevention:   exponential backoff with random jitter on all retries
                connection pool with maximum size enforced
                circuit breaker half-open state limits probe traffic
  Wrong fix:    increase resource capacity  ← treats symptom not cause
  Right fix:    add jitter, cap reconnection rate, limit half-open probes

ARCHETYPE 4 — SILENT DATA CORRUPTION
  What it is:   system appears healthy, data is wrong
                discovered much later during audit or user complaint
                by then the corruption has propagated everywhere
  Root cause:   missing validation at boundaries, no checksums,
                ACL not translating external models completely
  Detection:    hardest to detect — requires data invariant assertions
                periodic reconciliation jobs comparing expected vs actual
  Prevention:   validate at every boundary, never trust data crossing a context
                idempotency keys to detect duplicate processing
                event sourcing gives full audit trail for forensics
  Wrong fix:    "our code is correct so data will be correct"
  Right fix:    assume data will be wrong, design detection first

ARCHETYPE 5 — CONFIGURATION DRIFT
  What it is:   service works in development, fails in production
                or works Monday, fails Thursday after a config change
                no one changed the code but behaviour changed
  Root cause:   configuration is mutable at runtime without deployment
                different environments have different configs with no audit
  Detection:    config changes are not logged, not versioned, not alerted on
  Prevention:   config as code — all config in version control
                immutable config per deployment — change config = new deployment
                startup validation — service refuses to start with invalid config
  Wrong fix:    document the config  ← documentation goes stale
  Right fix:    validate config in CI before deployment reaches production

ARCHETYPE 6 — DEPENDENCY HELL
  What it is:   upgrading library A breaks library B
                security patch requires downgrading C
                system cannot be updated without breaking something
  Root cause:   implicit transitive dependencies, no pinned versions,
                circular dependencies between packages
  Detection:    discovered when attempting upgrades — too late by then
  Prevention:   pin all dependency versions explicitly
                dependency graph must be acyclic (ADP)
                contract tests between services catch integration breaks
                separate upgrade cadence from feature development
  Wrong fix:    avoid upgrading dependencies  ← security debt accumulates
  Right fix:    automated dependency updates with test coverage to catch breaks


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADR FORMAT 1 — NYGARD (original 2011)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Nygard's insight: decisions decay — the code changes but the reasoning
  for why it was built that way disappears
  ADR is the antidote to decayed reasoning

  STRUCTURE
  │
  ├── Title
  │     ADR-{number}: {imperative sentence describing the decision}
  │     WRONG: "ADR-001: Database"
  │     RIGHT: "ADR-001: Use PostgreSQL as the event store for Temporal state"
  │     The title must state the decision, not the topic
  │
  ├── Status
  │     Proposed     → being discussed, not yet committed
  │     Accepted     → committed, in effect
  │     Deprecated   → was accepted, no longer recommended for new work
  │     Superseded   → replaced by ADR-{number}
  │     The status is the most important field for an engineer reading
  │     historical ADRs — it tells them whether to follow this or not
  │
  ├── Context
  │     What was the situation at the time of this decision?
  │     What forces were in play? (technical, team size, timeline, budget)
  │     What constraints existed that no longer exist?
  │     WRONG: "We needed a database"
  │     RIGHT: "At the time of this decision, we had a team of 3 engineers,
  │             a 6-week deadline, and no dedicated ops support.
  │             We needed a solution that required zero operational overhead
  │             for the first 6 months. The expected write volume was
  │             under 100 events/second."
  │     Context is why the same decision would not be made today
  │     if constraints have changed
  │
  ├── Decision
  │     State the decision in one clear sentence
  │     Then the rationale — not the description of what was done
  │     WRONG: "We will use Kafka for messaging"
  │     RIGHT: "We will use Kafka for messaging because:
  │              - we need guaranteed ordering within a partition
  │              - consumers must replay from arbitrary offsets
  │              - we expect 10+ consumers on the same event stream
  │              - RabbitMQ was eliminated because it does not support replay"
  │
  ├── Consequences
  │     What becomes easier because of this decision?
  │     What becomes harder because of this decision?
  │     What new problems does this decision create?
  │     WRONG: only listing the positive consequences
  │     RIGHT: "Positive: event replay, independent consumer scaling
  │             Negative: operational complexity of Kafka cluster,
  │                       requires schema registry for event versioning,
  │                       at-least-once delivery means all consumers must
  │                       be idempotent — this is a new requirement on
  │                       every team that writes a consumer"
  │     The negative consequences are the most important part
  │     They are what future engineers need to know
  │
  └── Failure mode this decision creates or eliminates
        NYGARD DID NOT INCLUDE THIS — but it should be there
        WRONG approach: no failure mode analysis in the ADR
        RIGHT approach: "This decision eliminates: synchronous coupling
                                                   between services
                         This decision creates: consumer lag as a new
                                               failure mode — monitor
                                               consumer group offset"


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADR FORMAT 2 — MADR (Markdown Architectural Decision Records, 2019)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  MADR's improvement over Nygard:
  forces you to document what you CONSIDERED AND REJECTED
  this is the most valuable information in any ADR
  because it prevents future engineers from re-evaluating
  already-rejected options and spending weeks reaching
  the same conclusion

  STRUCTURE
  │
  ├── Title
  │     Same as Nygard — imperative sentence stating the decision
  │
  ├── Status
  │     Same as Nygard
  │
  ├── Context and Problem Statement
  │     One paragraph answering:
  │     "What is the architectural question we are trying to answer?"
  │     Frame it as a question, not a statement
  │     WRONG: "We need messaging infrastructure"
  │     RIGHT: "How should services communicate when a user places an order
  │             and multiple downstream services (inventory, billing, notifications)
  │             must react — given that each may be temporarily unavailable
  │             and we need at-least-once processing guarantees?"
  │
  ├── Decision Drivers
  │     The constraints and forces that shaped the options
  │     Each one must be a specific, falsifiable criterion
  │     WRONG: "performance, scalability, reliability"
  │     RIGHT: "- must support at least 10 independent consumers on same stream
  │              - must retain messages for minimum 7 days for replay
  │              - must be operable by team without dedicated Kafka experience
  │              - must support exactly-one semantic within a single service boundary
  │              - monthly infrastructure cost must stay under $200"
  │
  ├── Considered Options
  │     List every option that was seriously evaluated
  │     Even ones quickly eliminated — document WHY they were eliminated
  │     WRONG: only listing the chosen option
  │     RIGHT:
  │       Option A: Kafka
  │       Option B: RabbitMQ
  │       Option C: AWS SQS + SNS
  │       Option D: Redis Streams
  │       Option E: HTTP callbacks (webhooks)
  │
  ├── Decision Outcome
  │     "Chosen option: {X} because {specific reason tied to decision drivers}"
  │     Not "because it is better" — because which decision driver it satisfies
  │
  ├── Pros and Cons of Each Option
  │     For every option listed — not just the chosen one
  │     This is what makes MADR more valuable than Nygard for large teams
  │
  │     Option A — Kafka
  │       GOOD: replay from arbitrary offset
  │       GOOD: partition ordering guarantee
  │       GOOD: consumer group isolation
  │       BAD:  operational complexity — requires ZooKeeper or KRaft
  │       BAD:  steep learning curve for team unfamiliar with log compaction
  │       BAD:  overkill for current volume (under 1000 events/day)
  │
  │     Option B — RabbitMQ
  │       GOOD: simpler operational model than Kafka
  │       GOOD: flexible routing with exchanges and bindings
  │       BAD:  no replay — once consumed, message is gone
  │       BAD:  fan-out to 10+ consumers requires complex topology
  │       ELIMINATED BECAUSE: no replay violates decision driver #2
  │
  │     Option C — AWS SQS + SNS
  │       GOOD: zero operational overhead, managed service
  │       GOOD: fan-out via SNS topic subscription
  │       BAD:  vendor lock-in to AWS
  │       BAD:  no ordering guarantee across messages (FIFO queue costs extra)
  │       BAD:  maximum retention 14 days — acceptable but tight
  │       ELIMINATED BECAUSE: vendor lock-in conflicts with multi-cloud requirement
  │
  ├── Failure Modes Created by This Decision
  │     MADR standard does not include this — add it explicitly
  │     For your platform:
  │
  │     "Choosing Kafka creates these new failure modes:
  │      FM-1: consumer lag — consumer falls behind producer
  │            detection: monitor consumer_group_lag metric
  │            threshold: alert if lag exceeds 10,000 messages
  │            recovery: scale consumer horizontally, add partitions
  │
  │      FM-2: partition leader election delay — 10-30s during broker failure
  │            detection: producer error rate spike
  │            recovery: automatic — Kafka re-elects leader
  │            user impact: up to 30s of write unavailability
  │
  │      FM-3: consumer poison pill — one malformed message blocks the partition
  │            detection: consumer stuck on same offset for >60s
  │            recovery: move message to dead letter topic, advance offset
  │            prevention: schema validation before publishing"
  │
  └── Links
        ADR that this supersedes (if any)
        ADR that this is related to
        External references (RFC, benchmark, incident report)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NYGARD vs MADR — WHEN TO USE WHICH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  USE NYGARD WHEN
  ├── small team, moving fast
  ├── decision is clear, few alternatives considered
  ├── you need to document existing decisions retroactively
  ├── ADR will be read by the same team that wrote it
  └── context is well-understood by all readers

  USE MADR WHEN
  ├── multiple teams share the codebase
  ├── significant alternatives were seriously evaluated
  ├── future engineers will not have the original context
  ├── the decision involves tradeoffs others might reverse without this record
  └── you want to prevent option re-evaluation (most common waste in large teams)

  FAILURE MODE OF NYGARD
  ├── consequences section lists only positives → misleading
  ├── context is vague → future reader cannot tell if context still applies
  └── no rejected alternatives → future engineer re-evaluates RabbitMQ
      spends 2 weeks, reaches same conclusion, wastes sprint

  FAILURE MODE OF MADR
  ├── pros/cons section becomes exhaustive academic exercise → never finished
  ├── too long → engineers stop reading them
  └── decision drivers are vague ("scalability") → every option satisfies them
      and the comparison is meaningless

  RIGHT APPROACH FOR BOTH
    Write the ADR before or during the decision — not after
    An ADR written after is a justification, not a record
    An ADR written during forces you to articulate the tradeoffs
    before committing — this is its highest value


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAILURE-FIRST ADR — THE EXTENDED FORMAT
Combines Nygard + MADR + failure mode analysis for complex systems
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ADR-{number}: {decision as imperative sentence}
  Status: {Proposed | Accepted | Deprecated | Superseded by ADR-{n}}
  Date: {when decided}
  Deciders: {who was in the room — accountability}

  ── PROBLEM ──────────────────────────────────────────────────────────────────
  What architectural question does this answer?
  Frame as a specific question with concrete constraints.

  ── FAILURE MODES WE ARE SOLVING ─────────────────────────────────────────────
  What failure modes does the current approach have?
  List each with: symptom / root cause / frequency / severity
  This is the most important section — it is why this decision exists

  ── DECISION DRIVERS ─────────────────────────────────────────────────────────
  Specific, falsifiable criteria
  Each criterion maps to one or more failure modes above

  ── OPTIONS CONSIDERED ───────────────────────────────────────────────────────
  Every option seriously evaluated
  For each: what failure modes does it solve / what new ones does it create?
  Elimination reason for rejected options (one sentence per rejection)

  ── DECISION ─────────────────────────────────────────────────────────────────
  Chosen: {option}
  Because: {maps to specific decision drivers}
  Not {alternative} because: {specific failure mode it does not solve}

  ── FAILURE MODES CREATED ────────────────────────────────────────────────────
  For each new failure mode this decision introduces:
    Name:       {short identifier}
    Symptom:    {what you observe}
    Detection:  {what metric or alert catches it}
    Threshold:  {specific number that triggers action}
    Recovery:   {automatic or manual, with runbook link}
    Prevention: {design-level mitigation}

  ── CONSEQUENCES ─────────────────────────────────────────────────────────────
  What becomes easier?
  What becomes harder?
  What new requirements does this place on other teams?
  What is the reversal cost if this decision turns out wrong?

  ── REVIEW TRIGGER ───────────────────────────────────────────────────────────
  Under what conditions should this ADR be revisited?
  WRONG: "when the team feels it should be reviewed"
  RIGHT: "review if: write volume exceeds 50,000 events/day,
                      team size exceeds 8 engineers,
                      Kafka operational incidents exceed 2/month"


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APPLIED TO YOUR LLM OBSERVABILITY PLATFORM
Concrete example of failure-first ADR for your actual system
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ADR-001: Route LLM inference calls through Kafka async
           instead of synchronous Streamlit → Cloudflare direct call
  Status:  Proposed
  Date:    2026-06-03
  Deciders: Jaydeep

  ── FAILURE MODES WE ARE SOLVING ─────────────────────────────────────────────
  FM-CURRENT-1: Cloudflare AI slow (3-8s) → Streamlit UI blocks → user
                sees spinner with no feedback → timeout after 30s
                Severity: HIGH — user-facing, kills UX
                Frequency: every request at Cloudflare p99

  FM-CURRENT-2: Cloudflare AI unavailable → Streamlit returns 500 →
                entire chat UI is down, no degraded mode possible
                Severity: CRITICAL — total feature unavailability

  FM-CURRENT-3: Cannot scale LLM processing independently of UI
                Severity: HIGH — one slow LLM request affects all users
                on the same Streamlit process

  ── DECISION DRIVERS ─────────────────────────────────────────────────────────
  D1: LLM call latency must not block UI thread
  D2: LLM service must be independently scalable
  D3: LLM service failure must not take down chat UI
  D4: every LLM request must be traceable end-to-end (OTel)
  D5: failed LLM requests must be retryable without user re-submission

  ── OPTIONS CONSIDERED ───────────────────────────────────────────────────────
  Option A: Kafka async (Streamlit → Kafka → LLM Worker → Kafka → Streamlit)
    Solves: FM-CURRENT-1, FM-CURRENT-2, FM-CURRENT-3
    Creates: consumer lag as new failure mode
             UI must poll or subscribe for response (complexity)

  Option B: Temporal workflow (Streamlit → Temporal → Cloudflare → Temporal → Streamlit)
    Solves: FM-CURRENT-2, FM-CURRENT-3 (retry built-in)
    Does not solve: FM-CURRENT-1 — Temporal still blocks on activity timeout
    Eliminates: manual retry implementation
    Creates: Temporal becomes dependency of LLM path (already dependency — acceptable)

  Option C: WebSocket with background thread
    Solves: FM-CURRENT-1 (UI does not block)
    Does not solve: FM-CURRENT-2, FM-CURRENT-3
    Creates: thread management complexity in Streamlit
    Eliminated: Streamlit's threading model makes this fragile

  Option D: Keep synchronous — tune timeout only
    Solves: nothing — reduces severity of FM-CURRENT-1 slightly
    Does not solve: FM-CURRENT-2, FM-CURRENT-3
    Eliminated: does not address root cause

  ── DECISION ─────────────────────────────────────────────────────────────────
  Chosen: Option A (Kafka async) for new requests
          Option B (Temporal) for retry and durability of failed requests
  Because: D1 + D2 + D3 + D5 all satisfied
           Temporal already exists in the stack — reuse not new dependency

  ── FAILURE MODES CREATED ────────────────────────────────────────────────────
  FM-NEW-1: consumer lag
    Symptom:  LLM responses delayed beyond expected window
    Detection: monitor llm_consumer_group_lag > 100 messages
    Threshold: alert at 100, critical at 1000
    Recovery:  scale LLM worker horizontally (stateless — safe to add instances)
    Prevention: LLM worker auto-scale based on consumer lag metric

  FM-NEW-2: UI polling complexity
    Symptom:  UI does not know when response is ready
    Detection: user reports "response never appeared"
    Prevention: Streamlit uses Server-Sent Events or polls every 500ms
                with timeout of 60s, then shows "try again" — not spinner forever

  ── REVIEW TRIGGER ───────────────────────────────────────────────────────────
  Review if:
    consumer lag exceeds 1000 messages more than twice per week
    Cloudflare AI p50 latency drops below 500ms
    (at that point synchronous may be acceptable again)
    team grows beyond 5 engineers working on the platform


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE MASTER FAILURE-FIRST CHECKLIST
Run this before writing any ADR, before any design decision
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  BEFORE DECIDING
  ├── Have I enumerated all failure modes of the current approach?
  ├── Have I mapped the blast radius of each failure mode?
  ├── Have I identified the leading indicator for each failure mode?
  ├── Have I evaluated every realistic option — not just the obvious one?
  └── Have I documented why I am NOT choosing each rejected option?

  BEFORE COMMITTING
  ├── What new failure modes does this decision create?
  ├── What is the detection mechanism for each new failure mode?
  ├── What is the recovery procedure for each new failure mode?
  ├── What is the reversal cost if this decision is wrong?
  └── Under what conditions should this decision be revisited?

  AFTER DECIDING
  ├── Is the ADR written before the implementation — not after?
  ├── Is the status correct?
  ├── Are the failure modes documented with specific metrics and thresholds?
  ├── Does the ADR link to related ADRs?
  └── Is there a review trigger condition — not just "when we feel like it"?

  THE ONE QUESTION THAT SUMMARISES FAILURE-FIRST
  ────────────────────────────────────────────────
  "If I am wrong about this decision —
   how will I know, how quickly will I know,
   and how expensive will it be to reverse?"

  If you cannot answer all three parts of that question
  before committing to the decision —
  you are not ready to commit to the decision.