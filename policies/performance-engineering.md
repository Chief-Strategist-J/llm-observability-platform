# Performance Engineering — Complete Reference

Single source of truth. Combines and supersedes the earlier two documents, and adds the layer
that was still missing: the theory each rule is *downstream of*, and the named failure modes
each rule exists to prevent. No implementation code anywhere in this document — pseudocode-level
decision logic only. Rules are laws. Trees are judgment. Both are meant to be practiced, not read once.

---

## PART 0 — NAVIGATION

### 0.1 How This Document Is Organized

```
Part I    First Principles          — the theory (WHY the rules must be true)
Part II   Absolute Laws             — 98 rules, 19 tiers, severity-tagged (WHAT to enforce)
Part III  Algorithm Taxonomy        — selection trees + complexity tables
Part IV   Concurrency Taxonomy      — selection trees + primitive tables
Part V    Language Implementation   — Kotlin / Go / Python mapping
Part VI   Failure Mode Encyclopedia — named failure patterns, mechanism, detection, prevention
Part VII  Pre-Code Thinking Protocol— HOW to think before writing anything
Part VIII Critical Question Lists   — what to interrogate yourself with, by phase
Part IX   Daily Practice Protocol   — non-optional standing discipline
Part X    Cross-Reference Matrix    — law ↔ principle ↔ failure mode ↔ technique
Appendix  Severity legend, glossary
```

### 0.2 Master Bottleneck Decision Tree

```
                         ┌─────────────────────────┐
                         │   Where does it hurt?    │
                         └────────────┬─────────────┘
                                      │
        ┌───────────────┬────────────┼────────────┬───────────────┐
        │                │            │            │               │
   High CPU,        High latency   Memory      Throughput      Correctness
   low throughput   low CPU        growth      ceiling         under load
        │                │            │            │               │
        ▼                ▼            ▼            ▼               ▼
  Part II·Tier II    Part II·Tier V  Part II·III  Part II·Tier    Part II·Tier
  (Algorithmic)       (I/O, Fan-out) (Memory)     IV/VII/XII      VII/XVII
  Part II·Tier IX    Part I·G            │        (Concurrency,   (Distributed,
  (Micro-arch)        (latency table)    ▼        DB, Capacity)   predictability)
        │                │           Rule 12-15,       │               │
        ▼                ▼           44-48,52          ▼               ▼
  Profile w/       Measure p50/                    Rule 16-27,     Rule 17,31-38,
  perf/flame        p99/p999 w/ N                  52-58,96        63,71,83-88
  → Rule 1,44,50    → Rule 2,3,97
```

### 0.3 Severity Legend

| Tag | Meaning |
|---|---|
| `[BLOCKER]` | Violating this causes incidents/outages. Never negotiable. |
| `[CRITICAL]` | Violating this causes silent long-term regression or data risk. |
| `[STANDARD]` | Strong default; deviate only with a stated, measured reason. |

---

## PART I — FIRST PRINCIPLES

Every rule in Part II is a practical consequence of one of these. When a rule feels arbitrary,
trace it back here — the theory is where "strict" stops being opinion and becomes math.

### I.A — Little's Law

**Statement:** `L = λ × W`
— L = average number of items in the system (concurrency, in-flight requests, WIP)
— λ = average arrival rate (throughput)
— W = average time an item spends in the system (latency)

**Why it's absolute:** a conservation law. True for any arrival process, any service-time
distribution, any scheduling discipline, as long as the system is stable. No clever algorithm
gets around it.

**Direct consequence:** required concurrency = throughput × latency. Sustaining 10,000 req/s at
50ms average latency needs ≥500 in-flight slots — arithmetic, not a guess. Inverted: if
concurrency is capped (fixed pool size L) and downstream latency W rises, throughput λ = L/W
falls automatically. This is the exact mechanism behind "one slow dependency throttles
everything" — no bug required, just the law asserting itself.

### I.B — Utilization Law & Queueing Near Saturation

**M/M/1 wait time:** `Wq = ρ / (μ(1−ρ))`, ρ = utilization (0–1), μ = service rate.

**Why it's absolute:** as ρ→1, Wq→∞, and the curve is hyperbolic, not linear. Going from 70%
to 90% utilization doesn't add "20% more wait" — it can add multiples, because (1−ρ) shrinks
toward zero in the denominator.

**Caveat — PASTA property:** this specific math assumes Poisson (memoryless) arrivals. Real
traffic is often bursty/self-similar (correlated clustering), which makes real queueing delay
*worse* than Poisson math predicts at the same average utilization. Treat M/M/1 math as a
floor on required safety margin, never as an upper bound.

### I.C — Amdahl's Law

**Statement:** `Speedup(N) = 1 / (S + (1−S)/N)`, S = serial fraction, N = processors.

**Why it's absolute:** as N→∞, Speedup→1/S — a hard ceiling set by the serial fraction alone,
regardless of hardware budget. If 10% of a pipeline is inherently sequential, no amount of
parallel hardware exceeds 10x. This is the mathematical form of "classify order-dependent
work first" (Part VII.C) — it explains why that classification sets your speed ceiling, not
just your correctness.

### I.D — Universal Scalability Law (Gunther)

**Statement:** `Speedup(N) = N / (1 + σ(N−1) + κN(N−1))`, σ = contention cost, κ = coherency cost.

**Why it's the necessary extension of Amdahl:** Amdahl assumes everything but the serial
fraction scales for free. USL adds two real costs — σ (serialization/lock contention) and κ
(coherency: cross-node consensus, cache-coherency traffic, gossip). Because of the κN² term,
throughput doesn't just plateau — **past a certain N, adding more nodes makes the system
slower.** This is the formal explanation for "we scaled out and it got worse" incidents:
coordination cost grew faster than added capacity. Directly grounds Rule 36 (shard skew) and
Rule 84 (partition instead of globally serializing).

### I.E — Roofline Model

**Statement:** `Attainable performance = min(Peak compute, Memory bandwidth × Operational Intensity)`,
Operational Intensity = FLOPs per byte moved.

**Direct consequence:** tells you, before optimizing, whether you're compute-bound or
memory-bandwidth-bound. If memory-bandwidth-bound, adding cores/threads does nothing — you
need better data layout and access pattern instead (Rules 11, 13). Optimizing the wrong side
of the roofline is a common, entirely wasted, effort sink.

### I.F — CAP Theorem / PACELC

**CAP:** under a network Partition, choose Consistency or Availability — not both. (P isn't
optional in a real distributed system, so this is really a C-vs-A choice at partition time.)

**PACELC extension:** Else (no partition), there's still a Latency-vs-Consistency trade —
stronger consistency needs more coordination round-trips, which costs latency regardless of
partition state.

**Direct consequence:** grounds Rule 17 (explicit consistency model), Rule 35 (no wall-clock
causality), Rule 37 (SLI measured end-to-end). These aren't arbitrary process — they're the
only sane response to a theorem proving you can't dodge the trade-off, only choose consciously.

### I.G — Latency Numbers Every Engineer Must Know

| Operation | Approx. latency | Relative to L1 |
|---|---|---|
| L1 cache reference | ~1 ns | 1x |
| Branch mispredict | ~3–5 ns | ~4x |
| L2 cache reference | ~4 ns | ~4x |
| Mutex lock/unlock (uncontended) | ~20–25 ns | ~20x |
| Main memory reference (RAM) | ~100 ns | ~100x |
| Compress 1 KB (fast compressor) | ~2 μs | ~2,000x |
| Send 1 KB over 1 Gbps network | ~10 μs | ~10,000x |
| SSD/NVMe random read | ~16–150 μs | ~10,000–150,000x |
| Round trip within same datacenter | ~500 μs | ~500,000x |
| Read 1 MB sequentially from SSD | ~1 ms | ~1,000,000x |
| HDD disk seek | ~10 ms | ~10,000,000x |
| Round trip cross-continent | ~150 ms | ~150,000,000x |

**Why this is load-bearing, not trivia:** every I/O law in Part II (batching, pooling,
zero-copy) exists because these ratios span 100x to 150,000,000x. One accidental network call
inside a loop that should be memory-bound isn't "a bit slower" — it can be six-plus orders of
magnitude slower. These numbers drift as hardware evolves (NVMe alone moved the SSD row ~10x
over the last decade) — re-verify periodically; don't treat this table as permanent (Rule 72).

### I.H — Amortized Analysis (the proof behind "amortized O(1)")

Three formal methods used to prove an amortized bound:
- **Aggregate method** — total cost of n operations ÷ n.
- **Accounting method** — assign each operation a "credit"; expensive ops are paid for by
  credit banked by earlier cheap ones.
- **Potential method** — define a potential function Φ over the structure's state; amortized
  cost = actual cost + ΔΦ.

**Direct consequence:** grounds Rule 9 (state worst-case, not just amortized). Amortized O(1)
is an *average over a sequence* — a single operation inside that sequence (array-doubling
resize, tree rebalance) can still spike to O(n). A per-request p99/p999 SLO is not protected
by an amortized bound; you need the worst-case bound too.

### I.I — Pool Sizing Theory (Erlang B / Erlang C)

For a fixed-size resource pool where excess requests are rejected, **Erlang B** gives blocking
probability; where excess requests queue instead, **Erlang C** gives expected wait — both are
direct extensions of I.B's queueing theory, specialized for finite-server systems.

**Direct consequence:** grounds Rule 96 (pool sizing via Little's Law) with the next layer of
precision — "just make the pool big" isn't free (memory/OS-handle cost bounds pool size too),
so finite-pool math, not intuition, should set the size.

---

## PART II — ABSOLUTE LAWS (98 rules, 19 tiers)

### Tier I — Measurement `[BLOCKER]`

| # | Rule |
|---|---|
| 1 | No optimization without a profiler trace pointing to the exact line/frame. |
| 2 | Report p50/p99/p999 — never mean alone. |
| 3 | Every percentile ships with its sample count (N). |
| 4 | Benchmark on production-equivalent topology (NUMA, network hops, contention). |
| 5 | Every before/after claim includes variance (stddev), never a single run. |
| 6 | Profile under realistic load shape, never synthetic best-case. |
| 7 | Every fix ships with a regression alert on the metric it fixed. |

### Tier II — Algorithmic `[CRITICAL]`

| # | Rule |
|---|---|
| 8 | Know the Big-O of every hot-path call before touching memory/I/O tuning. |
| 9 | State worst-case, not just amortized case, for every hot-path structure (see I.H). |
| 10 | Any structure trade for "cleaner code" states the complexity delta explicitly. |
| 11 | Below ~10k elements, cache-locality wins over asymptotic elegance — never choose by Big-O alone. |

### Tier III — Memory `[CRITICAL]`

| # | Rule |
|---|---|
| 12 | Every allocation in a hot loop is guilty until proven innocent. |
| 13 | Hot mutable fields shared across threads are padded to the cache line (64B/128B). |
| 14 | GC pause budget is defined before code is written, not discovered in prod. |
| 15 | Zero-copy is mandatory for large payloads on hot paths. |

### Tier IV — Concurrency `[BLOCKER]`

| # | Rule |
|---|---|
| 16 | Lock granularity is a stated design decision, never an accident. |
| 17 | Every shared mutable state has an explicit consistency model stated (see I.F). |
| 18 | Memory ordering (`Relaxed`/`Acquire-Release`/`SeqCst`) is stated per atomic. |
| 19 | Never hold a lock across an I/O call or await point. Zero exceptions. |
| 20 | Priority: wait-free > lock-free > lock-based — only past lock-based when contention is measured. |
| 21 | Contended locks hide as CPU time in naive profilers — capture wait/futex time separately. |
| 22 | Every queue boundary has explicit backpressure (see I.A). |

### Tier V — I/O & Network `[BLOCKER]`

| # | Rule |
|---|---|
| 23 | Every batchable network/disk call is batched (see I.G). |
| 24 | Every synchronous I/O call in a request path is a hard throughput ceiling. |
| 25 | Connection pool exhaustion is a P0 failure mode, not an edge case (see I.A, I.I). |
| 26 | Every syscall in a hot loop is a context-switch tax — batch or justify. |
| 27 | Serialization format on a hot path is chosen by profiling, not convention. |

### Tier VI — Caching `[CRITICAL]`

| # | Rule |
|---|---|
| 28 | Every cache has an explicit eviction policy and TTL stated at creation. |
| 29 | Cache correctness outranks cache hit rate. |
| 30 | Every cache-miss path is protected against thundering herd (see Part VI). |

### Tier VII — Distributed Systems `[BLOCKER — strictest tier]`

| # | Rule |
|---|---|
| 31 | Every cross-service call: explicit timeout + retry policy + idempotency. No exceptions. |
| 32 | Every retry uses jittered exponential backoff. |
| 33 | Fan-out tail latency is a composed probability across N calls, never estimated from one service's p99. |
| 34 | Every circuit breaker has 3 explicit states with measured thresholds. |
| 35 | Wall-clock time is never used for cross-service causality (see I.F). |
| 36 | Every shard/partition key is justified against skew, not just throughput math (see I.D). |
| 37 | Every SLO is backed by an SLI measured end-to-end (see I.F). |
| 38 | Saturation trend (queue depth) — not average utilization — is the collapse signal (see I.B). |

### Tier VIII — Meta-Laws, Tier 1 `[BLOCKER]`

| # | Rule |
|---|---|
| 39 | Optimize the proven bottleneck — never the code you understand best. |
| 40 | Every optimization states its maintenance cost explicitly. |
| 41 | An optimization that cannot be measured after deployment is not done. |
| 42 | Rule wins over "ship faster" unless a human explicitly accepts the risk in writing. |
| 43 | Silence is not compliance — unmeasured systems are assumed broken. |

### Tier IX — Hardware / Micro-architectural `[CRITICAL]`

| # | Rule |
|---|---|
| 44 | Verify branch misprediction/IPC with hardware counters before declaring a hot path optimized. |
| 45 | NUMA-local allocation is mandatory for latency-sensitive threads. |
| 46 | Huge pages are a required decision once working set exceeds L2/L3, not a later knob. |
| 47 | SIMD/auto-vectorization is verified via disassembly/vectorization report, never assumed. |
| 48 | Page faults on a hot path are treated as I/O-class latency events (see I.G). |

### Tier X — Compiler / Runtime / JIT `[CRITICAL]`

| # | Rule |
|---|---|
| 49 | Cold-start/JIT warm-up latency is measured and reported separately from steady-state. |
| 50 | "The compiler will optimize this" is never trusted without verifying generated code, on hot paths. |
| 51 | GC algorithm choice is a stated architectural decision tied to the latency SLO. |

### Tier XI — Database & Storage `[BLOCKER]`

| # | Rule |
|---|---|
| 52 | Every hot-path query has a verified execution plan on record. |
| 53 | N+1 query patterns are zero-tolerance defects. |
| 54 | Index existence is verified against actual query predicates, never assumed. |
| 55 | Every write path states its durability guarantee explicitly, matched to data criticality. |

### Tier XII — Capacity & Scaling `[CRITICAL]`

| # | Rule |
|---|---|
| 56 | Capacity plans use measured peak-to-trough ratios and trend, never average × factor. |
| 57 | Every system has a stated, load-tested breaking point. |
| 58 | Horizontal scaling assumptions are verified against real shared-state bottlenecks (see I.D). |

### Tier XIII — Production Safety & Change Management `[BLOCKER]`

| # | Rule |
|---|---|
| 59 | Every performance change ships with a tested rollback path. |
| 60 | Canary/staged rollout is mandatory for any hot-path change at scale. |
| 61 | Load-shedding policy is defined before capacity is reached, never improvised mid-incident. |
| 62 | Degradation order is documented and rehearsed in advance. |
| 63 | A fix that alters correctness semantics gets full correctness-change review, regardless of urgency. |

### Tier XIV — Deeper Meta-Laws `[BLOCKER]`

| # | Rule |
|---|---|
| 64 | Absence of complaints is not absence of a problem — hunt p99/memory creep on a schedule. |
| 65 | Every "obvious" bottleneck is a hypothesis until measured. |
| 66 | A benchmark confirming your prior belief gets scrutinized harder, not less. |
| 67 | If the causal mechanism of a fix can't be stated in one sentence, it isn't understood well enough to ship. |
| 68 | A local optimization that degrades a global metric is a net loss, full stop. |
| 69 | Every optimization is re-justified against current load data before being reapplied elsewhere. |
| 70 | The last 10% of a perf gain costs 10x effort only when the SLO explicitly demands it. |
| 71 | When performance and correctness conflict, correctness wins unconditionally. |
| 72 | **Every rule in this document is falsifiable by your own measured data.** Priors, not scripture — trust the profiler over the rule, and log the disagreement as a finding. |

### Tier XV — Defensive Correctness & Boundary Condition `[BLOCKER]`

| # | Rule |
|---|---|
| 73 | Every input boundary — null, empty, zero, negative, max-value, empty-collection, duplicate — is enumerated before the happy path is written. Happy path is written LAST. |
| 74 | A missing null/empty check is not "works fine for now" — it is undefined behavior deferred to an unknown future caller, a liability with an unknown due date. |
| 75 | Every function's contract states what it does NOT handle, as explicitly as what it does. |
| 76 | Fail fast and loud at every trust boundary. Bad data crossing silently into internal logic converts a cheap failure into an untraceable one. |
| 77 | Every "this can never happen" comment is an unfiled bug report — prove it structurally or handle it explicitly. |

### Tier XVI — Data Modeling & Schema Design `[CRITICAL]`

| # | Rule |
|---|---|
| 78 | Normalize for correctness first, denormalize for measured performance second — never either direction preemptively. |
| 79 | Every entity-boundary decision is justified by an actual access pattern, never by "this feels like its own concept." |
| 80 | Table count is a symptom, not a goal — both over- and under-normalization are code smells until justified by real access patterns (see Part VII.B). |
| 81 | Every relationship states its cardinality AND consistency requirement at design time. |
| 82 | Every relationship decision is checked against the WRITE path, not just the read path. |

### Tier XVII — Concurrency–Predictability `[BLOCKER]`

| # | Rule |
|---|---|
| 83 | Before parallelizing, classify the operation as ORDER-DEPENDENT or ORDER-INDEPENDENT — this, not speed, determines the concurrency model (see I.C). |
| 84 | Partition, don't globally serialize — sequential within a key, parallel across keys (see I.D, Part VII.C). |
| 85 | Concurrency is never added until every program-order/wall-clock assumption in the code is found and audited. |
| 86 | Every concurrent write path states its ordering guarantee explicitly: total, per-key, causal, or none. |
| 87 | Idempotency is a prerequisite for concurrency-with-retries, never an optional add-on. |
| 88 | Predictability is tested, not assumed — every concurrent path gets adversarial-interleaving stress tests. |

### Tier XVIII — Maintainability & Debuggability `[CRITICAL]`

| # | Rule |
|---|---|
| 89 | Comments explain WHY, never WHAT. |
| 90 | Every system boundary carries a traceable identifier at runtime (request/trace/correlation ID). |
| 91 | Complexity is budgeted, not free — every abstraction justifies its cost against 3am debugging time. |
| 92 | A system is only as maintainable as its worst-documented failure mode. |
| 93 | Reproducibility is a feature — every non-deterministic bug gets its source of non-determinism named before being called fixed. |

### Tier XIX — Theoretical Grounding & Measurement Integrity `[BLOCKER — new]`

| # | Rule |
|---|---|
| 94 | Recognize NP-hard problem shapes early (TSP/knapsack/graph-coloring/SAT-reducible patterns) — stop searching for a polynomial exact solution; move to approximation, heuristic, or constraint solver. |
| 95 | Every "optimize this NP-hard-adjacent problem" task states upfront whether exact, approximate, or heuristic is acceptable — before implementation starts, not after a week of hand-tuning a doomed exact approach. |
| 96 | Every bounded resource pool is sized using Little's Law (`L = λW`) from measured λ and W — never a round number chosen by feel (see I.A, I.I). |
| 97 | Coordinated omission is checked for in every latency benchmark — closed-loop load generation systematically undercounts tail latency; open-loop (constant arrival rate) generation is required for trustworthy p99/p999 (see Part VI). |
| 98 | Every capacity model accounts for arrival variance, not just mean rate — bursty/self-similar traffic needs a higher safety margin than Poisson math suggests, because queueing delay is driven by variance as much as by mean utilization (see I.B). |

---

## PART III — ALGORITHM TAXONOMY

### III.A String Algorithms — Selection Tree

```
                    Need to work with strings?
                              │
          ┌───────────────────┼────────────────────┐
          │                    │                    │
   Single pattern        Multiple patterns     Substring/structure
   exact match            simultaneously          queries at scale
          │                    │                    │
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌────────────────┐    ┌──────────────────┐
   │ Streaming,    │   │ Trie → Aho-    │    │ Repeated queries │
   │ no backtrack? │   │ Corasick (DFA) │    │ on same text?     │
   │  KMP O(n+m)   │   │ O(n+m+z)       │    │  Suffix Array +   │
   ├──────────────┤   └────────────────┘    │  LCP (Kasai) or   │
   │ Fuzzy/approx? │                          │  Suffix Automaton │
   │  Levenshtein/ │   Cheap pre-filter        │  O(n) build       │
   │  Bitap        │   before expensive        └──────────────────┘
   ├──────────────┤   match?
   │ Many patterns,│    Rabin-Karp / Bloom
   │ hash-based?   │    filter pre-pass
   │  Rabin-Karp   │
   └──────────────┘
```

| Algorithm | Time | Space | Composes with |
|---|---|---|---|
| KMP | O(n+m) | O(m) | Feeds Aho-Corasick generalization |
| Z-algorithm | O(n) | O(n) | Suffix array prefix-doubling |
| Rabin-Karp | O(n+m) avg | O(1) | Bloom filter pre-pass |
| Trie | O(m) | O(alphabet·n·m) | Base of Aho-Corasick, radix tree |
| Aho-Corasick | O(n+m+z) | O(m·alphabet) | Trie + KMP failure fn generalized |
| Suffix Array (SA-IS) | O(n) build | O(n) | + LCP array (Kasai, O(n)) |
| Suffix Automaton | O(n) build | O(n), ≤2n-1 states | Dedup / fingerprinting pipelines |
| Suffix Tree (Ukkonen) | O(n) | O(n), high constant | SA+LCP usually preferred in practice |
| Manacher's | O(n) | O(n) | Standalone (palindromes) |
| Levenshtein | O(nm) → O(n) space-opt | O(min(n,m)) | Bitap for O(nm/w) at scale |

**Pipeline pattern (log/search-engine scale):**
```
Ingest → Rabin-Karp/Bloom (cheap reject) → Aho-Corasick (exact multi-match)
       → Suffix automaton (dedup/near-dup on matched spans)
```

### III.B Sorting & Selection

| Algorithm | Time | Space | Notes |
|---|---|---|---|
| Introsort | O(n log n) worst | O(log n) | quicksort+heapsort fallback+insertion for small n |
| Timsort | O(n) best / O(n log n) worst | O(n) | stable, exploits runs |
| Radix sort | O(nk) | O(n+k) | fixed-width keys only |
| Quickselect | O(n) avg / O(n²) worst | O(1) | k-th order stat |
| Median of medians | O(n) worst guaranteed | O(1) | adversarial-input threat model |

### III.C Graph Algorithms

```
                What kind of graph problem?
                          │
     ┌────────────┬───────┼────────┬─────────────┐
     │             │                │              │
 Shortest path  All-pairs      Connectivity /   DAG ordering
     │           shortest        clustering          │
     ▼               │              │                ▼
 Non-negative?    Floyd-Warshall  Union-Find     Kahn's / DFS
  yes: Dijkstra    O(V³), dense   O(α(n))~O(1)   topo sort
  no: Bellman-Ford  small graphs  amortized      O(V+E)
  heuristic avail:                              → Temporal/CI
   A*                                              DAG scheduling
```

| Algorithm | Time | Use |
|---|---|---|
| Dijkstra (binary heap) | O((V+E) log V) | SSSP, non-negative weights |
| Dijkstra (Fib heap) | O(E+V log V) | Same, better on dense graphs |
| Bellman-Ford | O(VE) | Negative weights, cycle detection |
| A* | O(E) best case | Pathfinding + heuristic |
| Floyd-Warshall | O(V³) | All-pairs, dense small graphs |
| Union-Find | O(α(n)) amortized | Connectivity, Kruskal's MST |
| Tarjan's SCC | O(V+E) | Strongly connected components |
| Topological sort (Kahn's) | O(V+E) | DAG scheduling — Temporal workflows, CI pipelines |

### III.D Streaming / Probabilistic / Sketch Algorithms

```
        What are you approximating under memory pressure?
                          │
     ┌──────────┬──────────┼───────────┬──────────────┐
     │           │                      │               │
 Cardinality  Frequency of         Membership       Percentile /
 (unique      heavy hitters        test              tail latency
 count)           │                   │                  │
     │             ▼                   ▼                  ▼
     ▼        Count-Min Sketch    Bloom filter        t-digest
 HyperLogLog  O(1/ε·log 1/δ)      (no del.) or      (accurate at
 O(log log n) additive ε·N err    Cuckoo filter      tails, low mem)
                                   (supports del.)
```

| Algorithm | Space | Error | Use |
|---|---|---|---|
| HyperLogLog | O(log log n) | ~2% std err | Unique trace IDs/users at scale |
| Count-Min Sketch | O(1/ε·log(1/δ)) | additive ε·N | Top error codes/slow endpoints |
| Bloom Filter | O(n) bits | tunable FP, zero FN | Pre-filter before expensive lookup |
| Cuckoo Filter | ~Bloom | supports deletion | Same, with eviction need |
| t-digest | O(compression) | accurate at p99/p999 | Latency percentile aggregation w/o raw samples |
| Reservoir sampling | O(k) | uniform | Sampling traces from unbounded stream |
| EWMA | O(1) | decay-weighted | Anomaly baseline w/o full history |
| Fenwick Tree | O(log n) upd/qry | exact | Prefix sums, cost aggregation |
| Segment Tree | O(log n) upd/qry | exact | Range min/max/sum, superset of Fenwick |
| Skip List | O(log n) expected | exact | Concurrent-friendly ordered structure |

**Measurement-integrity note (ties to Rule 97, Part VI):** every percentile structure above is
only as trustworthy as its input stream. If the collection pipeline itself is closed-loop
(request-gated), coordinated omission corrupts the t-digest/HDR histogram before the sketch
even sees biased data — the algorithm can't correct for a biased sample.

### III.E Dynamic Programming Patterns

| Pattern | Canonical problem | Class |
|---|---|---|
| 1D DP | Fibonacci, house robber | O(n) |
| 2D DP (grid) | Edit distance, LCS | O(nm) |
| Interval DP | Matrix chain multiplication | O(n³) |
| Bitmask DP | TSP, subset assignment | O(2ⁿ·n) |
| Digit DP | Counting w/ digit constraints | O(digits·states) |
| Tree DP | Max independent set on tree | O(n) |
| DP on DAG | Longest path (topo order) | O(V+E) |

**NP-hardness recognition (Rule 94):** Bitmask DP over subsets (TSP-shape) is exponential by
construction — its presence in the table above is not an endorsement to hand-roll it at scale.
Recognize the shape, then apply Rule 94/95: choose approximate or heuristic explicitly, don't
default to "make the exact DP faster."

---

## PART IV — CONCURRENCY TAXONOMY

### IV.A Primitive Selection Tree

```
              Shared mutable state — what access pattern?
                              │
     ┌─────────────┬──────────┼───────────┬───────────────┐
     │              │                      │                │
 Read-heavy,    Very short         Bounded resource    Wait/notify
 write-rare     critical section    counting             on predicate
     │              │                      │                │
     ▼              ▼                      ▼                ▼
  RWLock       hold-time <         Semaphore           Condition
  (reader      context-switch                          Variable
  starvation   cost?                                   (needs paired
  risk under    yes: Spinlock                           mutex)
  write-heavy   no: Mutex
  load)
```

### IV.B Lock-Free / Wait-Free Ladder

```
        Contention measured as high? ── no ──▶ Lock-based (Mutex) is correct.
                    │ yes
                    ▼
        Need arbitrary structure? ── no, stack/queue only ──▶
                    │                         Treiber Stack /
                    │ yes                     Michael-Scott Queue
                    ▼
        CAS-based custom lock-free structure
                    │
                    ▼
        Memory reclamation strategy required:
          - Hazard Pointers  (per-thread registry, more control)
          - Epoch-Based Reclamation (crossbeam-style, lower overhead)
          - RCU  (wait-free reads, readers never block)
```

| Technique | Mechanism | Guarantee | Use |
|---|---|---|---|
| CAS | HW atomic | lock-free | building block |
| LL/SC | ARM/RISC alt to CAS | lock-free | ARM lock-free structures |
| Treiber Stack | CAS linked-list | lock-free | simple stack |
| Michael-Scott Queue | CAS + dummy node | lock-free | standard FIFO |
| Hazard Pointers | per-thread ptr registry | safe reclaim | lock-free w/o GC |
| Epoch-Based Reclamation | global epoch, deferred free | safe reclaim, lower overhead | `crossbeam`-style systems |
| RCU | readers never block, writer copy-swap | wait-free reads | kernel structures, read-dominant |
| Disruptor Pattern | pre-allocated ring buffer | wait-free single producer | ultra-low-latency pipelines |

### IV.C Concurrency Model Selection Tree

```
                What shape is the workload?
                          │
     ┌────────────┬────────┼─────────┬────────────────┐
     │             │                  │                 │
 I/O-bound,    CPU-bound        Composable ops   Fault-isolated
 high conn.    divide&conquer   w/o manual lock   independent units
 count             │                  │                 │
     │              ▼                  ▼                 ▼
     ▼          Fork-Join /        STM            Actor Model
 Event Loop /   Work-Stealing    (optimistic,     (Erlang/Akka,
 Reactor        (ForkJoinPool)   rollback on      supervision
 (Node,                          conflict)         trees)
 asyncio)
     │
     ▼
 CPU-bound work
 blocks the loop
 → offload to
 executor/thread
```

Go's default model sits outside this tree as CSP (goroutines + channels — share memory by
communicating, not the reverse). Treat CSP as a first-class fifth branch when the language is Go.

| Model | Core idea | Best fit | Weakness |
|---|---|---|---|
| CSP | Channels, share-by-communicating | Go native; pipelines | Channel misuse → deadlock |
| Actor | Isolated state, messages only | Erlang/Akka fault isolation | Backpressure must be explicit |
| STM | Optimistic tx + rollback | Composable concurrent ops | Retry storms under contention |
| Fork-Join | Recursive divide/execute/join | CPU-bound divide&conquer | Overhead not worth small units |
| Work-Stealing | Idle threads steal work | Heterogeneous task-size balancing | Can hurt cache locality |
| Event Loop/Reactor | Single-thread, non-blocking I/O mux | Node/asyncio, I/O-bound | CPU work blocks whole loop |
| Proactor | Async I/O completion callback | `io_uring`, Windows IOCP | More complex than reactor |
| Thread Pool | Fixed/bounded workers on queue | General bounded concurrency | Sizing is its own tuning problem (I.I) |

### IV.D Coordination Patterns

| Pattern | Purpose |
|---|---|
| Single-flight / Request Coalescing | Collapse duplicate concurrent requests (thundering herd defense) |
| Fan-out / Fan-in | Parallel dispatch to N workers, merge results |
| Pipeline | Stage-based, concurrent stages, bounded channels between |
| Worker Pool | Fixed consumers pulling a shared queue |
| Pub-Sub | Decoupled producers/consumers via topic/broker |
| Saga | Distributed transaction via compensating actions |
| Leader Election | Single coordinator among peers (Raft/ZooKeeper/etcd) |
| 2PC / 3PC | Distributed atomic commit — rarely used at scale (blocking) |

### IV.E Distributed Consensus & Coordination

| Technique | Guarantee | Real-world use |
|---|---|---|
| Raft | Leader-based consensus | etcd, Consul, CockroachDB |
| Paxos/Multi-Paxos | Consensus, harder to implement | Chubby, Spanner variant |
| Vector Clocks | Partial causal ordering | Dynamo-style, conflict detection |
| Lamport Timestamps | Total ordering w/o sync clocks | Distributed logging |
| CRDTs | Convergent state, no coordination | Collaborative edit, eventually-consistent counters |
| Distributed Locks (Redlock/etcd lease) | Cross-node mutual exclusion | Leader-only cron — use cautiously, disputed correctness (Redlock) |

---

## PART V — LANGUAGE IMPLEMENTATION MATRIX

### V.A Primitive → Library Mapping

| Concept | Kotlin | Go | Python |
|---|---|---|---|
| Lightweight concurrent unit | `kotlinx.coroutines` `launch{}`/`async{}` | `go func(){}` goroutine | `asyncio.create_task()` |
| Thread/worker pool | `Dispatchers.IO`/`Default`, custom `Executors...asCoroutineDispatcher()` | `GOMAXPROCS` (M:N scheduler onto OS threads) | `ThreadPoolExecutor`, `ProcessPoolExecutor` |
| Structured concurrency | `coroutineScope{}`, `supervisorScope{}` | `errgroup.Group` (`x/sync/errgroup`) | `asyncio.TaskGroup` (3.11+), `anyio` |
| Channel | `kotlinx.coroutines.channels.Channel` | native `chan T`, `select` | `asyncio.Queue`, `multiprocessing.Queue` |
| Mutex | `kotlinx.coroutines.sync.Mutex` | `sync.Mutex` | `asyncio.Lock`, `threading.Lock` |
| RWLock | `ReentrantReadWriteLock` | `sync.RWMutex` | no stdlib — `readerwriterlock` pkg |
| WaitGroup / join-all | `Job.join()`, `awaitAll()` | `sync.WaitGroup` | `asyncio.gather()` |
| Once-only init | `lazy {}`, or `AtomicBoolean` guard | `sync.Once` | import-time singleton, `functools.lru_cache` factory |
| Atomics | `j.u.c.atomic.AtomicLong/Reference` | `sync/atomic` (`atomic.Int64`, CAS) | no true atomics under GIL — `threading.Lock` or `multiprocessing.Value` |
| Concurrent map | `ConcurrentHashMap` | `sync.Map` (often plain map+mutex preferred) | `dict` thread-safe per-op only, not compound |
| Future/Promise | `Deferred<T>` | none native — channel-of-1 or `errgroup` | `concurrent.futures.Future`, `asyncio.Future` |
| Object pool | manual, `Channel` as free-list | `sync.Pool` (GC-aware) | no stdlib — manual `queue.Queue` |
| Rate limiting | manual token bucket + `Semaphore` | `x/time/rate` (`rate.Limiter`) | `asyncio-throttle`, manual token bucket |
| Timeout/cancellation | `withTimeout{}`, structured `CancellationException` | `context.WithTimeout/WithCancel` | `asyncio.wait_for()`, `asyncio.timeout()` (3.11+) |

### V.B Runtime-Specific Non-Negotiables

**Python**
1. `[BLOCKER]` GIL means `threading` = concurrency, not parallelism, for CPU-bound work. CPU-bound → `multiprocessing`/`ProcessPoolExecutor`, always.
2. `[BLOCKER]` `asyncio` is single-threaded cooperative — one blocking call stalls the whole loop. Offload via `loop.run_in_executor()`.
3. `[STANDARD]` 3.13+ free-threaded build is experimental — never assume no-GIL behavior without verifying the interpreter build in use.
4. `[CRITICAL]` `multiprocessing` pays a pickle tax per message — batch payloads, never fine-grained cross-process messages.

**Go**
5. `[CRITICAL]` Goroutines are cheap (~2KB stack) but not free — unbounded goroutine-per-request is a resource leak. Always bound with a worker pool or semaphore channel.
6. `[BLOCKER]` A goroutine blocked forever on an unread channel is a silent leak — every goroutine needs a guaranteed exit path.
7. `[STANDARD]` `sync.Map` is not a default — optimized for write-once-read-many or disjoint key sets. Plain `map`+`sync.RWMutex` is usually correct and faster.

**Kotlin/JVM**
8. `[CRITICAL]` `Dispatchers.IO`/`Default` are separate pools — CPU-bound work on `IO` starves I/O tasks sharing that pool, and vice versa.
9. `[BLOCKER]` Structured concurrency is mandatory — unstructured `GlobalScope.launch` detaches lifecycle from caller and leaks on cancellation.
10. `[STANDARD]` JIT warm-up means cold-path benchmarks mislead — always benchmark post-warm-up (Rule 49).

### V.C Pattern → Idiom Mapping

| Pattern | Kotlin | Go | Python |
|---|---|---|---|
| Object pooling | manual pool + `Channel<T>` | `sync.Pool` | manual `queue.Queue` |
| Copy-on-write | `kotlinx.collections.immutable` | manual rebuild | tuple/`frozenset` convention |
| Immutable config builder | `data class` + `copy()` | functional options pattern | `dataclasses.replace()`, `attrs` builder |
| Circuit breaker | `resilience4j-kotlin` | `sony/gobreaker` | `pybreaker` |
| Retry w/ backoff | `kotlin-retry` | `cenkalti/backoff` | `tenacity` |
| Bulkhead isolation | separate `CoroutineDispatcher` per subsystem | separate goroutine pools/semaphores | separate `ThreadPoolExecutor`/`ProcessPoolExecutor` |
| Batching | `Flow.chunked()`, `Flow.buffer()` | manual channel batch + `time.Ticker` | manual via `asyncio.Queue` + timeout gather |

---

## PART VI — EMERGENT FAILURE MODE ENCYCLOPEDIA

Named patterns, each with mechanism, detection signal, and prevention. These are what the laws
in Part II exist to prevent — read this part as "the crime scenes," Part II as "the law that
would have prevented them."

**Thundering Herd**
- *Mechanism:* many clients act on the same trigger (cache expiry, service recovery, cron) simultaneously, with no coordination between them.
- *Detection:* sharp periodic spikes correlated with a shared TTL/schedule, not with real traffic growth.
- *Prevention:* jittered TTL, single-flight coalescing, staggered schedules. → Rules 30, 32.

**Cache Stampede** (special case of thundering herd)
- *Mechanism:* a popular key expires; many concurrent readers all miss and all regenerate the value at once.
- *Detection:* backend load spikes exactly at cache-key TTL boundaries.
- *Prevention:* single-flight on regeneration, probabilistic early expiration, stale-while-revalidate. → Rule 30.

**Retry Storm**
- *Mechanism:* many clients retry a failure at the same time, amplifying load on an already-struggling dependency.
- *Detection:* retry rate spikes in lockstep with the original failure; dependency load climbs faster than client count.
- *Prevention:* jittered exponential backoff, circuit breaker to stop retrying past a threshold. → Rules 32, 34.

**Cascading Failure**
- *Mechanism:* failure/slowness in one component propagates and amplifies into nominally-healthy components, via synchronous blocking calls with no isolation.
- *Detection:* multiple unrelated services degrade within seconds of each other, tracing to one root dependency.
- *Prevention:* timeouts everywhere, circuit breakers, bulkhead isolation, load shedding. → Rules 31, 34, 61.

**Metastable Failure** (advanced — outlasts its own trigger)
- *Mechanism:* the system, once pushed into a degraded state, stays degraded even after the original trigger is removed, because the degraded state itself generates the load that sustains it (retry backlog, cache-miss regeneration load, queue backlog).
- *Detection:* the system doesn't recover when the triggering incident resolves — it stays saturated until an explicit intervention (aggressive shed, restart, manual drain) breaks the internal feedback loop.
- *Prevention:* load shedding more aggressive than "seems necessary" during recovery; backlog draining that doesn't just resume normal traffic instantly. → Rules 61, 62.

**Hot Key / Hot Partition**
- *Mechanism:* one partition/shard/key receives disproportionate traffic, capping throughput at that partition's limit regardless of total cluster capacity.
- *Detection:* one partition's lag/CPU is far above its siblings while others idle.
- *Prevention:* key salting for known hot keys, per-partition skew monitoring, not just aggregate throughput. → Rule 36, I.D.

**Connection Pool Exhaustion Death Spiral**
- *Mechanism:* Little's Law in reverse (I.A) — rising latency W with fixed pool size L collapses throughput λ, while arrivals continue at the original rate, growing the wait queue unboundedly.
- *Detection:* pool wait time climbing while checked-out count reads 100%, latency growing non-linearly.
- *Prevention:* bound pool wait time itself (fail fast, don't queue forever); separate pools per downstream dependency so one slow dependency doesn't starve pools serving others. → Rules 19, 25, 96.

**GC Death Spiral**
- *Mechanism:* memory pressure triggers longer/more frequent GC pauses, which slow the app, which grows the request backlog, which increases memory pressure further.
- *Detection:* GC pause frequency/duration climbing together with request latency; memory sawtoothing at a rising baseline instead of returning to baseline.
- *Prevention:* reduce hot-path allocation rate, choose GC algorithm against the latency SLO ahead of time, define the GC pause budget explicitly. → Rules 12, 14, 51.

**Unbounded Queue Death Spiral**
- *Mechanism:* a queue with no bound absorbs backlog instead of applying backpressure, converting a throughput problem into an unbounded memory problem.
- *Detection:* queue depth trending up without bound, not oscillating around a stable point.
- *Prevention:* explicit backpressure at every queue boundary, bounded queues with a defined rejection/shedding policy. → Rule 22.

**Coordinated Omission** (critical — measurement integrity, directly relevant to any latency-percentile system)
- *Mechanism:* a closed-loop load generator (wait for response, then send next request) systematically undercounts tail latency, because it never issues the requests a real, constant-rate source would have kept sending during a slowdown — they simply never get "sent" in the test, so they never get counted as slow.
- *Detection:* benchmark p99 looks great, but production p99 under organic (non-request-gated) traffic is far worse for the same load.
- *Prevention:* open-loop (constant arrival rate) load generation for latency benchmarks; verify any percentile library's coordinated-omission-correction mode is enabled. The same bias can hide inside a production sampling/collection pipeline if it is itself request-gated, not just in benchmarks. → Rules 2, 3, 6, 97.

**Lock Convoy**
- *Mechanism:* multiple threads contend for the same lock in a way that synchronizes their scheduling — once one is delayed, others queue behind it in a self-reinforcing pattern that can outlast the original contention source.
- *Detection:* throughput drops in a stair-step/plateau pattern correlated with thread count, not smoothly.
- *Prevention:* reduce lock hold time, consider lock-free/partitioned alternatives once contention is measured. → Rules 19, 20.

**Priority Inversion**
- *Mechanism:* a low-priority task holds a resource a high-priority task needs; medium-priority tasks preempt the low-priority holder, indefinitely delaying the high-priority task.
- *Detection:* high-priority work stalls disproportionately during unrelated medium-priority load, not explained by the resource's own contention level.
- *Prevention:* priority inheritance protocols where supported, or avoid resource sharing across priority classes entirely.

**Split Brain**
- *Mechanism:* a network partition causes two subsets of a distributed system to each believe they're the sole leader/owner, producing conflicting writes.
- *Detection:* conflicting writes to the same logical record from two nodes claiming leadership in the same window.
- *Prevention:* quorum-based consensus with odd cluster sizes, fencing tokens on leadership handoff. → Rule 35, Part IV.E.

**Write Amplification**
- *Mechanism:* physical bytes written to storage are a multiple of the logical bytes the application intended, from LSM-tree compaction, SSD flash-translation-layer rewrites, or index maintenance.
- *Detection:* disk write throughput far exceeds application-level write volume; SSD wear/latency degrades faster than logical write volume predicts.
- *Prevention:* batch writes, choose storage engine/compaction strategy matched to write pattern, monitor the amplification ratio directly. → Rule 23.

---

## PART VII — PRE-CODE THINKING PROTOCOL

Run this sequence before writing any function, module, schema, or concurrent path that will
outlive a prototype.

```
 1. DEFINE THE CONTRACT
    → inputs, outputs, invariants, and — critically — the failure modes.

 2. ENUMERATE BOUNDARIES BEFORE LOGIC
    → null / empty / zero / negative / max / duplicate / wrong-encoding, for every input.
    → Do this before the first line of happy-path logic.

 3. CLASSIFY DATA RELATIONSHIPS
    → What has an independent lifecycle? What changes together? What's the write path?

 4. CLASSIFY OPERATIONS BY ORDER-DEPENDENCY
    → order-dependent vs. order-independent, before reaching for a thread pool.

 5. MATCH COMPLEXITY TO ACTUAL SCALE
    → design for the scale you have evidence for; note where the future seam would go.

 6. DEFINE THE OBSERVABILITY PLAN BEFORE THE LOGIC
    → how will this be traced, logged, measured when it breaks?

 7. WRITE THE HAPPY PATH LAST
    → everything above constrains it; writing it first rationalizes away the boundaries
      you just enumerated.
```

### VII.A Decision Tree — Defensive Boundary Checking

```
Is this value externally sourced?
(user input, API/network response, DB row, file, deserialized payload)
 │
 ├─ YES → treat as UNTRUSTED
 │         │
 │         ├─ Can it be structurally guaranteed non-null/valid at the boundary?
 │         │   (schema validation, DB NOT NULL constraint, strict deserialization)
 │         │     │
 │         │     ├─ YES → enforce ONCE at the boundary; trust it downstream.
 │         │     │         Re-checking deeper in the call chain is noise, not safety.
 │         │     │
 │         │     └─ NO  → explicit check REQUIRED here. Fail loud. Don't pass forward
 │         │               unchecked "just this once."
 │
 └─ NO → internally produced (from your own function/module)
           │
           ├─ Can your own invariants guarantee validity?
           │     │
           │     ├─ YES → no redundant check needed downstream.
           │     └─ NO  → this is a DESIGN GAP, not a missing-null-check gap.
           │               Fix the producer; don't patch every consumer.
```

**The strict rule this encodes:** every null/empty check exists because a value crosses a trust
boundary, or because the producer's own guarantee is genuinely unprovable. Anything else is
either a missing check (bug) or a redundant one (complexity tax, Rule 91).

### VII.B Decision Tree — Schema Granularity ("How many tables, actually")

```
For each CANDIDATE entity, score against these four questions:

  Q1. Independent lifecycle? (created/updated/deleted separately from the "parent")
        YES → +1 toward separate table
  Q2. Independent write-concurrency profile? (different actors/rate/tx boundary)
        YES → +1 toward separate table
  Q3. Queried independently, at meaningful volume today (not "might be useful")?
        YES → +1 toward separate table
  Q4. Does normalizing it prevent a real update anomaly (same fact stored 2+ places,
      can drift)?
        YES → +1 toward separate table, and near non-negotiable on its own

DECISION RULE:
  score >= 2  →  separate table, justified.
  score <= 1  →  embed / inline. Revisit only when an access pattern actually changes.

OVER-NORMALIZATION warning signs ("100 tables" failure):
  - every table scores only on Q4, structurally, with no real anomaly risk
  - most queries require 4+ joins to answer one business question
  - the write path touches 6+ tables for one logical transaction

UNDER-NORMALIZATION warning signs ("10 tables of everything" failure):
  - the same fact updated in multiple rows, kept in sync by application code
  - one table serves 3+ unrelated write-concurrency profiles
  - "add a column" is the answer to 12+ unrelated requirements in a row
```

### VII.C Decision Tree — Concurrency Without Losing Predictability

```
STEP 1 — Order dependency test
  Does correctness depend on THIS operation happening strictly before/after another
  specific operation (e.g., writes to the same row/aggregate)?
    YES → ORDER-DEPENDENT relative to that operation. Do not parallelize relative to it.
          Continue to Step 2 to see if speed is still gainable elsewhere.
    NO  → go directly to Step 3.

STEP 2 — Partition test
  Is there a natural partition key such that order matters WITHIN the key but not
  ACROSS keys? (user ID, account ID, aggregate ID, tenant ID...)
    YES → PARTITION BY KEY.
          - sequential within a partition (preserves the ordering correctness needs)
          - parallel across partitions (this is where the speed comes from)
          - same principle as single-writer-per-aggregate, actor-per-entity,
            Kafka partition-per-key
    NO  → the operation may need to stay globally sequential. Look for speed instead in:
          batching within the sequential path, reducing per-operation cost, or
          re-examining whether "must be ordered" is still actually true.

STEP 3 — Idempotency gate
  Is the operation idempotent and safely retryable?
    NO  → make it idempotent FIRST (idempotency key, dedup, upsert-not-insert) before
          adding concurrency or retries. Concurrency without idempotency is a
          corruption generator with a delay timer.
    YES → continue to Step 4.

STEP 4 — Name the guarantee
  State explicitly: [ total order | per-key order | causal order | no order ].
  If you can't name one, you don't have a concurrency design — you have a hope.

STEP 5 — Adversarial verification
  Stress-test under adversarial interleaving (max parallelism, deliberately reordered
  completions, injected delays) before calling this done. A test that only runs the
  "normal" interleaving has tested the happy path twice, not the concurrency.
```

**One-sentence internalization:** concurrency exploits order-INDEPENDENCE that already exists —
it never removes order-DEPENDENCE the domain actually requires. Trying to make an
order-dependent operation "just be concurrent" trades a predictable slow system for an
unpredictable fast one; that trade must be named and accepted explicitly, never implicit.

### VII.D Decision Tree — Complexity / Abstraction Budget

```
Before adding an abstraction layer (interface, generic, indirection, framework):

  1. Does this remove duplicated REASONING, not just duplicated text?
  2. Can a new engineer understand the CONCRETE behavior from one layer, or will
     they trace N layers to find out what actually happens?
  3. Is this solving a problem you have EVIDENCE for now, or one you can imagine?
     (YAGNI check — weighed against Rule 40: state the cost either way.)
  4. What's the cost, in 3am-debugging-minutes, of this indirection existing,
     multiplied by how often this path gets debugged?

DECISION: add the abstraction only if (1) is true AND (3) is "have evidence now."
          Otherwise: write the concrete version; note in a comment where the seam
          would go if the imagined future arrives.
```

---

## PART VIII — CRITICAL QUESTION CHECKLISTS

A "no" or "I don't know" is a blocking finding, not a note for later.

### VIII.A Before Writing Any Function or Module
1. What are ALL the inputs, including ones the type system doesn't force — null, empty, zero, negative, duplicate, out-of-range, wrong encoding?
2. What's the stated contract when any of the above occurs? Is it visible to a caller without reading the implementation?
3. What does this function silently assume the caller already validated — and is that assumption safe?
4. If called by 10,000 concurrent callers right now, does it still behave correctly?
5. What's the complexity if the input is 100x the size I'm imagining?
6. When this fails, does the caller see a clear signal of what broke — or a stack trace with no context?

### VIII.B Before Designing a Schema or Data Model
7. What does the WRITE path actually need — not what feels conceptually "correct" to model?
8. Which fields change together vs. independently?
9. Will most reads need parent+child together or independently, and at what relative volume?
10. Where could the same fact end up stored twice, and what stops it from drifting?
11. What happens to related data on delete — decided now, or discovered during an incident?

### VIII.C Before Adding Concurrency
12. Is this operation order-dependent relative to any other operation? (VII.C Step 1)
13. Is there a natural partition key preserving per-entity order with cross-entity parallelism?
14. Is the operation idempotent? Is making it idempotent scheduled BEFORE the concurrency work?
15. What ordering guarantee am I providing — total, per-key, causal, or none?
16. What's the blast radius if two run out of order — wasted work, or corrupted state? Is that explicitly accepted by someone with authority to accept it?
17. Have I stress-tested under adversarial interleaving, or only the interleaving that happened locally?

### VIII.D Before Merge / Self-Review
18. Can I explain, in one sentence, WHY this is correct — not just that it passed my test?
19. Did I test the boundary conditions, or only the happy path?
20. What's the rollback path if this is wrong in production, and has it been exercised?
21. What did I deliberately NOT handle — and did I say so out loud, or is it silent?
22. Did I add any abstraction that fails the VII.D test?

### VIII.E While Debugging in Production
23. Is this reproducible? If not, what's the specific source of non-determinism?
24. Am I looking at the symptom or the cause — could this be correct behavior reacting to bad upstream data?
25. What changed most recently that touches this path?
26. Am I fixing this occurrence, or the whole class of occurrence?
27. If I can't reproduce it, have I at least named the non-determinism before calling it closed?

---

## PART IX — DAILY PRACTICE PROTOCOL

```
DAILY (5–15 min, pick 1)
  □ Re-derive the complexity (Big-O AND real constant factor) of code you touched
    today, from first principles, without looking it up.
  □ Run the VIII.A checklist against one function you wrote, honestly.
  □ Read one incident postmortem and extract the ONE rule that would have prevented it.

WEEKLY
  □ Profile one hot path you assumed was fine; check the assumption still holds
    under current load.
  □ Run VII.B fresh against one schema/table you maintain, as if seeing it new.
  □ Re-verify one concurrent path's stated ordering guarantee (VII.C Step 4) is
    still accurate — refactors erode ordering guarantees more often than they
    violate types.

MONTHLY
  □ Re-read Tier VII (Distributed Systems) and Tier XIII (Production Safety)
    against current systems — these decay fastest as systems outgrow their
    original design assumptions.
  □ Audit one abstraction added >3 months ago against VII.D — did it pay for
    itself, or is it now indirection nobody remembers the reason for?

STANDARD THIS IS HELD TO:
  If you cannot currently answer "what's my ordering guarantee on my busiest
  concurrent write path, and when did I last verify it," this loop is overdue,
  not optional-and-skipped.
```

---

## PART X — CROSS-REFERENCE MATRIX

| Law # | Law (short) | First Principle | Failure Mode Prevented | Technique |
|---|---|---|---|---|
| 1, 44, 50 | Profiler-verified, hardware-counter-verified | — | wasted optimization effort | perf/flame graph, `perf stat` |
| 2, 3, 97 | Percentile + N reporting | I.G latency ladder | Coordinated Omission | HDR histogram / t-digest, open-loop load gen |
| 9, 10 | Worst-case stated | I.H amortized analysis | latency SLO breach at resize/rebalance | potential-method proof |
| 13 | Cache-line padding | I.G (L1 vs. memory gap) | Lock Convoy (contributing factor) | 64B/128B padding |
| 20, 21 | wait-free>lock-free>lock priority | — | Lock Convoy | Part IV.B ladder |
| 22 | Backpressure on queues | I.A Little's Law | Unbounded Queue Death Spiral | bounded queue, Part IV.D Pipeline |
| 25, 96 | Pool exhaustion = P0, sized via Little's Law | I.A, I.I | Connection Pool Exhaustion Death Spiral | finite-pool sizing math |
| 30 | Thundering herd protection | I.B utilization/queueing | Thundering Herd, Cache Stampede | single-flight, Part IV.D |
| 31–34 | Timeout/retry/idempotency/breaker | I.F CAP/PACELC | Retry Storm, Cascading Failure | circuit breaker, jittered backoff |
| 33 | Fan-out tail amplification | I.G latency ladder | — | composed-probability calc |
| 36 | Shard key skew | I.D USL (κ term) | Hot Key / Hot Partition | Count-Min Sketch detection |
| 38 | Saturation trend, not avg utilization | I.B utilization law | Metastable Failure, GC Death Spiral | queue-depth trend monitoring |
| 51 | GC algorithm tied to SLO | I.H (pause spikes) | GC Death Spiral | pause-budget design |
| 61, 62 | Load shedding defined in advance | — | Metastable Failure | rehearsed degradation order |
| 83, 84 | Order-dependency classification, partition don't serialize | I.C Amdahl, I.D USL | Lock Convoy, Split Brain | Part VII.C tree |
| 86 | Ordering guarantee stated | I.F CAP/PACELC | Split Brain | Part IV.E consensus |
| 94, 95 | NP-hard recognition, approximation stated upfront | — | wasted engineering effort on doomed exact solutions | approximation/heuristic, Part III.E note |
| 98 | Arrival variance in capacity models | I.B (PASTA caveat) | undersized capacity under bursty load | variance-aware safety margin |

---

## APPENDIX A — Severity Legend

- `[BLOCKER]` — causes incidents/outages if violated.
- `[CRITICAL]` — causes silent long-term regression or data risk if violated.
- `[STANDARD]` — strong default; deviate only with a stated, measured reason.

## APPENDIX B — Glossary

- **RTT** — round trip time.
- **SLI/SLO** — service level indicator / objective.
- **CAS** — compare-and-swap.
- **EBR** — epoch-based reclamation.
- **SSSP** — single-source shortest path.
- **N+1 query** — one query for a list, then one query per item — a scaling anti-pattern.
- **PASTA** — Poisson Arrivals See Time Averages; a queueing-theory assumption that breaks under bursty traffic.
- **USL** — Universal Scalability Law (Gunther); Amdahl's Law extended with contention (σ) and coherency (κ) costs.

---

## SYNTHESIS — The One-Paragraph Internalization

Before writing code that will outlive a prototype: know the theory that makes the rule true, not
just the rule (Part I grounds Part II — a rule you can't derive is a rule you'll abandon under
pressure). Define the contract and its failure modes before the happy path exists. Enumerate
boundaries, because "works today" and "correct" are different claims — the gap between them is
exactly where Part VI's failure modes live. Size data models to actual access patterns, not
aesthetics in either direction. Classify every operation as order-dependent or
order-independent before reaching for concurrency, and get speed from partitioning real
independence — never from erasing real dependence. Budget every abstraction against the
3am-debugging cost it creates. Treat all of this as a practice run continuously (Part IX),
because load shape, traffic skew, and scale keep changing even when the code doesn't — and
treat every rule here as falsifiable by your own measured data (Rule 72), because a rule that
survives contact with your profiler is worth more than a hundred that merely sound right.