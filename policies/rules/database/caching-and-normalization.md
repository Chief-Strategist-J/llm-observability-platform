# Caching Strategies & Data Normalization Policy Reference
*(Senior / Architect-Level Reference for Caching Mechanics, Invalidation, and Normalization/Denormalization Patterns)*

---

## Part A — Caching Architecture & Mechanics

### 1. Mandatory Caching Patterns

| Caching Pattern | Operation Flow | Best Used For | Consistency Level |
|---|---|---|---|
| **Cache-Aside** *(Lazy Loading)* | Read Cache ➔ Miss ➔ Read DB ➔ Populate Cache | Read-heavy workloads, query caching | Eventual (bounded by TTL) |
| **Write-Through** | Write Cache & DB in single transaction | Strict read-after-write consistency requirement | Strong (Immediate) |
| **Write-Behind** *(Write-Back)* | Write Cache immediately ➔ Async queue flushes DB | High-throughput write buffering (telemetry counters) | Eventual (risk of data loss on crash) |
| **Read-Through** | Cache facade fetches DB transparently | Simplifying application logic | Dependent on cache layer config |

---

### 2. Cache Key Naming Convention

All cache keys must follow a strict, namespaced, versioned key hierarchy:

```
{namespace}:{tenant_id}:{entity}:{entity_id}:{schema_version}
```

**Examples**:
- `obs:org_0123:user:usr_9981:v1`
- `obs:org_0123:dashboard:dash_4410:v2`

**Key Rules**:
- Never use un-namespaced key names (e.g. `user_123` is forbidden).
- Always include `tenant_id` (`org_id`) to ensure strict multi-tenant isolation.
- Always include `schema_version` to prevent deserialization errors during zero-downtime application deployments.

---

### 3. Cache Stampede & Thundering Herd Mitigation

When a high-traffic cache key expires, thousands of concurrent requests can hit the database simultaneously (Cache Stampede). Every service MUST implement one of the following two mitigations:

#### A. Single-Flight / Mutex Locking (Default)
When a cache miss occurs, only **one** request acquires a distributed lock (`lock:{key}`) to query the database and populate the cache. Concurrent incoming requests wait on the lock or receive a stale fallback payload.

#### B. Probabilistic Early Expiration (XFetch Algorithm)
Recompute and refresh the cache key **before** its actual hard TTL expires based on read frequency:

$$\Delta t = - \beta \cdot \delta \cdot \ln(\text{random}())$$

If $\text{currentTime} - \Delta t > \text{expirationTime}$, trigger background async recomputation while immediately returning the cached payload to the caller.

---

### 4. Cache Invalidation & Event-Driven Sync

1. **TTL Bound**: Every cache entry MUST have an explicit Time-To-Live (TTL). Permanent keys without TTL are forbidden.
2. **Event-Driven Invalidation**: Domain mutation events (`user.updated`, `dashboard.deleted`) MUST publish an invalidation payload to Redis Pub/Sub or queue consumers to purge affected cache keys immediately.
3. **Multi-Level Caching (L1/L2)**:
   - **L1 Cache**: In-Memory process cache (fastest, microsecond access, short TTL: 1-5 seconds).
   - **L2 Cache**: Distributed Redis cluster (millisecond access, longer TTL: 5-60 minutes).
   - L1 cache invalidation MUST be broadcast to all application nodes via Redis Pub/Sub.

---

## Part B — Data Normalization & Denormalization Rules

### 1. Relational Normalization Standards (1NF to 3NF/BCNF)

All relational OLTP databases (PostgreSQL) MUST adhere to **3rd Normal Form (3NF)** by default during initial schema design.

```
┌─────────────────────────────────────────────────────────────┐
│ 1NF: Atomic values, no array lists in relational columns    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2NF: No partial dependencies (all attributes depend on PK)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3NF: No transitive dependencies (attribute -> attribute)    │
└─────────────────────────────────────────────────────────────┘
```

- **1NF (First Normal Form)**: Every column contains atomic (indivisible) values. Repeating groups or comma-separated strings inside a single text field are strictly prohibited.
- **2NF (Second Normal Form)**: Table is in 1NF and all non-key attributes are fully dependent on the entire primary key (no partial key dependencies).
- **3NF (Third Normal Form)**: Table is in 2NF and no non-key attribute depends on another non-key attribute (no transitive dependencies).

---

### 2. Pragmatic Denormalization Thresholds & Guidelines

Denormalization introduces data redundancy and risk of update anomalies. Denormalization is permitted ONLY when empirical benchmark data proves a performance necessity.

#### Approved Denormalization Criteria
1. **High-Read Join Bottlenecks**: Queries joining 4+ normalized tables where query execution time exceeds SLA threshold ($p95 > 100\text{ms}$) under production traffic load.
2. **Pre-Aggregated Summary Counters**: Storing aggregate metrics (`order_count`, `total_spend_cents`) on parent records to eliminate expensive runtime `COUNT(*)` or `SUM()` scans across millions of child rows.
3. **Historical Point-in-Time Snapshots**: Copying address, pricing, or tax rates into an invoice/order record at the time of creation (so subsequent updates to the customer's profile do not alter historical financial records).

---

### 3. Denormalization Governance & Data Integrity Controls

When denormalization is applied, the following 3 architectural controls are MANDATORY:

```
┌─────────────────────────┐          Sync / CDC Worker          ┌─────────────────────────┐
│ Primary Normalized SSOT ├────────────────────────────────────►│ Denormalized Read View  │
│ (Single Source of Truth)│                                     │ (Pre-aggregated Table)  │
└────────────┬────────────┘                                     └────────────▲────────────┘
             │                                                               │
             └────────────────── Scheduled Reconciler Job ──────────────────┘
```

1. **Single Source of Truth (SSOT)**:
   - Normalized tables remain the canonical Single Source of Truth.
   - Denormalized tables or columns are treated as **read projections** derived from the SSOT.
2. **Atomic Synchronization Mechanism**:
   - Updates to denormalized projections MUST occur atomically using **Database Triggers**, **Transactional Outbox Pattern**, or **Change Data Capture (CDC via Debezium)**.
3. **Data Drift Reconciler**:
   - A scheduled background reconciliation job MUST run periodically (e.g. nightly) to compare normalized source data with denormalized projections, log any diffs, and automatically repair data drift.
