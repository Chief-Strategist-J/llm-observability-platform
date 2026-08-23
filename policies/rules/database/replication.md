# Replication — Copies of Data Across Nodes (Deep-Dive Edition)

*Availability, Read Scaling, and the Hardest Problem in Distributed Systems*

---

## 1. What Is Replication? (Formal View)

Replication is the maintenance of **N ≥ 2 physical copies** of one logical piece of state, `S`, across nodes `{n1, n2, ... nN}`, such that a well-defined subset of those copies can answer for `S` under a stated **consistency model**.

Formally, a replication system is the tuple:

```
R = (N, W_policy, Propagation, ConflictResolution, ConsistencyModel)
```

- `N` — replication factor (how many copies exist)
- `W_policy` — who is allowed to accept a write (leader / multi-leader / leaderless)
- `Propagation` — the mechanism that moves a write from where it landed to the other N-1 copies
- `ConflictResolution` — what happens when two writes touch the same logical state without knowing about each other
- `ConsistencyModel` — the guarantee the system is willing to make about what a reader will see (linearizable → sequential → causal → eventual)

Every named "replication technology" (MySQL replication, Kafka partitions, Cassandra, DynamoDB, Raft-based etcd, Spanner) is just a specific instantiation of this tuple. Once you can classify a system along these five axes, you can predict its failure modes without reading its source code — this is the entire point of studying replication as a *pattern language* rather than as a list of products.

**What it is not:**
- Not partitioning/sharding (that solves *volume*; replication solves *availability + read-scale + durability*). They compose (`Sharded Replication`), they don't substitute for each other.
- Not backup. A backup is a point-in-time, usually offline, recovery artifact. A replica is a live, queryable, usually-online copy participating in the system's real-time behavior.
- Not caching, although caches often look like leaderless, TTL-bounded, LWW-resolved replicas — the boundary is blurrier than people admit (see §7).

---

## 2. Why Replication? — From First Principles

### 2.1 The three physical facts

1. **Nodes fail** — MTBF (mean time between failures) of any single disk/node is finite. At data-center scale (10,000+ disks), a failure is not an edge case, it is a Tuesday. Annualized failure rate of consumer-grade disks in large-scale studies (Google, Backblaze) sits around 1–5% per year — with 10,000 disks that's multiple failures *per day*.
2. **Networks are neither instantaneous nor reliable** — message delay is bounded below by the speed of light (a round trip across a continent is tens of milliseconds no matter how good your code is) and unbounded above by congestion, partition, or routing failure. This is a hard physical floor, not a solvable engineering problem.
3. **Read/write ratios are asymmetric** — real-world systems (social feeds, product catalogs, ML feature serving) see read:write ratios from 10:1 to 10,000:1. A single-copy system's read throughput ceiling becomes the *entire system's* ceiling.

### 2.2 The formal consequence: CAP and PACELC

Given fact #2 (networks partition), Brewer's CAP theorem proves you cannot simultaneously offer:

- **C**onsistency (every read sees the latest write)
- **A**vailability (every request gets a non-error response)
- **P**artition tolerance (the system keeps working when the network splits)

...at the same time, during an actual partition. Since fact #2 says partitions *will* happen, every replicated system pre-commits, at design time, to being CP or AP during those events.

**PACELC** (Abadi) extends this to the *normal* case: even when there is **no** partition, you still trade **L**atency against **C**onsistency, because synchronous replication (waiting for other copies) costs round-trip time. This is why "eventually consistent" systems exist even in healthy, non-partitioned networks — it's not paranoia, it's a latency optimization.

### 2.3 First-principles restatement

> Replication exists to buy **availability** and **read-scale** against the hard floor of "nodes die, networks are slow/unreliable." Every mechanism past this point — quorums, vector clocks, Raft — is machinery to make that trade **explicit and tunable** instead of implicit and accidental.

---

## 3. Core Architecture — Full Decision Trees

Every replication system is the answer to a sequence of decisions. Below is the complete decision tree, expanded at every branch, in the order these decisions are actually made when designing a system.

### 3.1 Decision Point 1 — Who Accepts Writes?

```log
└── Q1: Who is allowed to accept a write?
    ├── Single-Leader (Primary–Replica)
    │   ├── Topology: star (1 leader, N-1 followers)
    │   ├── Write path: client → leader → log → followers
    │   ├── Failure mode: leader dies
    │   │   ├── Manual failover (human promotes a follower)
    │   │   └── Automatic failover (election protocol, e.g. Raft/ZooKeeper/etcd watch)
    │   ├── Read routing decision
    │   │   ├── Read from leader only → strong consistency, no read-scale benefit
    │   │   ├── Read from any follower → read-scale, risk of stale read
    │   │   └── Read-your-writes routing → pin a client's reads to leader (or a replica ≥ its last write version) after it writes
    │   └── Risk: zombie/stale leader after partition
    │       ├── Fencing tokens (monotonic epoch attached to every write)
    │       └── Lease-based leadership (leader must renew a time-bound lease)
    │
    ├── Multi-Leader
    │   ├── Topology: mesh (every leader replicates to every other leader) or star-of-leaders (regional hubs)
    │   ├── Use case driver: multi-datacenter writes, offline-first clients, edge devices
    │   ├── Conflict source: two leaders accept writes to the same key with no shared clock
    │   └── Conflict resolution decision (see §3.4 for full tree)
    │       ├── Last-Write-Wins (timestamp/epoch based)
    │       ├── Vector clocks (causal ordering, detect true concurrency)
    │       ├── CRDTs (mathematically guaranteed convergence)
    │       └── Application-defined merge (e.g. shopping-cart union, counter sum)
    │
    └── Leaderless
        ├── Topology: peer-to-peer, N replicas own each key (via consistent hashing ring)
        ├── Write path: client (or coordinator) fans out to N replicas directly
        ├── Quorum decision (see §3.3 for full tree)
        │   ├── Strict quorum: W + R > N
        │   ├── Sloppy quorum: W + R ≤ N, favors availability
        │   └── Hinted handoff: writes temporarily redirected to a healthy node when the "true" owner is down
        └── Repair decision
            ├── Read repair (client/coordinator fixes stale replica inline during a read)
            └── Background anti-entropy (Merkle-tree diff sweep, see §3.5)
```

### 3.2 Decision Point 2 — When Is a Write Acknowledged?

```log
└── Q2: When does the leader/coordinator tell the client "write succeeded"?
    ├── Synchronous
    │   ├── Ack after ALL replicas confirm durable write
    │   ├── Guarantee: zero data loss on single-node failure
    │   └── Cost: latency = slowest replica's round trip (tail-latency amplification)
    │
    ├── Asynchronous
    │   ├── Ack immediately after leader's local durable write
    │   ├── Guarantee: lowest possible write latency
    │   └── Risk: unacknowledged data loss window if leader dies before propagation completes
    │
    ├── Semi-Synchronous
    │   ├── Ack after at least 1 (or k < N) replica confirms
    │   ├── Remaining replicas updated asynchronously
    │   └── Balances durability against latency (used by MySQL semi-sync, Kafka acks=1)
    │
    └── Quorum-Tunable (leaderless systems)
        ├── W = N (write to all): strongest durability, lowest availability under failure
        ├── W = 1 (write to any one): highest availability, weakest durability
        └── W = majority (⌈N/2⌉ + 1): standard balance, matches Raft/Paxos commit rule
```

### 3.3 Decision Point 3 — Quorum Configuration (expands the leaf above)

```log
└── Q3: How do you pick W, R, N?
    ├── W + R > N (strict quorum)
    │   ├── Guarantees read/write quorum overlap → at least one replica in the read set has the latest write
    │   ├── Still NOT linearizable by default (concurrent quorum reads/writes can race)
    │   └── Common config: N=3, W=2, R=2
    │
    ├── W + R ≤ N (sloppy quorum)
    │   ├── Higher availability (fewer nodes required to respond)
    │   ├── Explicitly accepts stale reads as a possibility
    │   └── Common config: N=3, W=1, R=1 (AP-leaning systems, e.g. Cassandra ONE)
    │
    └── Dynamic/Adaptive quorum
        ├── Client-tunable per-request consistency (Cassandra: ONE / QUORUM / ALL per query)
        └── SLA-based auto-adjustment (raise W under detected corruption risk, lower under latency pressure)
```

### 3.4 Decision Point 4 — Conflict Resolution

```log
└── Q4: Two writes touched the same key with no causal knowledge of each other — now what?
    ├── Last-Write-Wins (LWW)
    │   ├── Attach wall-clock timestamp (or Lamport/Hybrid Logical Clock) to every write
    │   ├── On conflict, keep the higher timestamp, silently discard the other
    │   ├── Failure mode: clock skew silently drops a "later" write with a slower clock
    │   └── Mitigation: Hybrid Logical Clocks (HLC) bound skew using both wall time and logical counters
    │
    ├── Vector Clocks
    │   ├── Each replica maintains a per-node counter vector
    │   ├── Compare vectors: before / after / concurrent (see §10 code)
    │   ├── True concurrency (neither "before" nor "after") → surfaced to application or client (e.g. Dynamo "siblings")
    │   └── Cost: vector grows with number of writing nodes (needs pruning/garbage collection)
    │
    ├── CRDTs (Conflict-Free Replicated Data Types)
    │   ├── State-based (CvRDT): replicas exchange full state, merge via a commutative/associative/idempotent join
    │   ├── Operation-based (CmRDT): replicas exchange operations, apply commutatively
    │   ├── Types: G-Counter, PN-Counter, G-Set, OR-Set, LWW-Register, RGA (for sequences)
    │   └── Guarantee: Strong Eventual Consistency (SEC) — no coordination required, mathematically guaranteed convergence
    │
    └── Application-Level Merge
        ├── Domain-specific reconciliation function supplied by the developer
        ├── Example: shopping cart = set union of both replicas' items
        └── Risk: merge function itself must be commutative/associative or you reinvent the CRDT problem badly
```

### 3.5 Decision Point 5 — Propagation Mechanism

```log
└── Q5: How does a committed write physically reach the other replicas?
    ├── Log Shipping (Write-Ahead Log / binlog / oplog streaming)
    │   ├── Physical log shipping: byte-for-byte disk block changes (fast, but ties replicas to identical engine version)
    │   └── Logical log shipping: parsed row-level change events (portable across versions/engines)
    │
    ├── State Machine Replication (Raft / Multi-Paxos)
    │   ├── Every replica applies the exact same deterministic log in the exact same order
    │   ├── Requires a consensus protocol to agree on log order under failures
    │   └── Produces linearizable reads-from-leader by construction
    │
    ├── Change Data Capture (CDC)
    │   ├── Tail the source DB's WAL/binlog
    │   ├── Publish change events to a broker (Kafka/Pulsar)
    │   └── Fan out to heterogeneous sinks: search index, cache, data warehouse, another DB
    │
    ├── Chain Replication
    │   ├── Fixed order: head → mid1 → mid2 → ... → tail
    │   ├── Writes flow head-to-tail; reads served from tail only
    │   └── Strong consistency with high write throughput (each node only talks to 2 neighbors)
    │
    └── Gossip / Epidemic Propagation
        ├── Each node periodically picks k random peers and exchanges state digests
        ├── No single point of failure, scales sub-linearly in message count relative to full mesh
        └── Convergence is probabilistic (expected O(log N) rounds), not deterministic — needs background anti-entropy as a backstop
```

### 3.6 Decision Point 6 — Failure & Recovery Handling

```log
└── Q6: How does the system recover when a node/leader dies or reappears?
    ├── Leader Election
    │   ├── Timeout-based (Raft): follower times out waiting for heartbeat, becomes candidate
    │   ├── External coordinator (ZooKeeper/etcd watch-based leader lock)
    │   └── Split-vote handling: randomized election timeouts to avoid repeated ties
    │
    ├── Fencing (prevent zombie leader writes)
    │   ├── Monotonic epoch/term number attached to every write
    │   ├── Storage layer rejects any write with epoch < current known epoch
    │   └── Without fencing: old leader reconnecting after partition can silently overwrite newer data
    │
    └── Reconciliation on Rejoin
        ├── Catch-up via log replay (compare last applied index, stream missing entries)
        ├── Full resync (if log too far behind / log truncated — snapshot transfer)
        └── Anti-entropy sweep (Merkle diff) to catch anything log-replay missed (silent corruption, missed CDC events)
```

---

## 4. Edge Cases — Expanded

- **Split-brain**: partition + no fencing → two nodes both believe they're leader → divergent writes accepted simultaneously on both "leaders," visible to different client subsets.
- **Stale reads / read-your-writes violation**: a client writes to the leader, then reads from a lagging follower and doesn't see its own write.
- **Monotonic-read violation**: a client reads from replica A (fresh), then reads from replica B (stale) and appears to see time move *backward*.
- **Replication lag amplification**: under sustained write bursts, follower lag doesn't grow linearly — it compounds, because applying the backlog competes with disk I/O for incoming new entries, creating a feedback loop.
- **Silent data corruption propagation**: bit rot / cosmic-ray bit-flip on one replica gets faithfully replicated to all others before any integrity check catches it — replication propagates corruption exactly as efficiently as it propagates correctness.
- **Quorum overlap miscalculation**: choosing W + R ≤ N while believing you have strict-quorum guarantees — a very common production misconfiguration.
- **Clock skew in LWW**: NTP drift or a misconfigured hypervisor clock causes a semantically later write to lose to an semantically earlier one because its wall-clock timestamp reads lower.
- **Cascading failover storms**: a flapping link causes repeated leader elections; each election pauses writes system-wide for the duration of the election — a network blip becomes a multi-second outage.
- **Zombie leader / stale leader writes**: an isolated old leader doesn't yet know it's deposed and keeps accepting client writes into a log branch that will be discarded on rejoin (needs fencing tokens/epochs, §3.6).
- **Vector clock explosion**: with many writing nodes and no pruning, vector clocks grow unbounded, inflating metadata size per key far beyond the value itself.
- **CRDT metadata bloat**: OR-Sets that never garbage-collect tombstones grow forever, eventually dwarfing the useful payload.
- **Thundering herd on failover**: all clients simultaneously reconnect to the newly elected leader, overwhelming it right when it's least warmed up (cold caches, cold connection pools).
- **Asymmetric partition ("partial partition")**: node A can reach B but not C, while B can reach both — classic distributed systems textbooks assume symmetric partitions, but real networks routinely violate this, breaking naive quorum logic that assumes "reachable" is transitive.

---

## 5. The Hardest / Most Difficult Thing — Expanded

**Deciding what "correct" means for two writes that happen concurrently on two different copies, when there is no shared global clock to say which came first.**

This is not a bug-fixing problem — it's a **definitional** one, rooted in the physics of relativity of simultaneity applied to computation: without a shared clock, "simultaneous" across two nodes is not a well-defined concept (Lamport's original 1978 insight — *Time, Clocks, and the Ordering of Events in a Distributed System* — literally opens with this observation).

Every conflict-resolution mechanism is a **policy** for faking an ordering that physically doesn't exist:

- LWW fakes it with wall-clock time (accepting clock-skew risk)
- Vector clocks refuse to fake it — they honestly report "concurrent, unordered" and push the decision upward
- CRDTs sidestep the ordering question entirely by making the *merge function itself* order-independent (commutative + associative + idempotent), so no ordering decision is ever required

The genuinely hard part of system design is recognizing **which** of these three postures your business logic can tolerate — because picking wrong (e.g., LWW on a bank ledger) is a silent, compounding correctness bug that won't show up in any test that doesn't specifically inject concurrent writes with skewed clocks.

---

## 6. The Most Complex Part — Expanded

**Distributed consensus under partial, unpredictable failure (Raft / Multi-Paxos).**

### 6.1 Why it's harder than it looks

A consensus protocol must guarantee, simultaneously:

- **Election Safety**: at most one leader per term, ever
- **Leader Append-Only**: a leader never overwrites or deletes entries in its own log, only appends
- **Log Matching**: if two logs contain an entry with the same index and term, all preceding entries are identical in both
- **Leader Completeness**: if an entry is committed in a given term, it will be present in the logs of all leaders of higher terms
- **State Machine Safety**: if a server has applied an entry at a given index to its state machine, no other server will ever apply a different entry at that index

Each of these is independently easy to violate under specific interleavings of message delay, partial partition, and crash-recovery timing — and correct only in the *conjunction* of all five holding at all times.

### 6.2 Why FLP makes this provably unsolvable in theory

The Fischer–Lynch–Paterson (1985) result proves that in a **fully asynchronous** network (no bound on message delay), no consensus protocol can guarantee both safety and termination if even one node may fail. Raft and Paxos do not violate this theorem — they sidestep it by relying on **partial synchrony**: timeouts that are *usually* long enough to distinguish "slow" from "dead," but are not formally guaranteed to be. This is why consensus systems can, in rare pathological network conditions, stall (safe but not live) rather than elect a leader — this is a feature, not a bug: it's the theorem's fingerprint showing through.

### 6.3 Why it's the hardest *engineering* artifact, not just the hardest concept

Its defects are **Heisenbugs**: they manifest only under exact interleavings of network delay, crash timing, and election races — which is why production Raft/Paxos implementations (etcd, ZooKeeper, CockroachDB) have historically shipped correctness bugs that survived years of testing and were only found via exhaustive formal model checking (TLA+), not via unit/integration tests. Testing distributed consensus by running it is like testing a cryptographic cipher by looking at ciphertext — the space of "bad" interleavings is astronomically larger than what any test suite samples.

---

## 7. Replication, Data, and Modern AI — Expanded

- **Vector databases** (Pinecone, Milvus, Weaviate, Qdrant) replicate ANN indexes (HNSW/IVF-PQ) across nodes. Unlike row-store replication, index replication has an added wrinkle: the index structure itself (graph edges in HNSW) is expensive to rebuild, so replicas often ship the *serialized index snapshot* rather than replaying individual insert operations.
- **Feature stores** replicate feature data under *bounded staleness* SLAs (e.g., "features no more than 60s stale") — a middle ground between strict and eventual consistency invented specifically because ML inference degrades gracefully with staleness but fails hard on unavailability.
- **Distributed data-parallel training** replicates model parameters across GPU/TPU workers; gradient synchronization (all-reduce) functions like a **write quorum over the model state** every training step — the entire field of "communication-efficient distributed training" (gradient compression, local SGD, federated averaging) is really replication-consistency engineering wearing an ML hat.
- **LLM inference fleets** replicate model weights across stateless inference replicas behind a load balancer. Because replicas are read-only after weight-load, this collapses to the simplest corner of the whole design space: leaderless, no-conflict, replication-factor-for-availability-only — the interesting engineering problem shifts entirely to *cold-start latency* (loading tens of GB of weights) rather than to consistency.
- **RAG (retrieval-augmented generation) pipelines** expose a distinctive cross-system consistency bug: the vector index (usually eventually consistent) and the canonical document store (often strongly consistent) can drift apart — a document gets updated/deleted in the source of truth, but the stale embedding is still retrievable and gets fed to the LLM, producing an answer that cites content that no longer exists. This is a *replication-lag-induced hallucination*, not a model problem.
- **Prompt/response caches** in LLM API gateways are, structurally, leaderless replicas with LWW eviction — same underlying theory, different vocabulary ("cache invalidation" is "conflict resolution" in a trench coat).
- **Online feature/embedding stores for recommendation systems** frequently use CRDT-style counters (impressions, click counts) precisely because they need multi-region, coordination-free increments that must converge without a central counter service becoming the bottleneck.

---

## 8. 17 Design Patterns Related to Replication

1. **Leader-Follower (Primary-Replica) Replication**
2. **Multi-Leader Replication**
3. **Leaderless Replication (Dynamo-style)**
4. **Synchronous Replication**
5. **Asynchronous Replication**
6. **Semi-Synchronous Replication**
7. **Chain Replication**
8. **State Machine Replication (Raft / Multi-Paxos)**
9. **Quorum-Based Replication**
10. **Write-Ahead Log (WAL) Shipping**
11. **Change Data Capture (CDC) Replication**
12. **Sharded Replication (Replica Sets per Shard)**
13. **Active-Active Replication**
14. **Active-Passive (Failover) Replication**
15. **Gossip / Epidemic Propagation**
16. **CRDT-Based Replication**
17. **Anti-Entropy Repair (Merkle Tree Sync)**

---

## 9. Relationship Between the Patterns (Full Tree)

```log
└── Replication
    ├── Axis 1: Who writes?
    │   ├── Leader-Follower (1)
    │   │   └── formalized-by → State Machine Replication (8)
    │   ├── Multi-Leader (2)
    │   │   └── requires → Conflict Resolution { LWW, Vector Clock, CRDT (16) }
    │   └── Leaderless (3)
    │       ├── tuned-by → Quorum (9)
    │       └── repaired-by → Anti-Entropy (17)
    ├── Axis 2: When acknowledged?
    │   ├── Synchronous (4)
    │   ├── Asynchronous (5)
    │   ├── Semi-Synchronous (6)
    │   └── applies-on-top-of → { 1, 2, 3 }
    ├── Axis 3: How propagated?
    │   ├── WAL Shipping (10)
    │   │   └── generalized-by → CDC (11)
    │   ├── State Machine Replication (8)
    │   │   └── implemented-via → Raft/Paxos consensus
    │   ├── Chain Replication (7)
    │   │   └── specialization-of → Leader-Follower (1) with ordered relay
    │   └── Gossip (15)
    │       └── used-by → Active-Active (13), Leaderless (3)
    ├── Axis 4: How merged?
    │   ├── LWW
    │   ├── Vector Clocks
    │   ├── CRDTs (16)
    │   │   └── enables → Active-Active (13) without coordination
    │   └── Application Merge
    ├── Orthogonal composition
    │   ├── Sharded Replication (12) = Partitioning ⊕ { 1 | 2 | 3 }
    │   └── Active-Passive (14) = degenerate case of Leader-Follower (1) with cold/warm standby only
    └── Background layer (applies under almost everything)
        └── Anti-Entropy (17) — Merkle-tree diff and repair, backstops 3, 13, 15
```

---

## 10. Per-Pattern Pseudocode (Python-style, no comments, separated by topic)

### 10.1 Leader-Follower Replication

```python
def leader_write(leader_state, key, value, followers):
    entry = LogEntry(index=len(leader_state.log), term=leader_state.term, key=key, value=value)
    leader_state.log.append(entry)
    for follower in followers:
        follower.replicate_queue.append(entry)
    leader_state.commit_index = entry.index
    return entry.index


def follower_apply(follower_state):
    while follower_state.replicate_queue:
        entry = follower_state.replicate_queue.pop(0)
        follower_state.store[entry.key] = entry.value
        follower_state.applied_index = entry.index


def follower_read(follower_state, key, min_index=None):
    if min_index is not None and follower_state.applied_index < min_index:
        raise ReadNotReady(follower_state.applied_index, min_index)
    return follower_state.store.get(key)
```

### 10.2 Multi-Leader Replication

```python
def multi_leader_write(local_leader, key, value, peer_leaders):
    version = HybridClock.tick(local_leader.node_id)
    local_leader.store[key] = VersionedValue(value, version)
    for peer in peer_leaders:
        peer.receive_remote_write(key, value, version)
    return version


def receive_remote_write(local_leader, key, value, remote_version):
    existing = local_leader.store.get(key)
    if existing is None:
        local_leader.store[key] = VersionedValue(value, remote_version)
        return
    resolution = resolve_multi_leader_conflict(existing, VersionedValue(value, remote_version))
    local_leader.store[key] = resolution
```

### 10.3 Leaderless Replication (Dynamo-style)

```python
def leaderless_write(nodes_for_key, key, value, w):
    version = HybridClock.tick(coordinator_id())
    acks = 0
    for node in nodes_for_key:
        try:
            node.put(key, value, version)
            acks += 1
        except NodeUnavailable:
            continue
        if acks >= w:
            return version
    raise QuorumNotReached(acks, w)


def leaderless_read(nodes_for_key, key, r):
    responses = []
    for node in nodes_for_key:
        try:
            responses.append(node.get(key))
        except NodeUnavailable:
            continue
        if len(responses) >= r:
            break
    if len(responses) < r:
        raise QuorumNotReached(len(responses), r)
    return pick_latest(responses)
```

### 10.4 Synchronous / Asynchronous / Semi-Synchronous Ack

```python
def sync_ack_write(leader, entry, followers):
    confirmed = 0
    for follower in followers:
        if follower.send_and_confirm(entry):
            confirmed += 1
    if confirmed == len(followers):
        return True
    raise ReplicationFailure(confirmed, len(followers))


def async_ack_write(leader, entry, followers):
    for follower in followers:
        follower.enqueue(entry)
    return True


def semi_sync_ack_write(leader, entry, followers, k):
    confirmed = 0
    for follower in followers:
        if follower.send_and_confirm(entry, timeout=leader.timeout):
            confirmed += 1
            if confirmed >= k:
                for remaining in followers:
                    remaining.enqueue(entry)
                return True
    raise ReplicationFailure(confirmed, k)
```

### 10.5 Chain Replication

```python
def chain_write(chain_head, key, value):
    node = chain_head
    version = None
    while node is not None:
        version = node.apply(key, value, version)
        node = node.next
    return version


def chain_read(chain_tail, key):
    return chain_tail.get(key)


def chain_node_apply(node_state, key, value, incoming_version):
    version = incoming_version if incoming_version is not None else HybridClock.tick(node_state.node_id)
    node_state.store[key] = VersionedValue(value, version)
    return version
```

### 10.6 State Machine Replication (Raft core)

```python
def raft_append_entries(term, leader_id, prev_index, prev_term, entries, leader_commit, log_state):
    if term < log_state.current_term:
        return AppendResult(False, log_state.current_term)
    if prev_index >= 0:
        if len(log_state.entries) <= prev_index or log_state.entries[prev_index].term != prev_term:
            return AppendResult(False, log_state.current_term)
    base = prev_index + 1
    for offset, entry in enumerate(entries):
        idx = base + offset
        if idx < len(log_state.entries) and log_state.entries[idx].term != entry.term:
            log_state.entries = log_state.entries[:idx]
        if idx >= len(log_state.entries):
            log_state.entries.append(entry)
    if leader_commit > log_state.commit_index:
        log_state.commit_index = min(leader_commit, len(log_state.entries) - 1)
    log_state.current_term = term
    return AppendResult(True, log_state.current_term)


def raft_request_vote(term, candidate_id, last_log_index, last_log_term, voter_state):
    if term < voter_state.current_term:
        return VoteResult(False, voter_state.current_term)
    log_ok = (last_log_term > voter_state.last_log_term or
              (last_log_term == voter_state.last_log_term and last_log_index >= voter_state.last_log_index))
    already_voted = voter_state.voted_for not in (None, candidate_id)
    if log_ok and not already_voted:
        voter_state.voted_for = candidate_id
        voter_state.current_term = term
        return VoteResult(True, voter_state.current_term)
    return VoteResult(False, voter_state.current_term)


def raft_start_election(node_state, peers):
    node_state.current_term += 1
    node_state.voted_for = node_state.node_id
    votes = 1
    for peer in peers:
        result = peer.request_vote(node_state.current_term, node_state.node_id,
                                     node_state.last_log_index, node_state.last_log_term)
        if result.granted:
            votes += 1
    if votes > (len(peers) + 1) // 2:
        node_state.role = "leader"
        return True
    node_state.role = "follower"
    return False
```

### 10.7 Quorum Configuration Layer

```python
def quorum_config(n, mode):
    if mode == "strict":
        w = n // 2 + 1
        r = n - w + 1
        return w, r
    if mode == "sloppy_write_light":
        return 1, n
    if mode == "sloppy_read_light":
        return n, 1
    raise UnknownQuorumMode(mode)


def validate_quorum_overlap(w, r, n):
    return (w + r) > n
```

### 10.8 Write-Ahead Log (WAL) Shipping

```python
def wal_append(wal_state, key, value):
    entry = WalEntry(offset=wal_state.next_offset, key=key, value=value)
    wal_state.segments.append(entry)
    wal_state.next_offset += 1
    return entry.offset


def wal_ship(wal_state, replica_offset_store, replica):
    last_shipped = replica_offset_store.get(replica.id, 0)
    for entry in wal_state.segments[last_shipped:]:
        replica.apply(entry)
        replica_offset_store[replica.id] = entry.offset + 1
```

### 10.9 Change Data Capture (CDC)

```python
def cdc_tail_and_publish(wal_reader, broker, checkpoint_store):
    last_offset = checkpoint_store.get_offset()
    for change_event in wal_reader.stream_from(last_offset):
        broker.publish(topic=change_event.table, event=change_event)
        checkpoint_store.set_offset(change_event.offset)


def cdc_sink_apply(consumer, sink_writer, sink_checkpoint_store):
    last_offset = sink_checkpoint_store.get_offset()
    for change_event in consumer.poll_from(last_offset):
        sink_writer.apply(change_event)
        sink_checkpoint_store.set_offset(change_event.offset)
```

### 10.10 Sharded Replication

```python
def route_to_shard(shard_map, key):
    shard_id = consistent_hash(key) % len(shard_map)
    return shard_map[shard_id]


def sharded_write(shard_map, key, value, ack_mode):
    shard = route_to_shard(shard_map, key)
    if ack_mode == "sync":
        return sync_ack_write(shard.leader, LogEntry(len(shard.leader.log), shard.leader.term, key, value), shard.followers)
    return async_ack_write(shard.leader, LogEntry(len(shard.leader.log), shard.leader.term, key, value), shard.followers)


def sharded_read(shard_map, key):
    shard = route_to_shard(shard_map, key)
    return follower_read(shard.preferred_replica, key)
```

### 10.11 Active-Active Replication

```python
def active_active_write(local_site, key, value, remote_sites):
    version = HybridClock.tick(local_site.site_id)
    local_site.store[key] = VersionedValue(value, version)
    for site in remote_sites:
        site.gossip_inbox.append((key, value, version))
    return version


def active_active_absorb(local_site):
    while local_site.gossip_inbox:
        key, value, version = local_site.gossip_inbox.pop(0)
        existing = local_site.store.get(key)
        if existing is None or version > existing.version:
            local_site.store[key] = VersionedValue(value, version)
```

### 10.12 Active-Passive (Failover) Replication

```python
def active_passive_write(active_node, standby_node, key, value):
    active_node.store[key] = value
    standby_node.enqueue(key, value)
    return True


def promote_standby(standby_node, fencing_epoch):
    if fencing_epoch <= standby_node.last_known_epoch:
        raise StalePromotion(fencing_epoch, standby_node.last_known_epoch)
    standby_node.last_known_epoch = fencing_epoch
    standby_node.role = "active"
    return standby_node
```

### 10.13 Gossip / Epidemic Propagation

```python
def gossip_round(local_node, all_peers, fanout):
    targets = random_sample(all_peers, fanout)
    for peer in targets:
        peer.merge_digest(local_node.state_digest())


def merge_digest(local_state, incoming_digest):
    for key, incoming_entry in incoming_digest.items():
        current = local_state.get(key)
        if current is None or incoming_entry.version > current.version:
            local_state[key] = incoming_entry
```

### 10.14 CRDT-Based Replication

```python
def gcounter_increment(counter_state, node_id, amount):
    counter_state[node_id] = counter_state.get(node_id, 0) + amount
    return counter_state


def gcounter_merge(local_counter, remote_counter):
    merged = dict(local_counter)
    for node_id, value in remote_counter.items():
        merged[node_id] = max(merged.get(node_id, 0), value)
    return merged


def gcounter_value(counter_state):
    return sum(counter_state.values())


def orset_add(orset_state, element, tag):
    orset_state.adds.add((element, tag))
    return orset_state


def orset_remove(orset_state, element):
    tags_to_remove = {t for (e, t) in orset_state.adds if e == element}
    orset_state.removes |= {(element, t) for t in tags_to_remove}
    return orset_state


def orset_merge(local_orset, remote_orset):
    return ORSet(adds=local_orset.adds | remote_orset.adds, removes=local_orset.removes | remote_orset.removes)


def orset_elements(orset_state):
    return {element for (element, tag) in orset_state.adds if (element, tag) not in orset_state.removes}
```

### 10.15 Anti-Entropy Repair (Merkle Tree Sync)

```python
def merkle_diff(node_a, node_b):
    if node_a.hash == node_b.hash:
        return []
    if node_a.is_leaf and node_b.is_leaf:
        return [node_a.key]
    diffs = []
    for child_a, child_b in zip(node_a.children, node_b.children):
        diffs.extend(merkle_diff(child_a, child_b))
    return diffs


def anti_entropy_sync(tree_a, tree_b, store_a, store_b):
    if tree_a.root.hash == tree_b.root.hash:
        return []
    keys = merkle_diff(tree_a.root, tree_b.root)
    repaired = []
    for key in keys:
        value_a = store_a.get(key)
        value_b = store_b.get(key)
        winner = pick_latest([value_a, value_b])
        if winner != value_a:
            store_a.put(key, winner.value, winner.version)
        if winner != value_b:
            store_b.put(key, winner.value, winner.version)
        repaired.append(key)
    return repaired
```

### 10.16 Fencing (cross-cutting, used by 1, 8, 14)

```python
def fenced_write(storage, key, value, fencing_epoch):
    if fencing_epoch <= storage.get_current_epoch():
        raise StaleWriteRejected(fencing_epoch, storage.get_current_epoch())
    storage.set_current_epoch(fencing_epoch)
    storage.put(key, value)
    return True
```

### 10.17 Shared Helper Functions (used across the pseudocode above)

```python
def pick_latest(versioned_values):
    valid = [v for v in versioned_values if v is not None]
    if not valid:
        return None
    return max(valid, key=lambda v: v.version)


def resolve_multi_leader_conflict(existing, incoming):
    if incoming.version > existing.version:
        return incoming
    if incoming.version < existing.version:
        return existing
    return incoming if incoming.value > existing.value else existing


class HybridClock:
    counters = {}

    @staticmethod
    def tick(node_id):
        HybridClock.counters[node_id] = HybridClock.counters.get(node_id, 0) + 1
        return (current_wall_time_ms(), HybridClock.counters[node_id], node_id)
```

---

## 11. Flow of Execution (End-to-End List)

1. Client issues write → routed to leader (10.1) / any coordinator (10.3) / nearest site (10.11)
2. Write appended to local WAL first (10.8), before touching in-memory state
3. Ack policy decides when the client is told "done" (10.4)
4. Entry propagated via log stream (10.8), CDC (10.9), gossip (10.13), or chain relay (10.5)
5. If strong consistency required, entries pass through Raft `AppendEntries` (10.6) with term/index safety checks
6. Replicas apply entries in strict log order, deterministically updating local state
7. Concurrent writes across leaders/leaderless nodes resolved via LWW / vector clocks / CRDTs (10.14) / app-merge
8. Background anti-entropy (10.15) continuously diffs replicas and repairs silent divergence
9. Client issues read → routed via quorum config (10.7), preferred replica, or nearest site
10. Multiple versions returned → `pick_latest` (10.17) selects canonical value
11. On leader failure: election (10.6) + fencing (10.16) prevent a zombie leader from re-applying stale writes
12. Sharded systems (10.10) run this entire pipeline independently and in parallel, per shard

---

## 12. References

- Lamport, L. — *Time, Clocks, and the Ordering of Events in a Distributed System*, CACM, 1978
- Lamport, L. — *The Part-Time Parliament* (Paxos), ACM TOCS, 1998
- Ongaro, D. & Ousterhout, J. — *In Search of an Understandable Consensus Algorithm* (Raft), USENIX ATC, 2014
- DeCandia, G. et al. — *Dynamo: Amazon's Highly Available Key-value Store*, SOSP, 2007
- Corbett, J. et al. — *Spanner: Google's Globally-Distributed Database*, OSDI, 2012
- Kleppmann, M. — *Designing Data-Intensive Applications*, O'Reilly, 2017 (Ch. 5, 9)
- Shapiro, M. et al. — *Conflict-Free Replicated Data Types*, INRIA Technical Report, 2011
- Fischer, M., Lynch, N., Paterson, M. — *Impossibility of Distributed Consensus with One Faulty Process* (FLP), JACM, 1985
- Brewer, E. — *CAP Twelve Years Later: How the "Rules" Have Changed*, IEEE Computer, 2012
- Abadi, D. — *Consistency Tradeoffs in Modern Distributed Database System Design* (PACELC), IEEE Computer, 2012
- van Renesse, R. & Schneider, F. — *Chain Replication for Supporting High Throughput and Availability*, OSDI, 2004
- Kulkarni, S. et al. — *Logical Physical Clocks* (Hybrid Logical Clocks), OPODIS, 2014

---

*Replication is not a checklist of database features — it is a small set of physically forced tradeoffs (CAP/PACELC), instantiated across five design axes (who writes, when acknowledged, how propagated, how merged, how it fails/recovers). Every pattern above is a named point in that five-dimensional space, not a competing technology.*