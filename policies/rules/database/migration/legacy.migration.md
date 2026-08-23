# Migrating 100+ Microservices Off a Legacy Database — Scale, Behavior Preservation, and How Engineers Actually Trace It

*Not a new failure taxonomy — the practitioner's playbook for the specific, brutal problem: N services, one deprecated database, and a hard requirement that nothing observably changes while you replace the ground underneath all of them.*

---

## 0. Framing — Why This One Is Different

The previous four articles covered causal reconstruction, deep failure-class algorithms, and speed-of-resolution tooling. This article is about one specific, extremely common, extremely dangerous project: **a legacy database that 100-200 microservices depend on is being deprecated, and it must be replaced without any of those services — or their users — noticing.** Everything here is grounded in how this is actually done in production organizations, cross-checked against documented industry practice (Fowler's strangler fig and evolutionary database design, GitHub's Scientist library, Michael Feathers' characterization testing, and real published migrations at this exact scale) rather than derived from first principles alone.

---

## 1. What Is This, Precisely?

The problem has four properties simultaneously, and losing sight of any one of them is how these projects fail:

1. **Scale**: 100-200 independently-deployed, independently-owned services read from and write to one shared legacy store.
2. **Deprecation pressure**: the legacy database is being end-of-lifed — a vendor is sunsetting it, a license is expiring, it can no longer scale, or nobody left on staff can operate it safely.
3. **Behavior preservation**: every one of those 100-200 services must see the *exact same observable behavior* after the migration as before — not "equivalent," not "improved," identical, including quirks nobody remembers the reason for.
4. **Traceability under fire**: when something *does* drift, you need to find out which service, which query, which row, and why — fast — without the luxury of a maintenance window to think it over.

**What it is not**: a schema redesign project, a performance optimization project, or a microservice re-architecture project — even though all three are tempting to bundle in "while we're already touching this." Bundling them is the single most common way these projects blow their timeline and their safety margin (see Wrong Assumption #3 in §3).

---

## 2. Why? — First Principles Specific to This Problem

### 2.1 The database's actual behavior is the real specification, not any document describing it

<cite index="22-1">Hyrum's Law states that with a sufficient number of users of an API, all observable behaviors of the system will be depended on by somebody</cite> — regardless of what the interface contract or documentation claims. At 100-200 services deep, "sufficient number of users" isn't a hypothetical threshold, it's already been crossed for every single quirk your legacy database has: its exact rounding behavior, its exact NULL-sorting order, its exact error message text that some service parses with a regex, its exact timing characteristics that another service's retry logic was tuned against. **None of this is written down anywhere. All of it is the real spec.**

### 2.2 Coupling multiplies with N, and a shared database is a distributed system nobody designed

100-200 services sharing one database are not "100-200 services with a database dependency" — they are **one giant, undocumented, implicit distributed system**, coupled to each other through every shared table, every trigger, every stored procedure, every transaction boundary that happens to span two services' logical domains. Migrating the storage layer means you are about to re-implement the coupling mechanism itself for a system whose actual coupling graph has never been drawn.

### 2.3 The dependency map is an epistemic problem before it's a technical one

No single person, team, or document has ever had a complete, current picture of which of the 100-200 services touch which tables, in which ways, for what reason. This isn't a documentation failure to be fixed by writing better docs — it's a structural consequence of scale and organizational turnover: the engineer who wrote a batch job three years ago that reads this table once a quarter has since left, and the job still runs. **You cannot instrument, test, or safely migrate what you don't know exists** — which means dependency discovery is not a preliminary step you complete once, it is a continuous process that runs for the life of the migration (§8, Category H).

### 2.4 Migration risk scales with blast radius at the moment of cutover, not with the size of the change

A schema-level one-line change is "small" by code-diff standards but can instantly break every one of 200 services if flipped globally and atomically. The controlling variable for risk isn't how much code changed — it's **how many services are exposed to the change at the instant it takes effect.** This is the entire justification for every incremental-cutover pattern in this article (§8, Categories A, C, D).

### 2.5 Behavioral equivalence is a harder target than correctness

"Correct" means matching a specification. This migration has no specification — only twenty years of accumulated, undocumented, occasionally-buggy actual behavior. The target isn't "build it right," it's **"build something that produces the identical output the old, possibly-wrong system produces, for every input the old system has ever actually received."** This inversion — preserving bugs on purpose, deliberately, as a first-class goal — is the single hardest mental adjustment for engineers new to this kind of project (see Wrong Assumption #6).

### 2.6 Drift compounds silently over the transition window

Any period where two stores are simultaneously "true" (a dual-write window, a shadow-sync window) is a period where small, individually-invisible discrepancies accumulate — a missed write here, a race condition there — exactly the way floating-point rounding error compounds across repeated operations. **The longer that window stays open, the more the two stores diverge, and the harder reconciliation becomes** — which is why every credible migration playbook treats the dual-write window as a liability to be minimized in duration, not a comfortable steady state to live in indefinitely (§9, Technique T19).

---

## 3. What We Assume Wrong vs. How to Think Right

This table is the single most load-bearing artifact in this article. Every pattern in §8 exists to operationalize one of these corrections.

| # | Wrong Assumption | Why It Feels True | Right Mental Model | Why It's Actually Right |
|---|---|---|---|---|
| 1 | "If it's not in the documented API/schema, nobody depends on it" | The schema doc/API contract *is* the officially sanctioned interface | Assume every observable behavior is depended on by someone (Hyrum's Law, §2.1) | With 100-200 real consumers, the space of "things someone might depend on" has empirically been exhausted many times over |
| 2 | "Passing our test suite means behavior is preserved" | Tests are how we normally validate correctness | Tests only cover cases someone imagined; production traffic is the real, unbounded input distribution — needs parallel-run comparison against live traffic (§8, E1) | A test suite is a *sample* of possible inputs; the legacy system's actual callers are the *population* |
| 3 | "We should redesign the schema properly while we're already touching it" | It seems wasteful to migrate ugly data 1:1 just to redesign it again later | Separate "migrate" from "improve" completely — migrate 1:1 first, redesign as an independent later project (§9, T3) | If both behavior AND shape change simultaneously, a regression can't be attributed to either cause — you've destroyed your own ability to isolate the variable |
| 4 | "A scheduled maintenance window solves the consistency problem" | Downtime historically made migrations simple — stop writes, copy data, resume | At 100-200 independently-deployed services owned by different teams, synchronizing a downtime window is an organizational impossibility, not a technical inconvenience | Getting 100-200 teams to agree to simultaneous downtime, and to actually be ready at that instant, essentially never happens in practice at this scale |
| 5 | "The new database performing faster proves the migration succeeded" | Performance is measurable and satisfying to report | Performance parity and behavior parity are different, independent goals — a faster wrong answer is still wrong | Edge-case error codes, sort ordering, and transactional semantics don't show up in a latency graph |
| 6 | "This weird legacy behavior is clearly a bug — let's finally fix it" | Engineers are trained to fix bugs on sight | Chesterton's Fence: don't remove a quirk until you know why it exists and who depends on it (§9, T2) | A "fix" applied silently during a migration is indistinguishable, in the resulting diff, from an accidental regression — and Hyrum's Law says someone is very likely relying on it |
| 7 | "The architecture docs / the DBA / the wiki know every consumer of this database" | Someone, somewhere, is supposed to own that knowledge | Assume the dependency map is wrong until verified empirically via access logs (§9, T7 / §8, H1) | No static document has ever stayed accurate against 100-200 independently-changing services over years of organizational churn |
| 8 | "Dual writes are simple — just write to both stores" | It's a small code change, conceptually | Without idempotency keys and continuous reconciliation, dual writes silently diverge under any partial failure | A write that succeeds on one store and fails on the other, with no compensating check, produces silent, permanent drift that surfaces months later as "corrupted" data |
| 9 | "We found the dependents in our audit — discovery is done" | An audit feels like a completed, bounded task | Discovery is a continuous, monitored process for the full migration duration, not a single pass (§9, T9) | A quarterly batch job, an annual reconciliation script, or a once-a-year compliance report simply won't appear in any short observation window |
| 10 | "99% sync accuracy is basically done" | 99% sounds like an A-grade | At the row counts real legacy databases hold, 1% failure is still an enormous absolute number of silently wrong records (§9, T14) | 1% of 500 million rows is 5 million individually wrong records — "basically done" and "actually done" are very far apart at this scale |
| 11 | "Rollback means reverting the last deploy" | That's how rollback works for stateless services (see the GitOps article in this series) | Mid-migration, some services are on the new store and some aren't — rollback must be defined per-entity/per-shard via an explicit migration-state machine (§8, D4) | A single global on/off switch can't express "these 40 already-cut-over services stay put, these 12 mid-flight ones revert" |
| 12 | "We'll decommission the legacy DB once the migration 'looks done'" | Once the primary services are cut over, it feels finished | Decommission only after a staged, monitored access-revocation period shows genuinely zero access (§8, I1) | "Looks done" from the migrating team's vantage point misses the forgotten cron job, the BI dashboard, and the other team's quiet integration |
| 13 | "The new system should eventually do everything the old one did, and more" | It seems wasteful not to improve capability while rebuilding | During migration, the only goal is behavioral equivalence to what currently exists — "should do more" is a separate, later backlog | Scope creep during a behavior-preservation project reintroduces exactly the untestable, unbounded surface area you're trying to eliminate |
| 14 | "This is a database problem — hand it to the DBA team" | It's literally about a database | It's an organization-wide coordination problem wearing a database costume; the sync mechanism is the easy 20%, coordinating 100-200 teams' cutover readiness is the hard 80% (§9, T21) | The technical mechanism (CDC, dual-write) is well-documented and solved; nobody has solved "get 100 teams to test and confirm readiness on schedule" with a library |
| 15 | "Zero mismatches in a day of shadow-diffing means we're safe to cut over" | A quiet comparison window feels like validation | Traffic patterns vary by day-of-week, month-end close, and annual cycles — a short quiet window says nothing about rare-but-critical paths | Financial month-end batch jobs, annual renewal logic, and leap-year edge cases only fire on their own schedule, not yours |

---

## 4. Core Architecture — Full Decision Trees

### 4.1 Decision Point 1 — Big Bang vs. Incremental, and How Do You Slice 100-200 Services Into Waves?

```log
└── Q1: How do you sequence migrating 100-200 services off one shared store?
    ├── Big Bang Cutover (name it to rule it out at this scale)
    │   ├── Only viable for a handful of tightly-coordinated services with a real downtime budget
    │   └── At N=100-200 across independent teams: essentially never viable — Wrong Assumption #4
    └── Strangler Fig / Incremental Replacement
        ├── Introduce a façade/router in front of the legacy store that can direct each request to old or new
        ├── Wave-Grouping Strategy
        │   ├── Bulkhead-Isolated Waves: group services so a wave's blast radius can't leak into another wave
        │   ├── Domain-Boundary-First Sequencing: migrate along bounded contexts, least-coupled services first
        │   └── Dependency-Ordered Waves: topologically sort the service dependency graph, migrate leaves first
        └── Central Migration Team vs. Per-Team Self-Service
            ├── Central team owns tooling/automation, individual teams execute a repeatable checklist
            └── Reduces the coordination cost that Wrong Assumption #14 identifies as the real bottleneck
```

### 4.2 Decision Point 2 — How Do You Keep Two Stores in Sync During the Transition?

```log
└── Q2: The legacy store and the new store must both be "true" for a while — how do they stay consistent?
    ├── Dual-Write (application writes to both, synchronously or async)
    │   └── requires → idempotency keys + continuous reconciliation, or Wrong Assumption #8 bites you
    ├── CDC-Based Synchronization (tail the legacy DB's own commit log)
    │   ├── Doesn't require every writing service to change its code
    │   └── Captures storage-level change, not business intent (same caveat as the Event Sourcing article, §3.3 there)
    ├── Shadow Table Strategy
    │   ├── A synchronized duplicate table kept current via triggers or CDC
    │   └── industry case studies confirm this approach for large-scale extractions
    └── Backfill + Live-Tail Combination
        ├── Bulk-copy historical data once (backfill)
        └── CDC live-tail catches everything written since the backfill started, closing the gap
```

### 4.3 Decision Point 3 — How Do You Cut Over Reads Safely?

```log
└── Q3: 200 services need to start reading from the NEW store — how, without breaking anyone?
    ├── Percentage-Based Traffic Shifting (1% → 10% → 50% → 100%, per service)
    ├── Per-Tenant / Per-Shard Cutover (segment by customer or data partition, not just percentage)
    ├── Feature-Flag-Gated Read Source Selection (a flag per service decides which store answers a read)
    └── Circuit-Breaker-Gated Cutover Fallback
        └── auto-reverts a service to the legacy read path if new-path error rate crosses a threshold
```

### 4.4 Decision Point 4 — How Do You Cut Over Writes Safely?

```log
└── Q4: Writes are riskier than reads to move — what's the sequencing?
    ├── Expand Phase
    │   ├── Add new structures alongside old ones — purely additive, backward-compatible
    │   └── the safe first step: old clients remain completely unaware anything changed
    ├── Migrate Phase
    │   ├── Application dual-writes to both old and new structures
    │   └── Backfill existing data into the new structure
    └── Contract Phase
        ├── Remove the old structure only once NOTHING still depends on it (§8, Category H)
        └── each phase is deployed independently, safe to run while old and new application versions are both live
```

### 4.5 Decision Point 5 — How Do You Verify Behavior Equivalence, Not Just Data Equivalence?

```log
└── Q5: Data matching isn't enough — does the SYSTEM'S BEHAVIOR match?
    ├── Parallel-Run / Shadow Comparison (Scientist-style)
    │   ├── Run old (control) and new (candidate) code paths on the same input
    │   ├── Always return the control's result to the real caller — candidate never affects production
    │   └── Compare results, log mismatches, without the caller ever knowing an experiment ran
    ├── Characterization Testing / Golden Master
    │   ├── Capture the legacy system's ACTUAL current outputs as ground truth, before writing new code
    │   └── the target: this describes the actual behavior of existing code, not the intended behavior
    ├── Invariant Assertion Harness (business-rule checks evaluated on both paths)
    └── Production Traffic Replay (record real requests, replay offline against the new system)
```

### 4.6 Decision Point 6 — How Do You Discover the FULL Set of Dependents Before You Touch Anything?

```log
└── Q6: Who ACTUALLY talks to this database — not who's documented, who's REAL?
    ├── Query-Log / Access-Log Mining (Ground Truth)
    │   └── the only technique multiple independent practitioners agree actually works at this scale — logging every statement, or using engine-level access statistics, since no static document can be trusted
    ├── Deprecation Warning Injection
    │   └── log a warning/metric every time a to-be-removed path executes, building a live usage census
    ├── Access Tripwire / Read-Only Freeze Canary
    │   └── deliberately restrict access and see who breaks — a real, if blunt, technique practitioners use when logging alone isn't feasible
    └── Cross-Repo Static Dependency Graph Extraction
        └── AST/grep-based scan across all 100-200 services' repos for direct DB client usage
```

### 4.7 Decision Point 7 — How Do You Roll Back Mid-Migration, When Services Are in Mixed States?

```log
└── Q7: Something's wrong, and 40 services are cut over while 12 are mid-flight — now what?
    ├── Dual-Path Rollback Switch (per service, flip its own flag back to legacy)
    ├── Point-in-Time Consistency Checkpoint (snapshot BOTH stores right before cutover, as a rollback reference)
    └── Blast-Radius-Scoped Rollback Boundary
        └── ensure Wave 3's rollback never requires touching Wave 1 or Wave 2 — waves must be truly independent
```

### 4.8 Decision Point 8 — How Do You Decommission the Legacy Store Safely?

```log
└── Q8: Every service THINKS it's migrated — how do you PROVE the legacy store is safe to delete?
    ├── Staged Access Revocation (read-write → read-only → no access, bake period at each stage)
    ├── Legacy Read-Replica Safety Net (keep a read-only replica alive post-cutover for a bake period)
    └── Final Freeze & Cold Archive (snapshot final state before deletion, for audit/compliance)
```

---

## 5. Edge Cases Specific to Scale + Migration

- **The quarterly/annual job you never saw**: a batch job that runs once a quarter or once a year will not appear in any short discovery window, no matter how thorough — discovery must run for a full annual cycle before decommissioning is safe.
- **Dual-write divergence invisible for months**: a write that silently fails on the new store but succeeds on the legacy one produces no error anyone sees — until a read from the new store returns stale data and someone escalates a "data corruption" incident that's actually a migration bridge bug.
- **Foreign-key/transactional invariants lost when splitting one database into several**: the legacy DB enforced "an order can't exist without a valid customer" via a database-level constraint; once split across two new services and two new databases, that invariant has no enforcement mechanism at all unless explicitly rebuilt (§8, F3).
- **Auto-increment ID collisions on merge-back or rollback**: if both stores generate their own primary keys independently during a dual-write window, a rollback to the legacy store can produce ID collisions with rows the new store already created.
- **Character encoding and collation mismatches**: a legacy database's specific string-comparison/sort behavior (case sensitivity, accent folding) rarely matches a new engine's defaults exactly, and sort-order-dependent code silently returns differently-ordered results.
- **Floating-point/decimal rounding drift**: different database engines round intermediate calculations differently; for financial data this produces penny-level discrepancies that accumulate and eventually fail a reconciliation audit.
- **Read-after-write consistency assumptions breaking silently**: a service that always assumed strong consistency from the legacy RDBMS can start seeing eventually-consistent staleness from a new distributed store, and the resulting bugs look like random, unreproducible glitches.
- **Hidden dependents discovered only during decommissioning**: the single most common real-world migration failure mode — a service, script, or BI tool nobody remembered breaks the moment access is finally revoked.
- **Cutover during a traffic pattern nobody tested**: a percentage ramp validated during normal traffic can fail catastrophically the first time it's live during a genuine peak (Black Friday, month-end close) that simply hadn't occurred yet during the rollout window.
- **Partial rollback breaking cross-service transactions**: if Service A rolls back to the legacy store but Service B (which A calls mid-transaction) is already fully cut over to the new store, a workflow that spanned both can be left in a state neither system alone can resolve.
- **The migration bridge itself becoming a new single point of failure**: a dual-write adapter or CDC pipeline, if it goes down, can silently stop synchronizing while both "sides" of the migration appear healthy individually.

---

## 6. The Hardest Thing — Dependency Discovery Is an Epistemic Problem, Not a Technical One

The single hardest part of this entire class of project is not building the dual-write bridge, not writing the shadow-diff comparator, and not sequencing the cutover waves — all of those are, comparatively, solved problems with well-documented patterns (§8). **The hardest part is answering, with actual confidence, the question "who depends on this database, and how" — because no one, at any point in the organization, has ever had a complete, accurate answer to that question, and the cost of being wrong is only discovered after the legacy system is gone.**

This is fundamentally different from a bug you can eventually find by looking hard enough — it's a **negative-existence problem**: you're trying to prove the absence of dependents, and absence of evidence in your logs is not evidence of absence in reality, especially for anything that runs less often than your observation window is long. §2.3 established why this happens structurally (organizational turnover, undocumented batch jobs, forgotten integrations); §4.6 laid out the decision tree of *techniques* for attacking it.

**Worked example — the discovery technique that actually works, per practitioners who have tried the alternatives:** when a database engineer on a public PostgreSQL mailing list asked how to find which tables were genuinely unused before cleanup, another experienced practitioner's direct answer was that there is no way to know this <cite index="57-1">short of logging every statement executed against the database</cite> — static documentation, ORMs, and code search all miss dynamically-constructed queries, forgotten scripts, and BI tool connections. The practical, validated approach combines two things running *concurrently, for a full annual cycle*, not once:

```
enable_full_query_logging(legacy_db, retention_days=400)
for each_distinct(client_application_name, source_ip) in query_log:
    register_dependent(table=parsed_table_name, caller=client_application_name, last_seen=timestamp)

for table in candidate_tables_for_removal:
    if table not in registered_dependents_seen_in(last_400_days):
        flag_for_staged_access_revocation(table)
    else:
        notify_owning_team(table, dependents=registered_dependents[table])
```

Even this is not a single pass — it must run continuously through decommissioning (§8, H2's deprecation-warning logging is the same mechanism applied as a standing practice rather than a one-time audit), and it must be combined with the blunter but real technique some engineers use when logging alone isn't trusted: <cite index="58-1">deliberately revoking access to a suspected-unused table and observing what breaks</cite> — done only after staged, reversible access reduction (§8, I1), never as a single irreversible step.

---

## 7. The Most Complex Part — Building a Behavior-Equivalence Oracle That Doesn't Lie in Either Direction

Comparing the legacy system's output to the new system's output sounds simple: run both, diff the results. In practice, this comparator is the single most complex engineering artifact in the entire migration, because it must solve a calibration problem that gets *harder*, not easier, as you get more careful:

**A naive diff produces overwhelming false positives** — a generated UUID, a `created_at` timestamp, floating-point rounding in the seventeenth decimal place, or non-deterministic row ordering in an unordered query will all show up as "mismatches" on every single comparison, drowning the rare genuine bug in thousands of expected, meaningless noise. Teams that don't solve this either drown in false alarms and start ignoring the tool entirely, or — worse — **over-correct by normalizing away real differences**, silently masking an actual behavior regression as "just more noise," which is a false negative with real production consequences.

**Worked example:** GitHub's own description of their Scientist library makes exactly this tension explicit — <cite index="29-1">the tool runs both the old and new code paths, compares their outcomes, and logs any mismatches or exceptions</cite>, but critically <cite index="31-1">the comparison behavior itself is overridable</cite> precisely because a raw equality check is usually wrong for real-world data:

```python
def compare(control_result, candidate_result, normalization_rules):
    normalized_control = apply_normalization(control_result, normalization_rules)
    normalized_candidate = apply_normalization(candidate_result, normalization_rules)
    return normalized_control == normalized_candidate

def apply_normalization(result, rules):
    for field in rules.ignored_fields:
        result = strip_field(result, field)
    for field in rules.rounded_fields:
        result = round_to_precision(result, field, rules.precision[field])
    for field in rules.unordered_fields:
        result = sort_canonically(result, field)
    return result
```

The genuinely hard part is that `normalization_rules` cannot be written once — it must be *discovered incrementally*, field by field, comparison by comparison, as the migration surfaces each new category of expected-but-harmless divergence, while a human reviews every newly-proposed normalization rule to make sure it isn't quietly hiding a real bug (this human-review gate is the actual bottleneck at scale — with 100-200 services each producing their own result shapes, someone has to make this judgment call hundreds of times, and getting it wrong in either direction is expensive).

---

## 8. 44 Patterns for Migration at Scale

Each entry: **Definition · When · Who · How.**

### Category A — Migration Strategy & Sequencing

**A1. Strangler Fig Migration** — *Definition:* <cite index="4-1">a façade intercepts requests to the legacy system and routes each one to either the legacy application or a new service</cite>, letting features migrate incrementally while consumers keep using the same interface. *When:* the default strategy for any legacy-replacement project too large to safely swap in one step. *Who:* the platform/migration team building and owning the façade. *How:* the façade's routing table is the only thing that changes as each capability migrates — consumers never need to know a migration is happening at all.

**A2. Branch by Abstraction** — *Definition:* introduce a stable interface/seam in front of the current implementation before building the replacement behind it, so the swap becomes a single implementation-pointer change. *When:* migrating a specific subsystem's implementation without changing its calling contract. *Who:* the team owning the code being migrated. *How:* callers are refactored to depend on the new abstraction first (a no-op change, low risk); only afterward is the concrete implementation swapped behind that abstraction.

**A3. Expand-Contract (Parallel Change)** — *Definition:* a three-phase schema evolution technique — add new structures (expand), dual-write and backfill (migrate), then remove old structures only once nothing depends on them (contract). *When:* any schema change that must remain safe across a rolling deployment where old and new application versions run concurrently. *Who:* the service team making the schema change, coordinated with the migration team for the contract phase's dependency check. *How:* <cite index="16-1">each of the three phases is deployed independently and is safe to run while both application versions are simultaneously live</cite>.

**A4. Bulkhead-Isolated Migration Waves** — *Definition:* grouping the 100-200 services into batches whose blast radius is structurally contained — a failure in Wave 3 cannot cascade into Wave 1 or Wave 2. *When:* planning migration order for a large service fleet. *Who:* the central migration team, in consultation with each wave's service owners. *How:* waves are chosen so that no two waves share an un-migrated cross-dependency; each wave completes and bakes fully before the next begins.

**A5. Domain-Boundary-First Sequencing** — *Definition:* migrating along bounded-context lines, starting with the least-coupled, most self-contained services. *When:* choosing which services go in the earliest, lowest-risk waves. *Who:* architects mapping the service dependency graph. *How:* a topological sort of the dependency graph identifies "leaf" services with few incoming dependents — these migrate first, building confidence and tooling maturity before tackling the tightly-coupled core.

**A6. Central Migration Team / Embedded Support Model** — *Definition:* a dedicated team owns migration tooling and automation centrally, while individual service teams execute a repeatable, templated checklist rather than each improvising their own approach. *When:* at fleet scale (hundreds of services), where per-team improvisation guarantees inconsistent risk levels and wasted duplicated effort. *Who:* a central platform/migration team, coordinating with every service-owning team. *How:* a real, published example of this model — <cite index="42-1">a company running over 2,800 microservices relies on heavy automation and central planning, with migrations managed by a central team rather than individual service-owner teams, specifically to avoid delays and inconsistencies</cite>.

### Category B — Data Synchronization Bridge Patterns

**B1. Dual-Write Bridge** — *Definition:* application code writes every change to both the legacy and new stores at write time. *When:* the simplest sync mechanism, appropriate when writes originate from a small, controlled set of code paths. *Who:* the service team, implementing the dual-write logic directly. *How:* every write path is modified to issue two writes; without idempotency keys and reconciliation (§8, D5/B6) this drifts silently under partial failure (Wrong Assumption #8).

**B2. CDC-Based Synchronization** — *Definition:* a connector tails the legacy database's own commit log (WAL/binlog) and replays every change into the new store, without requiring application code changes. *When:* writes originate from too many uncontrolled code paths (ad hoc scripts, other teams' tools) for dual-write to reliably cover. *Who:* a dedicated migration-infrastructure team operating the CDC pipeline. *How:* the connector reads the database's native replication stream and translates each row-level change into an event applied to the new store — a real published migration used exactly this mechanism, where <cite index="38-1">40-plus database instances were migrated using change data capture</cite> as part of the sync strategy.

**B3. Shadow Table Strategy** — *Definition:* a synchronized duplicate table, kept current via triggers or CDC, existing alongside the original as a safe staging ground for migration or refactoring. *When:* migrating a specific table's structure or extracting it into a new service, without disturbing the original's availability. *Who:* the team performing the extraction, typically with platform-team support for the sync mechanism. *How:* <cite index="46-1">database triggers or change-data-capture frameworks actively replicate every change from the original table to the shadow table</cite>, and industry case studies from large-scale engineering organizations document this approach specifically for service extractions and data migrations at scale. *(Distinct from "Shadow Deployment/Dark Launch" traffic-routing patterns covered in the GitOps article — this is a data-layer synchronization mechanism, not a request-routing mechanism.)*

**B4. Backfill + Live-Tail Combination** — *Definition:* a one-time bulk copy of all historical data (backfill), combined with a continuously-running CDC tail that captures everything written since the backfill snapshot was taken. *When:* the standard combination for bringing a new store to full parity with an actively-written-to legacy store. *Who:* the migration-infrastructure team. *How:* the backfill establishes a starting checkpoint (a specific WAL position or timestamp); the live-tail then processes every change from that exact checkpoint forward, closing the gap without any window of missed writes.

**B5. Migration Bridge / Adapter Service** — *Definition:* a single, dedicated service owning all synchronization logic between old and new stores, rather than scattering dual-write or translation logic across 100-200 individual consumer services. *When:* the consumer fleet is too large for each service to reasonably own its own piece of the sync logic. *Who:* the central migration team, as the sole owner of this service. *How:* consumer services are entirely unaware of the migration — they call the bridge service (or the legacy/new store via the façade from A1), and all sync complexity is centralized in one auditable, testable place.

**B6. Continuous Reconciliation Sweep** — *Definition:* a background job that continuously compares old and new store contents — via checksums or a hash-tree structure rather than full row-by-row comparison — and flags or repairs divergence throughout the entire sync window. *When:* running for the full duration of any dual-write or CDC-bridge window, as a backstop against silent drift (Wrong Assumption #10). *Who:* the migration-infrastructure team. *How:* rather than comparing billions of rows on every sweep, a range-checksum approach (the same Merkle-tree-style technique described in this series' Replication article, §8.15/8.17 there, reused here for migration verification) hashes key ranges and only descends into full row comparison where a range's checksum disagrees — making continuous verification computationally feasible at legacy-database scale.

### Category C — Read-Path Cutover Patterns

**C1. Percentage-Based Read Traffic Shifting** — *Definition:* gradually increasing the percentage of read traffic served from the new store (1% → 10% → 50% → 100%) per service. *When:* the default, lowest-risk read-cutover mechanism. *Who:* the individual service team, using shared tooling from the central migration team. *How:* a routing layer randomly assigns each incoming read to old or new store according to the current percentage, with metrics compared at every step before advancing.

**C2. Per-Tenant / Per-Shard Cutover** — *Definition:* cutting over reads for a specific customer, tenant, or data partition completely, rather than a percentage of all traffic. *When:* the data or traffic pattern varies significantly by tenant, and a percentage-based approach would mix very different risk profiles together. *Who:* the service team, coordinating with account/customer-success teams for high-value tenants. *How:* an internal tenant, or a small opt-in customer segment, is cut over first and fully validated before expanding to the general population.

**C3. Feature-Flag-Gated Read Source Selection** — *Definition:* a flag, evaluated per service or per request, that determines whether a given read is answered by the legacy store or the new one. *When:* needing instant, code-deploy-free control over read routing during the cutover period. *Who:* the service team, operating the flag directly. *How:* flipping the flag redirects reads immediately, with no redeploy — the fastest possible read-path rollback mechanism if a problem appears. *(Scoped specifically to data-source selection during migration — distinct from the general feature-rollout pattern covered in the GitOps article.)*

**C4. Circuit-Breaker-Gated Cutover Fallback** — *Definition:* an automatic mechanism that reverts a service's reads (and, separately, its rollback trigger for writes) back to the legacy path the moment the new path's error rate crosses a defined threshold, with no human intervention required. *When:* as a standing safety net throughout the entire read and write cutover period for every migrated service. *Who:* the central migration team, providing this as shared infrastructure every service team enables. *How:* the breaker continuously samples new-path error rate; crossing the threshold flips the service's read-source flag (C3) and/or write-target back to legacy automatically, logging the trip for investigation.

### Category D — Write-Path Cutover Patterns

**D1. Dual-Write-Single-Read Staged Model** — *Definition:* a named, staged migration sequence where writes go to both stores while reads continue from only the legacy store, before reads are ever moved. *When:* the conservative default sequencing for write-path migration. *Who:* the migration-infrastructure team, defining the stage progression. *How:* a real documented implementation of this exact staged approach describes a <cite index="43-1">"Dual-Write Single-Read" mode</cite> as an explicit, named stage in a multi-stage migration dial, only advancing to reading from the new store once the dual-write stage has proven stable.

**D2. Write-Then-Verify** — *Definition:* synchronously comparing the result of a write against both stores before acknowledging success to the caller, rather than writing to both and trusting reconciliation to catch problems later. *When:* for the highest-value, lowest-tolerance-for-drift data (financial transactions, account balances). *Who:* the service team owning that specific critical write path. *How:* the write completes on both stores, then an immediate read-back comparison runs before the caller receives a success response — at the cost of added write latency, in exchange for zero silent-drift window on that specific path.

**D3. Write-Back Bridge** — *Definition:* once the new store becomes the primary write target, writes are mirrored back to the legacy store specifically to keep not-yet-migrated services (still reading from legacy) correctly served. *When:* mid-migration, once some but not all consumer services have cut over to reading from the new store. *Who:* the migration bridge service (B5). *How:* the direction of the dual-write flips relative to B1 — new store is authoritative, legacy store becomes the mirror — a subtle but critical distinction that must be tracked explicitly per entity (D4).

**D4. Per-Entity Migration State Machine** — *Definition:* tracking each record's (or shard's) migration status individually through explicit states, rather than treating the whole dataset as a single binary migrated/not-migrated flag. *When:* any migration running long enough, or granular enough, that different records can legitimately be in different stages simultaneously. *Who:* the migration-infrastructure team, exposing this state as queryable metadata. *How:*

```
states = [not_started, dual_write, backfilled, verified, cut_over, legacy_removed]

def transition(entity_id, current_state, event):
    if current_state == "not_started" and event == "bridge_enabled":
        return "dual_write"
    if current_state == "dual_write" and event == "backfill_complete":
        return "backfilled"
    if current_state == "backfilled" and event == "reconciliation_passed":
        return "verified"
    if current_state == "verified" and event == "cutover_confirmed":
        return "cut_over"
    if current_state == "cut_over" and event == "legacy_access_revoked":
        return "legacy_removed"
    return current_state
```

*(Distinct from the general causal-debugging "state machine + transition log" pattern covered in the second article of this series — here the states themselves are migration-lifecycle stages, tracked for rollback and cutover-readiness purposes, not for causal reconstruction of an incident.)*

**D5. Idempotent Migration Writes** — *Definition:* designing every write the migration bridge performs so that replaying it produces the same end state, no matter how many times it's retried. *When:* mandatory for any CDC-based or retried dual-write mechanism, given at-least-once delivery is the norm for any real message pipeline. *Who:* the migration-infrastructure team implementing the bridge. *How:* every migrated write carries a stable idempotency key (often derived from the legacy record's own primary key plus a version/offset), and the new store's write path upserts rather than blindly inserts or increments — directly avoiding the double-processing failure mode this series' earlier articles cover in more general terms.

### Category E — Behavior-Verification & Tracing Patterns (the critical section)

**E1. Shadow Traffic Parallel-Run Comparison** — *Definition:* running the legacy path (control) and new path (candidate) on the same real input, always returning the control's result to the actual caller, while comparing and logging any mismatch between the two. *When:* the primary verification technique for any critical read or write path before it is trusted to serve real traffic from the new store. *Who:* the service team owning the specific code path being migrated. *How:* fully detailed with a worked example in §7 above — this is the technique GitHub's Scientist library and its many ports across languages were purpose-built for, and it explicitly subsumes the narrower idea of "dark reads" (querying the new store in shadow and discarding the result) as one specific instance of the same general technique applied to read paths only.

**E2. Characterization Testing / Golden Master** — *Definition:* <cite index="48-1">a means to describe the actual behavior of an existing piece of software, protecting that existing behavior against unintended changes via automated testing</cite>, capturing what the system currently does rather than what it's supposed to do. *When:* before writing a single line of the new implementation — capture the legacy system's real outputs as ground truth first. *Who:* the service team migrating that specific code path. *How:* <cite index="51-1">Feathers' own heuristic is to first write tests for the area about to change, then specifically for the exact things being changed, and to verify existence and connection of behaviors being extracted before moving them</cite> — a large corpus of real historical (request, actual-output) pairs becomes a fixed regression suite the new implementation must reproduce exactly, bugs included, before it's trusted.

**E3. Non-Determinism Normalization Before Diffing** — *Definition:* explicitly stripping or canonicalizing fields expected to differ between systems (timestamps, generated IDs, floating-point precision, unordered result ordering) before any comparison runs. *When:* mandatory alongside E1/E5 — without it, false-positive noise drowns real signal (§7). *Who:* the team building the comparison harness, with normalization rules reviewed by the domain-owning service team. *How:* see the pseudocode worked example in §7 — normalization rules are discovered incrementally and must go through human review before being trusted, since an overly broad rule silently hides real regressions.

**E4. Invariant Assertion Harness** — *Definition:* explicit, codified business-rule checks (not just output-equality checks) evaluated against both the legacy and new paths' results. *When:* for domain rules too important to leave to incidental output matching — e.g., "account balance never goes negative," "order total always equals sum of line items." *Who:* domain experts and the service team together, since invariants require business knowledge no generic diffing tool has. *How:* each invariant is a small, independent predicate function run against both systems' state after every compared operation, failing loudly and immediately if either system violates it — catching classes of bugs a pure output-diff would miss entirely.

**E5. Production Traffic Replay** — *Definition:* recording real production requests (and their legacy-system responses) during a window, then replaying that exact recorded traffic against the new system offline, at any later time. *When:* for validating a new implementation against real traffic shape without any live production risk, and for re-validating after any subsequent change to the new system. *Who:* the migration-infrastructure team, maintaining the recording/replay tooling as shared infrastructure. *How:* recorded traffic becomes a reusable, growing regression corpus — every new bug found in production feeds a new recorded case back into this replay set, permanently.

**E6. Migration-Scoped Correlation ID Lineage Tagging** — *Definition:* injecting a stable identifier at the migration bridge that lets a single logical record's journey be traced across the legacy store, the sync mechanism, and the new store. *When:* essential the moment a discrepancy needs root-causing — without it, you cannot answer "was this specific wrong record ever correctly synced, and when did it diverge." *Who:* the migration-infrastructure team, embedding this into the bridge/CDC pipeline itself. *How:* directly reuses this series' second article's correlation/causation-ID technique (§8.5 there), applied specifically to migrated-record lineage rather than general request tracing.

**E7. Synthetic Canary Records** — *Definition:* deliberately planted, known test records injected continuously into the production data flow, specifically to verify the migration pipeline's own health independent of real traffic. *When:* as standing verification infrastructure for the entire duration of the sync window. *Who:* the migration-infrastructure team. *How:* a canary record with a known, predictable value is written on a fixed schedule; a monitor continuously checks that it appears correctly and promptly in the new store, alerting immediately if the pipeline itself silently stalls — catching an infrastructure failure before it's discovered by absence of expected data days later.

### Category F — Schema & Semantic Translation Patterns

**F1. Schema Translation / Adapter Layer** — *Definition:* an explicit mapping layer handling type, constraint, and null-semantics differences between the legacy and new database engines. *When:* whenever the new store's type system doesn't map 1:1 onto the legacy one (a near-certainty across different database engines). *Who:* the migration-infrastructure team, maintaining this centrally rather than per-service. *How:* every field's legacy type, null behavior, and default is explicitly mapped to its new-store equivalent, with every non-trivial mapping decision documented and reviewed — undocumented implicit type coercion is exactly where silent behavior drift hides.

**F2. Precision & Rounding Reconciliation** — *Definition:* explicit handling of floating-point and decimal rounding differences between database engines, particularly for financial or otherwise precision-sensitive data. *When:* any migration involving monetary amounts or other values where exact reproducibility matters. *Who:* the service team owning the financially-sensitive data, with the migration team providing tooling. *How:* values are compared with an explicitly documented, reviewed tolerance (never silently "close enough" without sign-off), and any systematic rounding bias is caught by the reconciliation sweep (B6) before it compounds into a real accounting discrepancy.

**F3. Referential-Integrity Emulation via Saga** — *Definition:* replacing a database-enforced foreign-key/transactional invariant, lost when a monolithic legacy schema is split across multiple new services and databases, with an explicit application-level saga that enforces the same invariant. *When:* whenever the legacy database enforced a cross-entity invariant (via FK constraint or trigger) that will span a service boundary after migration. *Who:* both service teams on either side of the newly-created boundary, jointly. *How (worked example):* the legacy database guaranteed an order row could never exist without a valid, matching customer row via a foreign-key constraint — a single-transaction, instantaneous guarantee. After splitting into a separate Order Service and Customer Service, each with its own new database, that guarantee no longer exists automatically. It must become an explicit saga: Order Service calls Customer Service to validate/reserve the customer reference *before* committing the order, and — because that two-step process can still race or partially fail — a background reconciliation job (structurally the same continuous-reconciliation idea as B6, applied to cross-service invariants rather than cross-store data) periodically scans for orphaned orders and either repairs or flags them. This directly reuses the Saga pattern from this series' Event Sourcing article (§8.8-8.9 there), applied here specifically to invariants inherited from a legacy schema split rather than to a newly-designed business process.

**F4. Semantic-Difference Registry** — *Definition:* an explicitly documented, reviewed, and signed-off list of every known *intentional* behavior difference between legacy and new systems — as opposed to an undocumented, accidental one. *When:* maintained continuously throughout the migration, growing every time E1/E3's normalization work legitimately identifies an intentional difference rather than a bug. *Who:* jointly owned by the migration team and every service team whose behavior has a registered difference. *How:* every entry requires an explicit owner, a reason, and a sign-off — turning "is this divergence a bug or intentional" from a repeated ad hoc debate during every incident into a single lookup against a reviewed source of truth.

### Category G — Rollback & Safety Patterns

**G1. Dual-Path Rollback Switch** — *Definition:* a per-service, instantly-flippable switch reverting that specific service back to the legacy store, independent of any other service's migration state. *When:* standing safety infrastructure for every service throughout its entire migration, from first cutover attempt through final decommissioning approval. *Who:* the individual service team, operating their own switch. *How:* implemented as the same mechanism as C3's read-source flag, extended to also cover write-target selection, giving each service full independent reversibility at all times.

**G2. Point-in-Time Consistency Checkpoint** — *Definition:* a synchronized snapshot of both the legacy and new stores taken at the exact moment immediately before a cutover, serving as a precise rollback reference point. *When:* immediately before any wave's cutover event. *Who:* the migration-infrastructure team, automating this as a mandatory pre-cutover step. *How:* both snapshots are tagged with the same logical checkpoint identifier (often a specific CDC offset or WAL position), so a rollback decision can reference "restore to exactly this shared point" rather than reasoning about two independently-drifting timelines.

**G4. Blast-Radius-Scoped Rollback Boundary** — *Definition:* a structural guarantee that rolling back one migration wave never requires touching, or risks destabilizing, any other wave. *When:* designed into the wave-planning process (A4) from the start, not retrofitted after a rollback is already needed. *Who:* the central migration team, enforcing this as a design constraint on every wave's scope. *How:* waves are defined specifically so their cross-wave dependencies are read-only or asynchronous — never a synchronous, transactional coupling that would force a joint rollback across waves that were supposed to be independent.

**G5. Time-Boxed Dual-Write Window** — *Definition:* an explicit, calendared deadline for closing any "temporary" dual-write or bridge mechanism, rather than letting it become an indefinite, permanent fixture. *When:* set at the moment any bridge mechanism (B1-B5) is first stood up. *Who:* the central migration team, tracking and enforcing the deadline against every active bridge. *How:* every bridge is opened with an explicit decommission date reviewed at a fixed cadence; a bridge approaching its deadline without a clear path to closure is escalated as a project risk, not left to drift — directly operationalizing §2.6's warning about compounding drift over time.

### Category H — Dependency Discovery Patterns

**H1. Query-Log / Access-Log Mining for Dependency Census** — *Definition:* using the database engine's own statement logging or access statistics as the authoritative source of truth for who actually touches which tables, since no static document reliably stays accurate. *When:* the mandatory starting point, and continuously throughout, any decommissioning effort. *Who:* the migration-infrastructure team, with output shared to every affected service team. *How:* fully detailed with a worked example in §6 above — this is the technique experienced practitioners point to as the only one that actually answers the question, since removing access and observing what breaks is confirmed as a real, if blunt, fallback when logging isn't already in place.

**H2. Deprecation Warning Injection** — *Definition:* logging a warning or emitting a metric every single time a code path or query pattern marked for removal actually executes, building a real, continuously-updated usage census rather than a one-time snapshot. *When:* the moment any path is identified as a decommissioning candidate. *Who:* the service team owning that path, instrumented with shared tooling from the migration team. *How:* the warning includes enough context (caller identity, query shape) to route a notification directly to whichever team is still triggering it — turning "someone is still using this" from a mystery into an actionable, attributed alert.

**H3. Access Tripwire / Read-Only Freeze Canary** — *Definition:* deliberately restricting access to a suspected-unused resource (making it read-only, or narrowing its permission grant) and observing what breaks, as a validation step beyond passive logging. *When:* used cautiously, only after H1/H2 suggest a resource is likely unused, and only as a staged, reversible step (never an irreversible deletion). *Who:* the migration-infrastructure team, with the affected service teams notified in advance where possible. *How:* this mirrors the real, practitioner-suggested technique of experimentally revoking access and watching for application errors, when no other verification method can give sufficient confidence.

**H4. Cross-Repo Static Dependency Graph Extraction** — *Definition:* an automated scan across all 100-200 services' source repositories for direct database client usage, connection strings, or ORM model definitions referencing the legacy store. *When:* as a complement to runtime discovery (H1) — catches code paths that exist but haven't executed during any observation window. *Who:* the central migration team, running this as shared tooling across the entire codebase estate. *How:* an AST-based or pattern-based scanner identifies every file referencing the legacy connection configuration or a known table name, cross-referenced against the runtime access census to find code that exists but hasn't fired recently — a strong candidate for the "quarterly job" edge case in §5.

**H5. Unknown-Caller Quarantine Alerting** — *Definition:* an alert fired the instant any database connection arrives from a client identity not on a maintained allow-list of known, tracked consumers. *When:* standing infrastructure throughout the migration, specifically to catch the forgotten cron job or undocumented script before it becomes a decommissioning surprise. *Who:* the migration-infrastructure team, maintaining the allow-list collaboratively as each service formally registers itself. *How:* every legitimate consumer is required to register (application name, owning team, purpose) as part of onboarding to the migration program; any connection not matching a registered identity triggers immediate investigation rather than being silently permitted.

### Category I — Decommissioning Patterns

**I1. Staged Access Revocation** — *Definition:* progressively restricting access to the legacy store in discrete stages — full read-write, then read-only, then no access — each held for a defined bake period before advancing. *When:* the final, mandatory phase before physical deletion of any legacy resource. *Who:* the central migration team, executing each stage with sign-off from affected service teams. *How:* each stage is fully reversible if H5-style alerting catches an unexpected dependent, giving a clean rollback path at every step rather than an irreversible single cutover.

**I2. Legacy Read-Replica Safety Net** — *Definition:* keeping a read-only replica of the legacy store alive for a defined bake period after the primary is decommissioned, rather than deleting everything simultaneously. *When:* for any migration where the cost of being wrong about "zero remaining dependents" is high enough to justify the marginal cost of keeping a replica alive a while longer. *Who:* the migration-infrastructure team. *How:* the replica serves as a safety net specifically for the discovery gaps described in §5 and §6 — a forgotten quarterly job that surfaces during the bake period can still be served (and flagged for proper migration) rather than simply failing outright.

**I3. Final Freeze & Cold Archive** — *Definition:* taking a final, complete snapshot of the legacy store's state immediately before deletion and moving it to low-cost cold storage, for audit, compliance, or historical-investigation purposes. *When:* the very last step, after every access-revocation stage (I1) has passed its bake period with zero flagged access. *Who:* the central migration team, coordinating with compliance/legal stakeholders on retention requirements. *How:* the archive is deliberately not queryable in normal operation (to avoid becoming a shadow dependency itself) but is retrievable through an explicit, audited restoration process if a genuinely unanticipated need arises later.

---

## 9. 22 Techniques & Mental Models

Each includes why it's actually correct, not just asserted.

**T1. Hyrum's Law as Default Assumption.** Assume every observable behavior — not just the documented contract — is depended on by somebody. *Why right:* empirically confirmed across large real API/dependency datasets, and the cost of being wrong (a silent production break) vastly outweighs the cost of over-caution.

**T2. Chesterton's Fence for Legacy Quirks.** Don't remove or "fix" a quirk until you understand why it exists and who relies on it. *Why right:* a "fix" applied during a behavior-preservation project is indistinguishable, in the diff, from an accidental regression — you lose your own ability to tell the difference later.

**T3. Separate "Migrate" from "Improve."** Migrate the schema and behavior 1:1 first; redesign is a separate, later, independently-scoped project. *Why right:* isolates the variable — if both shape and behavior change at once, a regression can't be attributed to either cause with confidence.

**T4. The Implicit-Coupling Insight.** A shared database among N services is already a distributed system, whether anyone designed it that way or not. *Why right:* naming this explicitly changes how you plan — you're not "migrating a database," you're re-implementing an existing, undocumented coupling mechanism.

**T5. "Silence Is the Success Metric."** The win condition for a migration is that nothing observably changes — no new alerts, no metric shifts, no support tickets. *Why right:* any observable change, positive or negative, means behavior preservation failed at the one thing this project type was actually asked to do.

**T6. Isolate the Variable Under Test.** Change exactly one axis at a time — schema OR service boundaries, sync mechanism OR cutover percentage — never several simultaneously. *Why right:* a basic experimental-design principle; without it, you cannot attribute an observed effect to its actual cause when something goes wrong.

**T7. Assume Your Dependency Map Is Wrong Until Verified Empirically.** No wiki, doc, or architecture diagram about "who uses this" should be trusted without runtime log confirmation. *Why right:* documented and confirmed directly by practitioners who tried the alternative and found no reliable substitute for actual access logging.

**T8. Sync Infrastructure Before Cutover, Never the Reverse.** The dual-write/CDC bridge must be proven stable before any read or write traffic is moved, never built reactively after a cutover already happened. *Why right:* cutting over onto an unproven sync mechanism means you have no verified rollback target if something goes wrong immediately after.

**T9. Percentage Ramp With an Automatic, Not Manual, Rollback Threshold.** The threshold that triggers a rollback should be a pre-agreed, automated trigger (C4), not a judgment call made live during an incident. *Why right:* removes exactly the kind of pressured, in-the-moment decision-making this series' third article (§5 there) identifies as the hardest, most error-prone part of incident response.

**T10. Normalize Before You Diff.** Strip or canonicalize known-expected-to-differ fields before any comparison runs, never after. *Why right:* an unnormalized diff drowns real signal in expected noise so thoroughly that teams stop trusting — and then stop using — the comparison tool entirely.

**T11. Sample Plus Periodic Full Sweep, Not Full Comparison Every Time.** Use range-checksums for continuous verification, with occasional full row-by-row sweeps rather than constant exhaustive comparison. *Why right:* full comparison at legacy-database row counts is computationally infeasible to run continuously; checksums make continuous verification tractable without sacrificing eventual completeness.

**T12. Treat the Migration Itself as a State Machine Worth Debugging.** The migration's own progress (D4) deserves the same tracing rigor as the business logic it's migrating. *Why right:* when something goes wrong, "what state was this record's migration actually in" is usually the first question, and it needs a direct answer, not a reconstruction from scattered logs.

**T13. Reversibility Before Speed.** Prefer a slower step you can cleanly undo over a fast step you can't. *Why right:* the cost asymmetry is enormous — a slow but reversible migration step costs time; an irreversible mistake at 100-200-service scale can cost the entire project's credibility and require restarting trust-building from zero.

**T14. The "Small Error Rate at Huge N" Trap.** A 1% failure rate sounds acceptable until you multiply it by the actual row count. *Why right:* legacy databases at this scale routinely hold hundreds of millions to billions of rows — 1% of that is a genuinely enormous number of individually wrong records, not a rounding error.

**T15. Blast-Radius Thinking Over Total-Correctness Thinking.** Accept a small, controlled, well-understood risk over a theoretically "more correct" but all-or-nothing approach. *Why right:* directly follows from §2.4 — risk scales with exposure at the moment of change, not with the elegance or completeness of the underlying technical approach.

**T16. Correlation-ID Lineage Tagging at the Bridge.** Every migrated record should carry a traceable identifier linking its legacy and new-store existence. *Why right:* without this, root-causing a specific wrong record means manually correlating timestamps and guessing — exactly the causal-reconstruction problem this series' second article shows cannot be solved after the fact if not captured at write time.

**T17. Boring, Proven Sync Mechanisms Over Clever Ones.** Prefer well-documented CDC tooling and established patterns over a bespoke, clever synchronization scheme unique to this migration. *Why right:* migration correctness matters more than elegance — a boring, widely-used mechanism has already had its edge cases found by someone else's production incidents, not yours.

**T18. Assume the Legacy System's Bugs Are Load-Bearing Until Proven Otherwise.** Treat every discovered legacy quirk as a deliberate design decision until you can prove it's genuinely just a bug nobody depends on. *Why right:* the practical restatement of Hyrum's Law (T1) plus Chesterton's Fence (T2) combined — the default assumption must be "load-bearing," because the cost of wrongly assuming "harmless bug" is a silent production break.

**T19. Time-Box Every "Temporary" Bridge With a Hard Decommission Date.** No dual-write or sync mechanism should exist without an explicit closing date set at creation. *Why right:* directly follows from §2.6 — drift compounds the longer a bridge stays open, and "temporary" infrastructure with no deadline reliably becomes permanent technical debt in every organization that has ever tried otherwise.

**T20. Observability Before Migration, Not After.** Instrumentation, logging, and the discovery census (§8, Category H) must exist before the first line of migration code is written, not added reactively once something has already gone wrong. *Why right:* this series' second article establishes that causal information not captured at the moment it happens can never be recovered afterward — the same is true here for dependency and behavior information.

**T21. The Org Boundary Is Part of the System.** Migration sequencing must account for team coordination cost and readiness, not just technical dependency order. *Why right:* Conway's Law means your service architecture already mirrors your org structure — a migration plan that ignores which teams can realistically coordinate on what timeline is planning against a system that doesn't actually exist.

**T22. Trust the Access Logs, Not the Wiki.** When runtime evidence and documentation disagree about a dependency, the runtime evidence wins, every time, without exception. *Why right:* this is the single most repeated lesson across every practitioner account of this kind of project — documentation describes intent, logs describe reality, and reality is what breaks in production.

---

## 10. Relationship Between the Pattern Categories

```log
└── Migration at Scale
    ├── Strategy Layer (Category A) — decides the SHAPE of the whole project
    │   └── determines → how many Sync Bridges (B) and Waves (G4) are needed
    ├── Sync Bridge Layer (Category B) — keeps two stores simultaneously true
    │   ├── feeds → Read Cutover (C) and Write Cutover (D) once proven stable (T8)
    │   └── verified-continuously-by → Reconciliation Sweep (B6) and Canary Records (E7)
    ├── Cutover Layer (Categories C, D) — moves real traffic, service by service
    │   ├── gated-by → Circuit-Breaker Fallback (C4) at all times
    │   └── tracked-by → Per-Entity Migration State Machine (D4)
    ├── Verification Layer (Category E) — the load-bearing "behavior preservation" proof
    │   ├── E1/E2/E5 answer → "does the new system behave identically"
    │   └── E3/E4 answer → "how do we tell real divergence from expected noise" (§7)
    ├── Translation Layer (Category F) — reconciles semantic differences between engines
    │   └── F3 specifically rebuilds → invariants the legacy DB enforced for free via transactions/FKs
    ├── Safety Layer (Category G) — makes every step reversible
    │   └── depends-on → Blast-Radius-Scoped waves (A4) actually being independent
    ├── Discovery Layer (Category H) — the epistemic problem (§6), runs continuously
    │   └── gates → every Decommissioning (I) step's go/no-go decision
    └── Decommissioning Layer (Category I) — the final, only-provably-safe-after-Discovery step
        └── never begins until → Discovery (H) shows sustained zero access, not just "looks migrated"
```

---

## 11. Flow — How an Actual Senior Engineer Runs This, End to End

**For one service, start to finish:**

1. **Discover first, touch nothing yet** (H1-H5): pull query logs, cross-reference static code search, register every caller. Assume the existing documentation is wrong (T7, T22) until logs confirm otherwise.
2. **Capture ground truth before writing new code** (E2): build a characterization/golden-master corpus from real historical requests and their actual legacy outputs — bugs included, deliberately.
3. **Stand up the sync bridge and let it bake** (B1-B5, D5): dual-write or CDC, idempotent, with continuous reconciliation (B6) and canary records (E7) running before any real cutover is even considered.
4. **Verify behavior in shadow, not in production** (E1, E3, E4): run old and new in parallel on real traffic, always serving the old result, comparing and normalizing until the noise is gone and only real signal remains — reviewed by a human every time a new normalization rule is proposed (§7).
5. **Cut over reads first, gradually, with an automatic safety net** (C1-C4): percentage ramp, per-tenant where it matters, circuit-breaker-gated, correlation-ID tagged (E6) so any discrepancy can be traced to its exact origin.
6. **Cut over writes through expand-contract, never in one step** (A3, D1-D3): expand, dual-write, verify, only then contract — each phase independently deployed and independently safe.
7. **Keep the rollback switch live the entire time** (G1-G2): every stage remains instantly reversible until there's no reason left to need it to be.
8. **Time-box the bridge and hold the line on the deadline** (G5, T19): a dual-write mechanism without a decommission date is not a migration in progress, it's new permanent infrastructure nobody decided to build.
9. **Decommission only after sustained, monitored silence** (I1-I3): staged access revocation, a safety-net replica held through the bake period, and only then — not before — the final archive and deletion.

**Across 100-200 services, the same nine steps repeat per wave** (A4-A6), with a central team owning steps 1, 3, and 8's tooling so each individual service team is executing a proven, repeatable checklist rather than re-deriving this playbook from scratch — the exact model a real 2,800-microservice migration program is documented as having used specifically to keep hundreds of parallel migrations consistent and on schedule.

---

## 12. References

- Fowler, M. — *StranglerFigApplication*, martinfowler.com, 2004
- <cite index="2-1">Wikipedia — *Strangler fig pattern*</cite>, contributors, citing Fowler's original coinage
- <cite index="4-1">Microsoft Azure Architecture Center — *Strangler Fig pattern*</cite>, learn.microsoft.com
- Fowler, M. — *Evolutionary Database Design*, martinfowler.com/articles/evodb.html
- <cite index="16-1">"The Expand and Contract Pattern for Zero-Downtime Migrations"</cite>, dev.to, JP Fontenele
- Feathers, M. — *Working Effectively with Legacy Code*, Prentice Hall, 2004
- <cite index="48-1">Wikipedia — *Characterization test*</cite>, citing Feathers' original coinage
- GitHub — *Scientist: A Ruby Library for Carefully Refactoring Critical Paths*, github.com/github/scientist
- <cite index="29-1">InfoQ — "GitHub's Scientist Aims to Help Refactoring Critical Paths"</cite>, 2016
- <cite index="38-1">Google Cloud Blog — "Apollo24|7: Migrating a Complex Microservices Application to Google Cloud with Zero Downtime"</cite>, 2023
- <cite index="42-1">InfoQ — "Planning, Automation and Monorepo: How Monzo Does Code Migrations Across 2800 Microservices"</cite>
- <cite index="43-1">AWS Architecture Blog — "Middleware-assisted Zero-downtime Live Database Migration to AWS"</cite>
- <cite index="46-1">InfoQ — "Shadow Table Strategy for Seamless Service Extractions and Data Migrations"</cite>
- Nygard, M. — *Referential Integrity Refactoring / Database Refactoring*, databaserefactoring.com
- Kleppmann, M. — *Designing Data-Intensive Applications*, O'Reilly, 2017 (schema evolution, migrations)

---

*This entire project type reduces to one sentence: prove — continuously, empirically, and at a scale no single person can hold in their head — that nothing observably changed, while replacing everything underneath. Every one of the 44 patterns and 22 techniques above exists because some team, somewhere, tried the shortcut past that proof and paid for it in an incident that could not be root-caused after the fact.*