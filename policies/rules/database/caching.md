# Caching Architecture & Mechanics Policy Reference
*(Senior / Architect-Level Reference for Caching Mechanics, Key Hierarchies, Eviction, Invalidation, and Stampede Mitigation)*

---

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
