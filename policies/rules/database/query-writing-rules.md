# Master Database Query Writing & Optimization Policy

---

## 1. Executive Summary & Core Architectural Directives

This policy establishes the **non-negotiable database query writing, execution, and optimization standards** for the LLM Observability Platform. Unoptimized database queries represent the primary source of server CPU spikes, locking cascades, memory exhaustion, transaction log bloat, and distributed system deadlocks.

Every SQL query submitted to the platform (whether written directly, generated via ORM/Query Builder, or executed inside database migrations) **MUST** strictly adhere to the rules outlined herein. Every rule is backed by empirical performance benchmarks, query execution plans, and reference implementations documented across all nine files in `policies/rules/database/queries/` (`performance-queries-0.md` through `performance-queries-8.md`).

### Key Operational SLAs & Thresholds:
- **OLTP Single-Row Lookup Latency ($p99$):** $\le 2\text{ms}$
- **OLTP Multi-Row Join Latency ($p95$, $<4$ tables):** $\le 25\text{ms}$
- **OLAP / Analytical Micro-Batch Processing Latency ($p99$):** $\le 200\text{ms}$
- **Real-Time Event Stream Notification Latency ($p99$):** $\le 1\text{ms}$ (PostgreSQL `LISTEN/NOTIFY`)
- **Zero Full Table Scans:** Strictly prohibited on tables containing $>10,000$ rows in production OLTP paths.
- **Zero Unindexed Foreign Keys:** Strictly prohibited on all child tables across the entire schema.

---

## 2. Policy Master Index (40 Non-Negotiable Rules)

| Rule ID | Category | Summary / Objective | Reference File & Query Target |
|---|---|---|---|
| `RULE-QW-01` | Indexing & Sargability | Sargable WHERE predicates (Zero column function wrapping) | [performance-queries-0.md: Q3](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L45) |
| `RULE-QW-02` | Indexing & Sargability | Composite index column ordering (Equality $\rightarrow$ Range) | [performance-queries-0.md: Q5](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L75) |
| `RULE-QW-03` | Indexing & Sargability | Zero implicit type conversion on indexed columns | [performance-queries-0.md: Q4](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L59) |
| `RULE-QW-04` | Indexing & Sargability | Leading wildcard ban & Full-Text Search usage | [performance-queries-0.md: Q2](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L28) |
| `RULE-QW-05` | Indexing & Sargability | Exclusive arc partial indexes for polymorphic foreign keys | [performance-queries-1.md: Q2](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L56) |
| `RULE-QW-06` | Indexing & Sargability | `UNION ALL` refactoring for multi-column `OR` queries | [performance-queries-0.md: Q6](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L93) |
| `RULE-QW-07` | SELECT & Joins | Strict prohibition of `SELECT *` projection | [performance-queries-0.md: Q9](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L148) |
| `RULE-QW-08` | SELECT & Joins | Fan-out elimination via LATERAL joins & pre-aggregation | [performance-queries-1.md: Q4](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L144) |
| `RULE-QW-09` | SELECT & Joins | Early pushdown filtering prior to table joins | [performance-queries-0.md: Q18](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L313) |
| `RULE-QW-10` | SELECT & Joins | `LEFT JOIN` predicate placement & NULL mechanics | [performance-queries-0.md: Q20](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L350) |
| `RULE-QW-11` | SELECT & Joins | Prohibition of `DISTINCT` to mask duplicated join rows | [performance-queries-0.md: Q11](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L178) |
| `RULE-QW-12` | SELECT & Joins | `NOT EXISTS` / `EXISTS` subqueries over `NOT IN` | [performance-queries-0.md: Q13](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L223) |
| `RULE-QW-13` | Pagination & Window | Keyset / Cursor pagination mandatory over `OFFSET` | [performance-queries-0.md: Q16](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L276) |
| `RULE-QW-14` | Pagination & Window | Explicit `PARTITION BY` & ranking function semantics | [performance-queries-0.md: Q26](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L473) |
| `RULE-QW-15` | Pagination & Window | Conditional aggregations (`FILTER`) in single pass | [performance-queries-6.md: P8](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L597) |
| `RULE-QW-16` | CTEs & Traversals | CTE depth guards (`depth < 10`) on recursive graphs | [performance-queries-0.md: Q25](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L447) |
| `RULE-QW-17` | CTEs & Traversals | Closure Tables for deep hierarchy trees ($>5$ levels) | [performance-queries-1.md: Q1](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L9) |
| `RULE-QW-18` | CTEs & Traversals | Tarjan's SCC & Topological Sort graph algorithms in SQL | [performance-queries-4.md: Q6](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-4.md#L323) |
| `RULE-QW-19` | Locking & Concurrency | Out-of-transaction external API calls & logic execution | [performance-queries-0.md: Q29](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L534) |
| `RULE-QW-20` | Locking & Concurrency | Primary Key ascending lock acquisition order | [performance-queries-0.md: Q30](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L555) |
| `RULE-QW-21` | Locking & Concurrency | Non-blocking work queue via `FOR UPDATE SKIP LOCKED` | [performance-queries-2.md: Q8](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-2.md#L457) |
| `RULE-QW-22` | Locking & Concurrency | PostgreSQL Session Advisory Locks for distributed semaphores | [performance-queries-2.md: Q2](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-2.md#L64) |
| `RULE-QW-23` | Locking & Concurrency | Iterative micro-batching (`LIMIT 1000`) for deletes/updates | [performance-queries-0.md: Q33](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L608) |
| `RULE-QW-24` | Schema & Types | Exact decimal precision (`DECIMAL(15,4)`) for currency | [performance-queries-0.md: Q37](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L685) |
| `RULE-QW-25` | Schema & Types | Standardized `TIMESTAMPTZ` data types for time attributes | [performance-queries-0.md: Q34](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L627) |
| `RULE-QW-26` | Schema & Types | First Normal Form (1NF): Absolute ban on CSV columns | [performance-queries-0.md: Q42](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L779) |
| `RULE-QW-27` | Schema & Types | Mandatory `NOT NULL` constraints on foreign keys | [performance-queries-0.md: Q36](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L663) |
| `RULE-QW-28` | Partitioning & Archival | Sargable partition-pruning & sub-partitioning | [performance-queries-1.md: Q6](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L244) |
| `RULE-QW-29` | Partitioning & Archival | Partition-wise parallel joins & aggregation pushdown | [performance-queries-1.md: Q8](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L307) |
| `RULE-QW-30` | Partitioning & Archival | Metadata-only zero-downtime partition detach/attach | [performance-queries-1.md: Q10](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L378) |
| `RULE-QW-31` | Distributed Sharding | Shard key selection, co-location & hot-key salting | [performance-queries-1.md: Q11](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L411) |
| `RULE-QW-32` | Distributed Sharding | CRDT additive upserts & version vectors over 2PC | [performance-queries-1.md: Q17](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L642) |
| `RULE-QW-33` | Streaming & CDC | Incremental high-watermark refresh over full re-scans | [performance-queries-1.md: Q18](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L685) |
| `RULE-QW-34` | Streaming & CDC | Event-driven `LISTEN/NOTIFY` & WAL logical decoding | [performance-queries-1.md: Q19](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L752) |
| `RULE-QW-35` | Distributed & Replicas | Causal LSN replica routing & fencing tokens | [performance-queries-3.md: Q1](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-3.md#L9) |
| `RULE-QW-36` | Financial Ledgers | Double-entry invariant validation & transaction balance | [performance-queries-8.md: Q1](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-8.md#L11) |
| `RULE-QW-37` | JSONB Analytics | `jsonb_path_ops` GIN indexing for semi-structured data | [performance-queries-7.md: 1.2](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-7.md#L138) |
| `RULE-QW-38` | Analysis & CI Gates | Mandatory `EXPLAIN (ANALYZE, BUFFERS)` CI gates | [performance-queries-0.md: Q38](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L699) |
| `RULE-QW-39` | Analysis & CI Gates | Automated optimizer statistics freshness maintenance | [performance-queries-0.md: Q40](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L740) |
| `RULE-QW-40` | ORM Governance | Zero-tolerance ORM N+1 query loop prevention | [performance-queries-0.md: Q43](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L797) |

---

## 3. Exhaustive Category Specifications

### 3.1 Category 1: Indexing & Sargability Governance

#### RULE-QW-01: Sargable WHERE Predicates (Zero Column Function Wrapping)
- **Requirement:** Queries **MUST NOT** wrap indexed columns inside SQL scalar functions (e.g. `DATE()`, `YEAR()`, `LOWER()`, `UPPER()`, `CAST()`, `SUBSTRING()`, `COALESCE()`) within `WHERE` or `ON` clauses. Wrapping an indexed column forces a full table scan by disabling B-Tree index lookup.
- **Reference:** [performance-queries-0.md: Q3 (Function on indexed column breaks index)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L45), [performance-queries-1.md: Q6 (Range Partition Pruning Failure)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L244), [performance-queries-6.md: P10 (Efficient NULL Handling)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L695)
- **Impact:** $1000\times$ execution delay ($\sim 4,200\text{ms}$ scan vs $\sim 2\text{ms}$ index seek on 10M rows).

```sql
-- ❌ PROHIBITED: DATE() function disables index seek & partition pruning
SELECT * FROM spans 
WHERE DATE(start_time) = '2026-08-15';

-- ✅ MANDATORY: Bare column in sargable range comparison enables B-Tree index seek
SELECT * FROM spans 
WHERE start_time >= '2026-08-15 00:00:00+00' 
  AND start_time <  '2026-08-16 00:00:00+00';
```

---

#### RULE-QW-02: Composite Index Column Ordering Alignment
- **Requirement:** Queries filtering against composite indexes **MUST** supply the leading (leftmost) column of the index definition in the `WHERE` predicate. Composite indexes **MUST** be ordered following the rule: `Equality Columns` $\rightarrow$ `Range Columns` $\rightarrow$ `Covered Select Columns`.
- **Reference:** [performance-queries-0.md: Q5 (Composite index column order wrong)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L75), [performance-queries-0.md: Q7 (Over-indexing)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L108), [performance-queries-6.md: I2 (Composite Index Column Order)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L797)

```sql
-- Index Definition: CREATE INDEX idx_spans_tenant_status ON spans(tenant_id, status, created_at DESC);

-- ❌ PROHIBITED: Skipping leading column 'tenant_id' invalidates index usage
SELECT * FROM spans WHERE created_at > '2026-08-15 00:00:00+00';

-- ✅ MANDATORY: Includes leading equality column 'tenant_id' for exact B-Tree seek
SELECT * FROM spans 
WHERE tenant_id = 'tenant_123' 
  AND status = 'ERROR' 
  AND created_at > '2026-08-15 00:00:00+00';
```

---

#### RULE-QW-03: Zero Implicit Type Conversion on Indexed Columns
- **Requirement:** SQL queries **MUST** compare column values against literals of the exact matching data type. String columns (`VARCHAR`, `UUID`, `TEXT`) **MUST NOT** be compared against raw integers, as implicit type casting (`CAST(col AS INT)`) disables index seeking.
- **Reference:** [performance-queries-0.md: Q4 (Implicit type conversion disables index)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L59)

```sql
-- ❌ PROHIBITED: Comparing VARCHAR column 'phone' to INT forces implicit CAST(phone AS INT)
SELECT * FROM users WHERE phone = 9876543210;

-- ✅ MANDATORY: Exact matching string literal preserves B-Tree index seek
SELECT * FROM users WHERE phone = '9876543210';
```

---

#### RULE-QW-04: Leading Wildcard Ban & Full-Text Search Usage
- **Requirement:** Queries **MUST NOT** use leading wildcards (`LIKE '%term%'`) on standard B-Tree indexed columns. For substring, fuzzy, or free-text search, developers **MUST** use PostgreSQL `pg_trgm` GIN indexes or Full-Text Search (`tsvector` / `tsquery`).
- **Reference:** [performance-queries-0.md: Q2 (Leading Wildcard kills index)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L28), [performance-queries-7.md: 1.3 (Denormalized Search)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-7.md#L198)

```sql
-- ❌ PROHIBITED: Leading wildcard causes full table scan
SELECT * FROM trace_events WHERE attributes LIKE '%error%';

-- ✅ MANDATORY: Trigon GIN index or Full-Text Search
SELECT * FROM trace_events 
WHERE to_tsvector('english', attributes) @@ to_tsquery('english', 'error');
```

---

#### RULE-QW-05: Exclusive Arc Partial Indexes for Polymorphic Foreign Keys
- **Requirement:** Generic string-based polymorphic relationships (`commentable_type` + `commentable_id`) are **STRICTLY BANNED**. Polymorphic entity references **MUST** use Exclusive Arc Foreign Keys protected by `CHECK` constraints and partial indexes.
- **Reference:** [performance-queries-1.md: Q2 (Polymorphic Relationships Anti-Pattern)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L56), [performance-queries-7.md: 2.1 (Polymorphic Relationships - The Right Way)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-7.md#L270)
- **Impact:** $4,450\times$ execution speedup ($\sim 8,900\text{ms}$ polymorphic scan vs $\sim 2\text{ms}$ partial index seek).

```sql
-- ❌ PROHIBITED: Rails-style polymorphic string + ID (cannot foreign key or index efficiently)
CREATE TABLE comments (id BIGSERIAL PRIMARY KEY, commentable_type VARCHAR(50), commentable_id BIGINT);

-- ✅ MANDATORY: Exclusive Arc Schema with Partial Indexes
CREATE TABLE comments (
  id BIGSERIAL PRIMARY KEY,
  trace_id BIGINT REFERENCES traces(id) ON DELETE CASCADE,
  span_id  BIGINT REFERENCES spans(id)  ON DELETE CASCADE,
  alert_id BIGINT REFERENCES alerts(id) ON DELETE CASCADE,
  CONSTRAINT single_parent_check CHECK (
    (trace_id IS NOT NULL)::INT + (span_id IS NOT NULL)::INT + (alert_id IS NOT NULL)::INT = 1
  )
);

CREATE INDEX idx_comments_trace ON comments(trace_id, created_at DESC) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_comments_span  ON comments(span_id,  created_at DESC) WHERE span_id  IS NOT NULL;
CREATE INDEX idx_comments_alert ON comments(alert_id, created_at DESC) WHERE alert_id IS NOT NULL;
```

---

#### RULE-QW-06: `UNION ALL` Refactoring for Multi-Column `OR` Queries
- **Requirement:** Queries filtering multiple indexed columns using `OR` predicates (e.g. `WHERE email = x OR phone = y`) **MUST** be refactored into `UNION ALL` statements to allow independent B-Tree index scans per branch.
- **Reference:** [performance-queries-0.md: Q6 (OR condition breaks index)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L93)

```sql
-- ❌ PROHIBITED: OR condition forces optimizer to abandon indexes or perform expensive bitmap ORs
SELECT * FROM users WHERE email = 'a@b.com' OR phone = '+1234567890';

-- ✅ MANDATORY: Explicit UNION ALL enables dual index seek
SELECT * FROM users WHERE email = 'a@b.com'
UNION ALL
SELECT * FROM users WHERE phone = '+1234567890' AND email != 'a@b.com';
```

---

### 3.2 Category 2: SELECT, Aggregation & Join Optimization

#### RULE-QW-07: Strict Prohibition of `SELECT *` Projection
- **Requirement:** Queries **MUST** explicitly list required target columns. `SELECT *` is **PROHIBITED** in production code as it breaks index-only covering scans, increases network payload size, and inflates memory usage.
- **Reference:** [performance-queries-0.md: Q9 (SELECT * performance killer)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L148)

```sql
-- ❌ PROHIBITED: Fetches all columns including large JSONB payloads
SELECT * FROM spans s JOIN traces t ON s.trace_id = t.id;

-- ✅ MANDATORY: Explicit projection allows covering index scan with zero heap reads
SELECT s.id, s.name, s.duration_ms, t.service_name 
FROM spans s 
JOIN traces t ON s.trace_id = t.id;
```

---

#### RULE-QW-08: Fan-Out Elimination via LATERAL Joins & Pre-Aggregation
- **Requirement:** When joining a parent entity to multiple child tables with aggregate metrics, developers **MUST NOT** use multi-`LEFT JOIN` queries. Developers **MUST** use `CROSS JOIN LATERAL` or pre-aggregated CTEs to eliminate row multiplication (fan-out).
- **Reference:** [performance-queries-1.md: Q4 (Many-to-Many Fan-Out Problem)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L144), [performance-queries-5.md: Q10 (The Fan-Out JOIN)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-5.md#L750), [performance-queries-6.md: P3 (Aggregate-Then-Join)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L343)
- **Impact:** Prevents intermediate row explosion ($10\text{B}$ rows $\rightarrow$ $100\text{K}$ rows; $\sim 12\text{MB}$ vs $180\text{GB}$ OOM crash).

```sql
-- ❌ PROHIBITED: 3 LEFT JOINs create 1 post × 10 tags × 50 spans × 200 logs = 100,000 intermediate rows per post
SELECT p.id, COUNT(DISTINCT t.tag_id), COUNT(DISTINCT s.id)
FROM projects p
LEFT JOIN project_tags t ON t.project_id = p.id
LEFT JOIN spans s ON s.project_id = p.id
GROUP BY p.id;

-- ✅ MANDATORY: LATERAL joins aggregate each child table independently
SELECT p.id, t.tag_count, s.span_count
FROM projects p
CROSS JOIN LATERAL (
  SELECT COUNT(*) AS tag_count FROM project_tags WHERE project_id = p.id
) t
CROSS JOIN LATERAL (
  SELECT COUNT(*) AS span_count FROM spans WHERE project_id = p.id
) s
WHERE p.status = 'ACTIVE';
```

---

#### RULE-QW-09: Early Pushdown Filtering Prior to Table Joins
- **Requirement:** Queries joining massive tables **MUST** apply filtering predicates in derived tables or CTEs prior to executing the `JOIN`, minimizing hash-join memory requirements.
- **Reference:** [performance-queries-0.md: Q18 (Joining without filtering first)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L313), [performance-queries-5.md: Q1 (Filter and Aggregate Before Join)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-5.md#L59)

```sql
-- ❌ PROHIBITED: Joins 100M span_events to 50M spans before filtering status
SELECT s.id, se.event_name 
FROM spans s
JOIN span_events se ON se.span_id = s.id
WHERE s.status = 'ERROR' AND s.created_at >= NOW() - INTERVAL '1 hour';

-- ✅ MANDATORY: Derived CTE filters parent spans first, reducing join inputs by 99%
WITH filtered_spans AS (
  SELECT id FROM spans 
  WHERE status = 'ERROR' AND created_at >= NOW() - INTERVAL '1 hour'
)
SELECT fs.id, se.event_name
FROM filtered_spans fs
JOIN span_events se ON se.span_id = fs.id;
```

---

#### RULE-QW-10: `LEFT JOIN` Predicate Placement & NULL Mechanics
- **Requirement:** When filtering right-table attributes in a `LEFT JOIN`, predicates **MUST** be placed in the `ON` clause, not the `WHERE` clause. Placing right-table predicates in the `WHERE` clause silently converts the `LEFT JOIN` into an `INNER JOIN`.
- **Reference:** [performance-queries-0.md: Q20 (LEFT JOIN with WHERE filtering right table)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L350)

```sql
-- ❌ PROHIBITED: WHERE predicate filters out NULLs, converting LEFT JOIN into INNER JOIN
SELECT t.id, s.duration_ms FROM traces t LEFT JOIN spans s ON s.trace_id = t.id WHERE s.status = 'ERROR';

-- ✅ MANDATORY: Filter moved into JOIN condition preserves outer trace rows
SELECT t.id, s.duration_ms FROM traces t LEFT JOIN spans s ON s.trace_id = t.id AND s.status = 'ERROR';
```

---

#### RULE-QW-11: Prohibition of `DISTINCT` to Mask Duplicated Join Rows
- **Requirement:** Developers **MUST NOT** use `DISTINCT` to mask duplicated rows produced by flawed join conditions. If a query requires deduplication, developers **MUST** fix the join logic or explicitly group by the target primary key.
- **Reference:** [performance-queries-0.md: Q11 (DISTINCT masking a JOIN problem)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L178)

```sql
-- ❌ PROHIBITED: DISTINCT forces expensive sorting across huge intermediate sets
SELECT DISTINCT t.id, t.service_name FROM traces t JOIN spans s ON s.trace_id = t.id;

-- ✅ MANDATORY: Fix join or use EXISTS subquery
SELECT t.id, t.service_name FROM traces t
WHERE EXISTS (SELECT 1 FROM spans s WHERE s.trace_id = t.id);
```

---

#### RULE-QW-12: `NOT EXISTS` / `EXISTS` Subqueries Over `NOT IN`
- **Requirement:** Subquery membership checks **MUST** use `EXISTS` or `NOT EXISTS` instead of `IN` or `NOT IN`. If the subquery in a `NOT IN` clause evaluates to even a single `NULL`, the outer query evaluates to zero rows.
- **Reference:** [performance-queries-0.md: Q13 (NOT IN with NULLs returns nothing)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L223), [performance-queries-6.md: P9 (Existence Check)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L644)

```sql
-- ❌ PROHIBITED: If deleted_tenants returns 1 NULL, outer query returns 0 rows
SELECT * FROM spans WHERE tenant_id NOT IN (SELECT tenant_id FROM deleted_tenants);

-- ✅ MANDATORY: Semantically safe and short-circuits at first match
SELECT * FROM spans s
WHERE NOT EXISTS (SELECT 1 FROM deleted_tenants d WHERE d.tenant_id = s.tenant_id);
```

---

### 3.3 Category 3: Pagination, Window Functions & Aggregation Mechanics

#### RULE-QW-13: Keyset / Cursor Pagination Mandatory Over `OFFSET`
- **Requirement:** Pagination over datasets with $>1,000$ rows **MUST** use Keyset (Cursor-based) pagination (`WHERE (sort_col, id) < ($last_sort, $last_id)`). The `OFFSET` keyword is **PROHIBITED** on large tables as it scales at $O(N)$ by reading and discarding offset rows.
- **Reference:** [performance-queries-0.md: Q16 (Pagination with OFFSET at scale)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L276), [performance-queries-5.md: Q5 (The OFFSET Pagination Cliff)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-5.md#L323), [performance-queries-6.md: P1 (Safe Pagination)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L229)
- **Impact:** Keyset pagination maintains $O(1)$ constant latency regardless of page depth ($\sim 2\text{ms}$ vs $\sim 5,000\text{ms}$ at page 10,000).

```sql
-- ❌ PROHIBITED: OFFSET 100000 reads 100,020 rows and discards 100,000
SELECT * FROM spans ORDER BY created_at DESC LIMIT 20 OFFSET 100000;

-- ✅ MANDATORY: Keyset pagination seeks directly to B-Tree offset
SELECT id, name, duration_ms, created_at FROM spans 
WHERE (created_at, id) < ('2026-08-15 10:00:00+00', 987654)
ORDER BY created_at DESC, id DESC 
LIMIT 20;
```

---

#### RULE-QW-14: Explicit `PARTITION BY` & Ranking Semantics in Window Functions
- **Requirement:** Window functions **MUST** explicitly specify `PARTITION BY` clauses aligned with shard/tenant boundaries. Developers **MUST** select the correct ranking function based on tie-handling requirements: `RANK()` (gaps on ties), `DENSE_RANK()` (no gaps), or `ROW_NUMBER()` (arbitrary tie-breaker).
- **Reference:** [performance-queries-0.md: Q26 (ROW_NUMBER vs RANK vs DENSE_RANK)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L473), [performance-queries-0.md: Q28 (LAG/LEAD without proper partitioning)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L513), [performance-queries-6.md: P7 (Rank / Top-N Per Group)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L549)

```sql
-- ❌ PROHIBITED: Missing PARTITION BY calculates LAG across disparate tenants
SELECT span_id, tenant_id, duration_ms, LAG(duration_ms) OVER (ORDER BY created_at) FROM spans;

-- ✅ MANDATORY: Partitioned by tenant guarantees intra-tenant sequence
SELECT span_id, tenant_id, duration_ms, LAG(duration_ms) OVER (PARTITION BY tenant_id ORDER BY created_at) FROM spans;
```

---

#### RULE-QW-15: Conditional Aggregations (`FILTER`) in Single Pass
- **Requirement:** Aggregating data across multiple conditional states (e.g. active vs pending vs failed) **MUST** use SQL `FILTER (WHERE condition)` clause or `CASE WHEN` inside a single query pass. Running multiple queries or subquery joins per status is **PROHIBITED**.
- **Reference:** [performance-queries-6.md: P8 (Conditional Aggregation)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L597)

```sql
-- ✅ MANDATORY: Computes all status counts in 1 single table scan
SELECT
  tenant_id,
  COUNT(*)                                         AS total_spans,
  COUNT(*) FILTER (WHERE status = 'OK')           AS success_spans,
  COUNT(*) FILTER (WHERE status = 'ERROR')        AS error_spans,
  AVG(duration_ms) FILTER (WHERE status = 'OK')   AS avg_success_duration
FROM spans
WHERE created_at >= NOW() - INTERVAL '1 hour'
GROUP BY tenant_id;
```

---

### 3.4 Category 4: CTEs, Recursion & Graph Traversals

#### RULE-QW-16: CTE Depth Guards (`depth < 10`) on Recursive Graphs
- **Requirement:** Recursive CTEs **MUST** include an explicit depth counter guard (`WHERE depth < 10`) to prevent infinite execution loops caused by circular data references in graph relations.
- **Reference:** [performance-queries-0.md: Q25 (Recursive CTE depth limit)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L447)

```sql
-- ❌ PROHIBITED: Recursive CTE without depth limit (vulnerable to infinite loops on cyclic data)
WITH RECURSIVE org_tree AS (
  SELECT id, parent_id FROM orgs WHERE parent_id IS NULL
  UNION ALL
  SELECT o.id, o.parent_id FROM orgs o JOIN org_tree t ON o.parent_id = t.id
) SELECT * FROM org_tree;

-- ✅ MANDATORY: Depth guard prevents infinite loops on circular references
WITH RECURSIVE org_tree AS (
  SELECT id, parent_id, 1 AS depth FROM orgs WHERE parent_id IS NULL
  UNION ALL
  SELECT o.id, o.parent_id, t.depth + 1
  FROM orgs o JOIN org_tree t ON o.parent_id = t.id
  WHERE t.depth < 10 -- Mandatory Guard
) SELECT * FROM org_tree;
```

---

#### RULE-QW-17: Closure Tables for Deep Hierarchy Trees ($>5$ Levels)
- **Requirement:** For organizational, category, or trace call tree hierarchies exceeding 5 levels of depth, developers **MUST NOT** rely on recursive adjacency list queries. Hierarchies **MUST** be modeled using pre-materialized Closure Tables (`ancestor_id`, `descendant_id`, `depth`).
- **Reference:** [performance-queries-1.md: Q1 (Closure Table vs Adjacency List)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L9), [performance-queries-7.md: 2.2 (Hierarchical Data - Closure Table)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-7.md#L348)
- **Impact:** $350\times$ query speedup ($\sim 12\text{ms}$ vs $\sim 4,200\text{ms}$).

```sql
-- ✅ MANDATORY: Fetch all descendants at any depth in 1 single index seek
SELECT n.id, n.name, cc.depth
FROM category_closure cc
JOIN category_nodes n ON n.id = cc.descendant_id
WHERE cc.ancestor_id = 42 AND cc.depth > 0
ORDER BY cc.depth;
```

---

#### RULE-QW-18: Tarjan's SCC & Topological Sort Graph Algorithms in SQL
- **Requirement:** Workflow DAG dependency resolution, microservice circular dependency detection, and execution scheduling **MUST** utilize Tarjan's Strongly Connected Components (SCC) or Recursive Topological Sort queries implemented directly in database SQL rather than pulling full edge graphs into memory.
- **Reference:** [performance-queries-3.md: Q7 (Critical path dependency CPM)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-3.md#L423), [performance-queries-4.md: Q6 (Tarjan's SCC in Pure SQL)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-4.md#L323), [performance-queries-4.md: Q7 (Recursive Topological Sort)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-4.md#L416)

---

### 3.5 Category 5: Locking, Transactions & Concurrency Governance

#### RULE-QW-19: Out-of-Transaction External API Calls & Logic Execution
- **Requirement:** Transactions **MUST** be kept brief. External HTTP API calls, third-party RPCs, cryptographic hashing, and application computations **MUST NOT** occur inside an open database transaction.
- **Reference:** [performance-queries-0.md: Q29 (Long-running transactions holding locks)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L534)

```sql
-- ❌ PROHIBITED: Holding row lock while executing external HTTP API call
BEGIN;
SELECT * FROM accounts WHERE id = 42 FOR UPDATE;
-- ... app calls ExternalPaymentAPI.charge() for 5000ms ...
UPDATE accounts SET balance = balance - 100 WHERE id = 42;
COMMIT;

-- ✅ MANDATORY: Perform API call FIRST, then execute rapid atomic transaction
-- 1. App calls ExternalPaymentAPI.charge()
-- 2. Execute DB transaction:
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 42 AND balance >= 100;
COMMIT;
```

---

#### RULE-QW-20: Primary Key Ascending Lock Acquisition Order
- **Requirement:** Concurrent transactions locking multiple rows **MUST** acquire locks in a globally deterministic order (e.g. sorted by Primary Key ascending: `ORDER BY id ASC`).
- **Reference:** [performance-queries-0.md: Q30 (Deadlock from inconsistent lock order)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L555), [performance-queries-3.md: Q10 (Recursive Deadlock Graph Detector)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-3.md#L572)

```sql
-- ✅ MANDATORY: Lock rows in strictly ascending primary key order
BEGIN;
SELECT * FROM accounts WHERE id IN (5, 10) ORDER BY id ASC FOR UPDATE;
UPDATE accounts SET balance = balance - 100 WHERE id = 5;
UPDATE accounts SET balance = balance + 100 WHERE id = 10;
COMMIT;
```

---

#### RULE-QW-21: Non-Blocking Work Queue via `FOR UPDATE SKIP LOCKED`
- **Requirement:** Database-backed job/task queues **MUST** use `FOR UPDATE SKIP LOCKED` when claiming pending work. Workers **MUST NOT** perform unadorned `SELECT FOR UPDATE` queries.
- **Reference:** [performance-queries-2.md: Q8 (SKIP LOCKED as Distributed Work Queue)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-2.md#L457)

```sql
-- ❌ PROHIBITED: Workers block each other on locked rows
SELECT * FROM jobs WHERE status = 'PENDING' LIMIT 1 FOR UPDATE;

-- ✅ MANDATORY: Workers atomically claim unclaimed work without blocking
WITH claimed AS (
  SELECT id FROM jobs WHERE status = 'PENDING' ORDER BY priority DESC, created_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED
)
UPDATE jobs SET status = 'PROCESSING', worker_id = 'worker_node_1' WHERE id = (SELECT id FROM claimed) RETURNING *;
```

---

#### RULE-QW-22: PostgreSQL Session Advisory Locks for Distributed Semaphores
- **Requirement:** Application-level distributed locks (e.g. cron job execution, leader election) **MUST** use PostgreSQL Session Advisory Locks (`pg_try_advisory_lock()`). Creating temporary lock tables is **PROHIBITED**.
- **Reference:** [performance-queries-2.md: Q2 (Advisory Lock as Cross-Instance Distributed Semaphore)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-2.md#L64)

```sql
-- ✅ MANDATORY: Session advisory lock acts as an in-memory zero-I/O mutex
SELECT pg_try_advisory_lock(hashtext('daily_aggregation_job')) AS acquired;
-- Returns TRUE on exactly 1 instance; all other instances skip gracefully in <0.02ms.
```

---

#### RULE-QW-23: Iterative Micro-Batching (`LIMIT 1000`) for Deletes/Updates
- **Requirement:** Bulk data deletions or mass updates on tables exceeding $100,000$ rows **MUST** be broken down into bounded micro-batches (`LIMIT 1000` per iteration) to prevent table-level lock escalation and replication lag.
- **Reference:** [performance-queries-0.md: Q33 (Batch deletes)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L608), [performance-queries-5.md: Q8 (Bulk UPDATE WAL Management)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-5.md#L566), [performance-queries-6.md: P4 (Safe Batch DELETE)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L395)

```sql
-- ❌ PROHIBITED: Mass deletion locks 10M rows in a single transaction
DELETE FROM raw_logs WHERE created_at < '2025-01-01';

-- ✅ MANDATORY: Bounded iterative batch deletion
DELETE FROM raw_logs 
WHERE id IN (SELECT id FROM raw_logs WHERE created_at < '2025-01-01' LIMIT 1000);
```

---

### 3.6 Category 6: Data Types, Integrity & 1NF Normalization

#### RULE-QW-24: Exact Decimal Precision (`DECIMAL(15,4)`) for Currency
- **Requirement:** Floating-point data types (`FLOAT`, `DOUBLE PRECISION`, `REAL`) are **STRICTLY PROHIBITED** for monetary values, financial billing, or quota tracking. Monetary amounts **MUST** be stored as `DECIMAL(15,4)` or integer cents.
- **Reference:** [performance-queries-0.md: Q37 (DECIMAL vs FLOAT for money)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L685)

```sql
-- ❌ PROHIBITED: Binary floating point causes rounding errors (0.1 + 0.2 = 0.30000000000000004)
CREATE TABLE billing (amount FLOAT);

-- ✅ MANDATORY: Exact decimal representation
CREATE TABLE billing (amount DECIMAL(15,4) NOT NULL DEFAULT 0.0000);
```

---

#### RULE-QW-25: Standardized `TIMESTAMPTZ` Data Types for Time Attributes
- **Requirement:** Date and time values **MUST NOT** be stored as `VARCHAR` or string representations. Developers **MUST** use native temporal types (`TIMESTAMPTZ` or `DATE`) to preserve B-Tree range order.
- **Reference:** [performance-queries-0.md: Q34 (Using VARCHAR for dates)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L627)

```sql
-- ❌ PROHIBITED: String dates cause lexicographical sort errors and disable date math
CREATE TABLE events (event_time VARCHAR(30));

-- ✅ MANDATORY: Standardized TIMESTAMPTZ
CREATE TABLE events (event_time TIMESTAMPTZ NOT NULL DEFAULT NOW());
```

---

#### RULE-QW-26: First Normal Form (1NF): Absolute Ban on CSV Columns
- **Requirement:** Storing comma-separated lists of values inside a single string column is **STRICTLY PROHIBITED** (First Normal Form violation). Arrays **MUST** be stored as normalized relational mapping tables or explicit PostgreSQL `typed arrays`/`JSONB` with GIN indexes.
- **Reference:** [performance-queries-0.md: Q42 (Storing comma-separated values)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L779)

```sql
-- ❌ PROHIBITED: CSV column cannot be indexed, joined, or validated
CREATE TABLE spans (tags VARCHAR(500)); -- 'env:prod,service:auth,status:500'

-- ✅ MANDATORY: Normalized join table
CREATE TABLE span_tags (
  span_id BIGINT REFERENCES spans(id),
  tag_key VARCHAR(50) NOT NULL,
  tag_value VARCHAR(100) NOT NULL,
  PRIMARY KEY (span_id, tag_key)
);
```

---

#### RULE-QW-27: Mandatory `NOT NULL` Constraints on Foreign Keys
- **Requirement:** Foreign key columns, composite join attributes, and tenant discriminators **MUST** be declared with explicit `NOT NULL` constraints. Allowing NULLs in join columns creates tri-valued logic bugs and degrades optimizer join plans.
- **Reference:** [performance-queries-0.md: Q36 (Missing NOT NULL constraints)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L663)

```sql
-- ❌ PROHIBITED: Nullable foreign key allows orphaned rows and breaks equality checks
CREATE TABLE spans (trace_id BIGINT REFERENCES traces(id));

-- ✅ MANDATORY: Enforced non-null constraint
CREATE TABLE spans (trace_id BIGINT NOT NULL REFERENCES traces(id));
```

---

### 3.7 Category 7: Partitioning, Sharding & Archival Governance

#### RULE-QW-28: Sargable Partition-Pruning & Sub-Partitioning
- **Requirement:** Partitioned queries **MUST** supply explicit partition key bounds in the `WHERE` clause to enable static and dynamic partition pruning. High-throughput time-series tables with hot tenant activity **MUST** use sub-partitioning (`RANGE(created_at) + HASH(tenant_id)`).
- **Reference:** [performance-queries-1.md: Q6 (Range Partition Pruning Failure)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L244), [performance-queries-1.md: Q7 (Sub-Partitioning for Hot/Cold Data)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L270)
- **Impact:** Reduces I/O by $1095\times$ (scans 1 partition instead of 1095 daily partitions).

```sql
-- ❌ PROHIBITED: DATE() wrapper disables range partition pruning, scanning all 1095 daily partitions
SELECT * FROM metrics WHERE DATE(timestamp) = '2026-08-15';

-- ✅ MANDATORY: Literal range enables instant partition pruning to 1 physical segment
SELECT * FROM metrics 
WHERE timestamp >= '2026-08-15 00:00:00+00' AND timestamp < '2026-08-16 00:00:00+00';
```

---

#### RULE-QW-29: Partition-Wise Parallel Joins & Aggregation Pushdown
- **Requirement:** When joining two large partitioned tables (e.g. `traces` and `spans`), both tables **MUST** share identical partition boundaries and partition keys to enable PostgreSQL Partition-Wise Joins (`enable_partitionwise_join = ON`).
- **Reference:** [performance-queries-1.md: Q8 (Partition-wise JOIN)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L307), [performance-queries-1.md: Q12 (Distributed Aggregation Pushdown)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L447)
- **Impact:** $34\times$ latency reduction ($\sim 1,400\text{ms}$ vs $\sim 48,000\text{ms}$).

```sql
-- ✅ MANDATORY: Partition-wise join enables independent, parallel worker joins per partition pair
SET enable_partitionwise_join = ON;
SET enable_partitionwise_aggregate = ON;

SELECT t.service_name, COUNT(s.id) AS span_count
FROM traces t
JOIN spans s ON s.trace_id = t.id AND s.created_at = t.created_at
WHERE t.created_at >= '2026-08-01 00:00:00+00'
GROUP BY t.service_name;
```

---

#### RULE-QW-30: Metadata-Only Zero-Downtime Partition Detach/Attach
- **Requirement:** Purging old data from partitioned tables **MUST NOT** be executed using `DELETE`. Historical partitions **MUST** be detached concurrently (`ALTER TABLE ... DETACH PARTITION ... CONCURRENTLY`) and dropped, reducing WAL log generation from gigabytes to bytes.
- **Reference:** [performance-queries-1.md: Q10 (Partition Detach/Attach for Zero-Downtime Archival)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L378)
- **Impact:** Detach + Drop completes in $\sim 50\text{ms}$ (vs 6 hours for DELETE) with zero WAL replication lag.

```sql
-- ❌ PROHIBITED: Deleting 100M historical rows causes massive lock & 40GB WAL flood
DELETE FROM spans WHERE created_at < '2025-01-01';

-- ✅ MANDATORY: Instant metadata-only detach & drop
ALTER TABLE spans DETACH PARTITION spans_2024_q4 CONCURRENTLY;
DROP TABLE spans_2024_q4;
```

---

### 3.8 Category 8: Distributed Sharding & Consistency Mechanics

#### RULE-QW-31: Shard Key Selection, Co-Location & Hot-Key Salting
- **Requirement:** Sharded tables (Citus/Distributed SQL) **MUST** be sharded on high-cardinality, stable attributes (`tenant_id` or `user_id`) to enforce co-location. Queries touching celebrity or viral entities **MUST** use salted shard key suffixes (`shard_key + random(0-9)`).
- **Reference:** [performance-queries-1.md: Q11 (Shard Key Selection)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L411), [performance-queries-1.md: Q16 (Hot Key Problem)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L601)

```sql
-- ✅ MANDATORY: Citus Co-Location declaration ensures all tenant entities share physical shards
SELECT create_distributed_table('traces', 'tenant_id');
SELECT create_distributed_table('spans',  'tenant_id', colocate_with => 'traces');
```

---

#### RULE-QW-32: CRDT Additive Upserts & Version Vectors Over 2PC
- **Requirement:** Distributed updates across sharded clusters **MUST NOT** use Two-Phase Commit (2PC) protocols. High-throughput distributed counter updates **MUST** use commutative CRDT-style additive upserts (`total_count = total_count + EXCLUDED.total_count`) combined with version vector locks.
- **Reference:** [performance-queries-1.md: Q13 (Cross-Shard Transaction - 2PC vs Saga)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L485), [performance-queries-1.md: Q17 (Distributed UPSERT)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L642), [performance-queries-3.md: Q3 (Atomic Multi-Row Upsert)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-3.md#L122), [performance-queries-4.md: Q2 (Multi-Instance Hot Row Update)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-4.md#L77)
- **Impact:** $30\times$ write throughput gain ($85,000\text{ TPS}$ vs $800\text{ TPS}$).

```sql
-- ✅ MANDATORY: Commutative CRDT upsert eliminates cross-shard lock waiting
INSERT INTO tenant_metrics (tenant_id, metric_name, total_val, version)
VALUES ('tenant_123', 'ingested_spans', 50, 1)
ON CONFLICT (tenant_id, metric_name) DO UPDATE SET
  total_val = tenant_metrics.total_val + EXCLUDED.total_val,
  version   = tenant_metrics.version + 1,
  updated_at = NOW();
```

---

### 3.9 Category 9: Real-Time Streaming, CDC & Replica Routing

#### RULE-QW-33: Incremental High-Watermark Refresh Over Full Re-Scans
- **Requirement:** Real-time materialized view dashboards **MUST NOT** issue full `REFRESH MATERIALIZED VIEW` commands in production loops. Dashboards **MUST** maintain incremental high-watermark aggregation tables driven by micro-batch watermark functions.
- **Reference:** [performance-queries-1.md: Q18 (Streaming Aggregation via Incremental Materialized View)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L685), [performance-queries-2.md: Q7 (Streaming Aggregation via Recursive Poll)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-2.md#L386)
- **Impact:** $2,400\times$ faster refresh ($\sim 200\text{ms}$ micro-batch vs 8-minute full refresh).

```sql
-- ✅ MANDATORY: High-watermark incremental refresh
INSERT INTO hourly_tenant_stats (tenant_id, hourly_bucket, total_spans, last_id)
SELECT tenant_id, DATE_TRUNC('hour', created_at), COUNT(*), MAX(id)
FROM spans
WHERE id > (SELECT last_processed_id FROM watermark_store WHERE name = 'span_stats')
GROUP BY tenant_id, DATE_TRUNC('hour', created_at)
ON CONFLICT (tenant_id, hourly_bucket) DO UPDATE SET
  total_spans = hourly_tenant_stats.total_spans + EXCLUDED.total_spans,
  last_id     = GREATEST(hourly_tenant_stats.last_id, EXCLUDED.last_id);
```

---

#### RULE-QW-34: Event-Driven `LISTEN/NOTIFY` & WAL Logical Decoding
- **Requirement:** Microservices tracking real-time database state changes **MUST NOT** poll tables using repeated `SELECT` queries. Event delivery **MUST** utilize PostgreSQL `LISTEN/NOTIFY` (for low-latency events) or WAL-based Logical Decoding slots (`pg_logical_slot_get_changes`).
- **Reference:** [performance-queries-1.md: Q19 (LISTEN/NOTIFY)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L752), [performance-queries-1.md: Q20 (CDC Logical Decoding Slots)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-1.md#L798), [performance-queries-2.md: Q5 (Multi-Channel LISTEN)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-2.md#L244)

```sql
-- ✅ MANDATORY: Zero-polling change event notification trigger
CREATE OR REPLACE FUNCTION notify_critical_span() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.duration_ms > 5000 THEN
    PERFORM pg_notify('critical_spans', json_build_object(
      'span_id', NEW.id, 'tenant_id', NEW.tenant_id, 'duration_ms', NEW.duration_ms
    )::TEXT);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

#### RULE-QW-35: Causal LSN Replica Routing & Fencing Tokens
- **Requirement:** Read replica routing **MUST** incorporate Log Sequence Number (LSN) validation (`pg_last_wal_replay_lsn() >= $causal_token`). If a replica lags behind the client's write LSN token, the read query **MUST** fall back to the primary database instance.
- **Reference:** [performance-queries-3.md: Q1 (Fencing Token Pattern)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-3.md#L9), [performance-queries-3.md: Q2 (Causal LSN Read-Your-Writes)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-3.md#L71), [performance-queries-2.md: Q1 (PgBouncer Load Balancing)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-2.md#L9), [performance-queries-4.md: Q5 (Quorum Reads Across Replicas)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-4.md#L264)

```sql
-- ✅ MANDATORY: Causal LSN Check for Stale Read Avoidance on Replicas
SELECT 
  CASE WHEN pg_last_wal_replay_lsn() >= $required_lsn::PG_LSN 
       THEN 'REPLICA_READY' 
       ELSE 'REPLICA_STALE' 
  END AS replica_status;
-- If REPLICA_STALE -> Route read to Primary instance.
```

---

### 3.10 Category 10: Special Domain Integrity, Diagnostics & ORM Rules

#### RULE-QW-36: Double-Entry Invariant Validation & Transaction Balance
- **Requirement:** Financial or credit balance ledgers **MUST** enforce double-entry invariants (`SUM(debit) - SUM(credit) = 0`) per transaction entry ID. Global sums are **PROHIBITED** as a verification mechanism because opposing errors cancel each other out.
- **Reference:** [performance-queries-8.md: Q1 (Double-Entry Ledger Balance)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-8.md#L11), [performance-queries-4.md: Q10 (Recursive Running Balance)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-4.md#L663)

```sql
-- ✅ MANDATORY: Entry-level double-entry validation
WITH entry_checks AS (
  SELECT entry_id, SUM(debit) - SUM(credit) AS imbalance
  FROM journal_lines
  WHERE entry_id = $entry_id
  GROUP BY entry_id
)
SELECT entry_id FROM entry_checks WHERE imbalance != 0;
```

---

#### RULE-QW-37: `jsonb_path_ops` GIN Indexing for Semi-Structured Data
- **Requirement:** Tables storing JSONB attributes queried for key-value existence or containment (`@>`) **MUST** utilize `jsonb_path_ops` GIN indexes rather than default GIN indexes to reduce index size by $>60\%$ and accelerate containment lookups.
- **Reference:** [performance-queries-7.md: 1.2 (Index Architecture for Mixed OLTP+OLAP)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-7.md#L138)

```sql
-- ✅ MANDATORY: Dedicated jsonb_path_ops GIN index for rapid containment seeking
CREATE INDEX idx_spans_attributes_gin ON spans USING GIN (attributes jsonb_path_ops)
WHERE attributes IS NOT NULL;
```

---

#### RULE-QW-38: Mandatory `EXPLAIN (ANALYZE, BUFFERS)` CI Gates
- **Requirement:** Every newly added repository SQL query **MUST** be validated using `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` against a representative staging dataset. CI pipelines **MUST** reject any PR introducing query plans containing `Seq Scan` (on tables $>10,000$ rows) or `Using filesort`.
- **Reference:** [performance-queries-0.md: Q38 (Not using EXPLAIN)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L699), [performance-queries-0.md: Q39 (Ignoring query cost)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L720), [performance-queries-5.md: Q1 (EXPLAIN Analysis)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-5.md#L34)

---

#### RULE-QW-39: Automated Optimizer Statistics Freshness Maintenance
- **Requirement:** Following large ingestion batches ($>1,000,000$ rows inserted or updated), background tasks **MUST** trigger explicit database statistic updates (`ANALYZE table_name;`) to prevent stale query execution plans.
- **Reference:** [performance-queries-0.md: Q40 (Statistics not updated)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L740), [performance-queries-5.md: Q4 (Nested Loop on Misestimated Rows)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-5.md#L281), [performance-queries-6.md: D5 (Table Bloat)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-6.md#L191)

---

#### RULE-QW-40: Zero-Tolerance ORM N+1 Query Loop Prevention
- **Requirement:** ORM queries fetching collections and their associated children **MUST** explicitly use eager loading (`joins()`, `includes()`, `select_related()`, or `prefetch_related()`). Issuing database queries inside application loops is strictly prohibited.
- **Reference:** [performance-queries-0.md: Q43 (Using ORM-generated queries blindly)](file:///home/btpl-lap-22/live/llm-observability-platform/policies/rules/database/queries/performance-queries-0.md#L797)

```typescript
// ❌ PROHIBITED: Classic N+1 loop executing 100 queries for 100 traces
const traces = await prisma.trace.findMany();
for (const trace of traces) {
  const spans = await prisma.span.findMany({ where: { traceId: trace.id } });
}

// ✅ MANDATORY: Eager loading issues 1 query with IN clause or JOIN
const tracesWithSpans = await prisma.trace.findMany({
  include: { spans: true }
});
```

---

## 4. Verification & CI/CD Compliance Matrix

```
[ ] 1. All WHERE/JOIN predicates are sargable (no column function wrapping).
[ ] 2. SELECT * is completely absent; explicit columns are specified.
[ ] 3. Pagination uses Keyset cursors ((created_at, id) < ($last_t, $last_id)).
[ ] 4. Currency fields are DECIMAL(15,4) or Integer cents.
[ ] 5. Multi-table aggregation uses LATERAL joins to prevent fan-out.
[ ] 6. Work queues use FOR UPDATE SKIP LOCKED.
[ ] 7. Lock acquisitions follow PK-ascending order (ORDER BY id ASC).
[ ] 8. Micro-batch deletes limit updates to 1,000 rows per transaction.
[ ] 9. EXPLAIN (ANALYZE, BUFFERS) verified 0 Seq Scans in staging.
[ ] 10. ORM queries utilize explicit eager-loading (0 N+1 loops).
```
