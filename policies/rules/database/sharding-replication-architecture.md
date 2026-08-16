# Database Architecture & Distributed Data Systems Reference
*(Senior / Architect-Level Reference for OLTP, OLAP, Sharding, Replication, and Storage Engines)*

---

## Tier 1 — Non-Negotiable Fundamentals

### 1. ACID & Transaction Isolation Levels
- **Atomicity**: Transactions commit completely or roll back entirely using WAL undo records.
- **Consistency**: Invariants and constraints (foreign keys, check constraints, unique indexes) hold before and after execution.
- **Isolation Levels & Read Anomalies**:

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Serialization Anomaly |
|---|---|---|---|---|
| **Read Uncommitted** | Possible | Possible | Possible | Possible |
| **Read Committed** (Default PG) | Prevented | Possible | Possible | Possible |
| **Repeatable Read** | Prevented | Prevented | Prevented | Possible |
| **Serializable** (SSI) | Prevented | Prevented | Prevented | Prevented |

- **MVCC (Multi-Version Concurrency Control)**:
  - Readers do not block writers; writers do not block readers.
  - Each tuple tracks transaction visibility via `xmin` (creating transaction ID) and `xmax` (deleting/updating transaction ID).
  - Periodic vacuuming/compaction reclaims dead tuple storage space.

### 2. Locks & Deadlock Prevention
- **Lock Hierarchy**: Row-level locks (`SELECT FOR UPDATE`, `FOR SHARE`), Table-level locks (`ACCESS EXCLUSIVE` for schema changes).
- **Advisory Locks**: Application-level distributed locks tied to database sessions (`pg_advisory_lock(key)`).
- **Deadlock Handling**: Always acquire locks in a deterministic global order (e.g., sorted primary key IDs). Configure `deadlock_timeout` to abort stuck transactions.

### 3. Indexing & Query Execution Plans
- **B-Tree**: Default for equality (`=`) and range queries (`<`, `>`, `BETWEEN`).
- **GIN (Generalized Inverted Index)**: Optimized for array values, JSONB document fields, and full-text search.
- **BRIN (Block Range Index)**: Ultra-compact index for naturally sorted append-only time-series data.
- **Scan Types**:
  - `Index Scan`: Reads index then fetches matching heap pages.
  - `Bitmap Index Scan`: Constructs in-memory bitmap of pages to minimize random I/O.
  - `Sequential Scan`: Scans entire table when table is small or returning > 15-20% of rows.
- **Join Strategies**:
  - `Nested Loop Join`: Best when driving set is small and inner relation is indexed.
  - `Hash Join`: Best for joining large unindexed relations by building in-memory hash table.
  - `Merge Join`: Best when both inputs are pre-sorted on join keys.

### 4. Replication & High Availability
- **Synchronous Replication**: Zero data loss (`RPO = 0`), higher write latency (waits for standby ACK).
- **Asynchronous Replication**: Low write latency, potential replication lag and data loss during failover.
- **Semi-Synchronous Replication**: Waits for at least one secondary node to write transaction to WAL before committing.
- **Replication Lag Mitigation**: Route critical read-after-write operations to Primary node; route stale-tolerant reads to Secondary replicas.

### 5. Partitioning & Sharding
- **Table Partitioning (Single DB Instance)**:
  - `Range Partitioning`: Partitioning by time intervals (`orders_2026_08`).
  - `Hash Partitioning`: Distributing rows across N partitions via hash function (`hash(user_id) % N`).
- **Horizontal Sharding (Multi-Node)**:
  - Shard Key Selection: Must distribute reads/writes evenly avoiding hot shards while enabling single-shard query routing.

### 6. CAP & PACELC Theorem
- **CAP Theorem**: In the presence of a Network Partition (**P**), a system must choose between Availability (**A**) or Consistency (**C**).
- **PACELC Theorem**:
  - **P/A** or **P/C**: If **P**artitioned, choose **A**vailability vs **C**onsistency.
  - **E/L** or **E/C**: **E**lse (normal execution), choose **L**atency vs **C**onsistency.

### 7. Connection Pooling & Caching Architecture
- **Connection Pooling**: Use transaction-level proxy pooling (e.g., PgBouncer).
  - Pool Sizing Formula: `max_connections = (CPU_cores * 2) + effective_spindle_count`
- **Caching Patterns**:
  - `Cache-Aside`: Application reads cache; on miss, reads DB and updates cache with TTL.
  - `Cache Stampede Prevention`: Probabilistic early expiration (XFetch algorithm) or single-flight mutex locking.
  - See [caching.md](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/caching.md) for caching mechanics and [data-normalization.md](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/data-normalization.md) for normalization standards.

### 8. Backup, Disaster Recovery & OLTP vs OLAP
- **RPO (Recovery Point Objective)**: Maximum acceptable data loss duration.
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime duration during disaster recovery.
- **OLTP vs OLAP Architecture**:
  - **OLTP (PostgreSQL)**: Low-latency row-oriented CRUD transactions.
  - **OLAP (ClickHouse)**: High-throughput columnar analytics engine with sparse primary block indexes.

---

## Tier 2 — Distributed Systems Depth

### 1. Quorum Consensus & Vector Clocks
- **Quorum Equation**: `R + W > N` (where `N` = replica count, `W` = write quorum, `R` = read quorum).
- **Strict Quorum**: Guarantees read includes at least one node with the latest committed write.
- **Sloppy Quorum & Hinted Handoff**: Temporary writes stored on healthy neighbors during node outages.

### 2. Consensus Algorithms (Raft)
- **Node States**: Leader, Follower, Candidate.
- **Leader Election**: Heartbeat timeouts trigger term increments and candidate votes.
- **Log Matching & Commit**: Leader appends entries to its log and replicates to a majority before applying to state machine.

### 3. Distributed Transactions & Saga Pattern
- **Two-Phase Commit (2PC)**:
  - Phase 1: Coordinator sends `PREPARE` to all participants.
  - Phase 2: If all vote `YES`, Coordinator sends `COMMIT`; otherwise `ABORT`.
  - *Drawback*: Blocking protocol if Coordinator fails during prepare phase.
- **Saga Pattern (Microservices)**:
  - Sequence of local transactions coordinated via events (Choreography) or a central orchestrator (Orchestration).
  - Every step defines a corresponding **Compensating Transaction** to roll back changes on downstream failure.

### 4. Consistent Hashing & Ring Topology
- **Hash Ring**: Hashes keys and physical nodes onto a `[0, 2^32 - 1]` ring space.
- **Virtual Nodes (Vnodes)**: Maps each physical server to multiple virtual points on the ring to ensure uniform distribution and balanced rebalancing on node additions/removals.

### 5. Change Data Capture (CDC)
- **WAL Streaming (Debezium)**: Captures row-level database modifications directly from PostgreSQL Logical Replication WAL streams and streams them into Kafka/Redpanda without application dual-write overhead.

---

## Tier 3 — Storage Engine Depth

### 1. Write-Ahead Logging (WAL) & Buffer Pool
- **WAL First Rule**: Database changes must be written to disk-backed WAL before dirty memory pages are written to heap files.
- **Buffer Pool**: Memory buffer caching database disk pages. Uses Clock Sweep / LRU eviction algorithms.

### 2. LSM Trees (Log-Structured Merge-tree) vs B-Trees
- **LSM Tree (Write-Optimized)**:
  - Writes land in in-memory **MemTable** and append-only WAL.
  - Flushed to immutable **SSTables (Sorted String Tables)** on disk.
  - Reads use **Bloom Filters** to quickly bypass SSTables not containing the target key.
- **Compaction**:
  - *Size-Tiered Compaction*: Merges SSTables of similar size (lower write amplification).
  - *Leveled Compaction*: Organizes SSTables into fixed-size levels L0, L1, L2 (lower read/space amplification).

### 3. Columnar Storage Engine (ClickHouse)
- **Block Storage**: Data stored in columns rather than rows for high compression ratios (LZ4 / ZSTD).
- **Granules**: Primary index stores 1 mark entry every 8,192 rows (Sparse Index), reducing memory usage while scanning large telemetry datasets.
