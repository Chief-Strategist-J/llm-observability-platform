Good call — let me understand what "generic + actually fast" means for your context before writing 40 queries.# Generic High-Performance SQL — Execution-Proven Patterns

> **How to read this:** Every query is a template. Replace `your_table`, `your_column` with your real names. Each pattern solves a real execution problem, not a theoretical one.

---

## 🔴 PART 1: DIAGNOSTIC QUERIES — RUN THESE RIGHT NOW IN PROD

---

**D1. Find Every Slow Query Running Right Now**

```sql
-- PostgreSQL — Run this when prod feels slow
-- Replace nothing — works on any database immediately

SELECT
  pid,
  now() - query_start                    AS running_for,
  wait_event_type,
  wait_event,
  state,
  ROUND(100.0 * (now()-query_start) /
    NULLIF(EXTRACT(EPOCH FROM (now()-xact_start)),0),1) AS pct_of_txn,
  LEFT(query, 200)                        AS query_snippet,
  application_name,
  client_addr
FROM pg_stat_activity
WHERE state  != 'idle'
  AND pid    != pg_backend_pid()
  AND query_start < now() - INTERVAL '3 seconds'   -- running >3s
ORDER BY query_start ASC;                           -- oldest first = worst first

-- MySQL equivalent:
-- SHOW PROCESSLIST;
-- SELECT * FROM information_schema.PROCESSLIST
-- WHERE TIME > 3 ORDER BY TIME DESC;

-- SQL Server equivalent:
-- SELECT r.session_id, r.status, r.wait_type,
--        r.total_elapsed_time/1000 AS elapsed_secs,
--        LEFT(t.text, 200) AS query_snippet
-- FROM sys.dm_exec_requests r
-- CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
-- WHERE r.total_elapsed_time > 3000 ORDER BY elapsed_secs DESC;
```
**When to run:** First thing when someone says "the app is slow." Tells you exactly which queries are the problem in under 1 second.

---

**D2. Find What Is Blocking What (The Lock Chain)**

```sql
-- PostgreSQL — find blocking queries and their victims

SELECT
  blocked.pid                            AS blocked_pid,
  blocked_act.usename                    AS blocked_user,
  ROUND(EXTRACT(EPOCH FROM
    now() - blocked_act.query_start))    AS blocked_secs,
  LEFT(blocked_act.query, 150)           AS blocked_query,
  '  blocked by  →'                      AS arrow,
  blocking.pid                           AS blocking_pid,
  blocking_act.usename                   AS blocking_user,
  ROUND(EXTRACT(EPOCH FROM
    now() - blocking_act.query_start))   AS blocking_running_secs,
  LEFT(blocking_act.query, 150)          AS blocking_query
FROM pg_locks         blocked
JOIN pg_stat_activity blocked_act  ON blocked_act.pid  = blocked.pid
JOIN pg_locks         blocking     ON  blocking.locktype  = blocked.locktype
                                   AND blocking.relation  = blocked.relation
                                   AND blocking.granted   = TRUE
                                   AND blocking.pid      != blocked.pid
JOIN pg_stat_activity blocking_act ON blocking_act.pid = blocking.pid
WHERE blocked.granted = FALSE
ORDER BY blocked_secs DESC;

-- Kill the blocker if needed (get blocking_pid from above):
-- SELECT pg_terminate_backend(blocking_pid);

-- MySQL:
-- SELECT r.trx_id AS waiting_trx, r.trx_mysql_thread_id AS waiting_thread,
--        r.trx_query AS waiting_query,
--        b.trx_id AS blocking_trx, b.trx_mysql_thread_id AS blocking_thread,
--        b.trx_query AS blocking_query
-- FROM information_schema.innodb_lock_waits w
-- JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id
-- JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id;
```
**When to run:** When app times out on writes. 90% of production emergencies are one long transaction blocking hundreds of others.

---

**D3. Top 20 Slowest Queries by Total Time Consumed**

```sql
-- PostgreSQL — pg_stat_statements must be enabled
-- This shows where your DATABASE TIME actually goes

SELECT
  ROUND(total_exec_time::NUMERIC / 1000, 1)     AS total_secs,
  calls,
  ROUND(mean_exec_time::NUMERIC, 1)             AS avg_ms,
  ROUND(stddev_exec_time::NUMERIC, 1)           AS stddev_ms,
  ROUND(100.0 * total_exec_time /
    SUM(total_exec_time) OVER (), 2)            AS pct_of_db_time,
  rows / NULLIF(calls, 0)                       AS rows_per_call,
  -- Cache hit rate for this query:
  ROUND(100.0 * shared_blks_hit /
    NULLIF(shared_blks_hit + shared_blks_read,0),1) AS cache_hit_pct,
  -- Temp disk spill:
  temp_blks_written * 8 / 1024                  AS temp_mb_spilled,
  LEFT(query, 200)                              AS query_snippet
FROM pg_stat_statements
WHERE calls > 10                               -- ignore one-off queries
ORDER BY total_exec_time DESC
LIMIT 20;

-- Interpretation guide:
-- pct_of_db_time > 20%  → this query is your #1 problem
-- stddev_ms > avg_ms    → query is inconsistent (parameter sniffing, plan instability)
-- cache_hit_pct < 90%   → query is reading from disk (needs index or more RAM)
-- temp_mb_spilled > 0   → hash join / sort spilling to disk (needs more work_mem)

-- Reset stats after fixing (start fresh measurement):
-- SELECT pg_stat_statements_reset();
```

---

**D4. Index Health Check — Every Table in One Query**

```sql
-- PostgreSQL — Tells you: missing indexes, unused indexes, bloated indexes

WITH index_stats AS (
  SELECT
    t.tablename,
    ix.indexname,
    pg_size_pretty(pg_relation_size(ix.indexrelid::REGCLASS)) AS index_size,
    s.idx_scan,
    s.idx_tup_read,
    s.idx_tup_fetch,
    -- Is it a unique/PK index? Don't drop those.
    ix.indexdef ILIKE '%UNIQUE%' OR pi.indisprimary AS is_constraint,
    pi.indisvalid AS is_valid
  FROM pg_indexes ix
  JOIN pg_stat_user_indexes s  ON s.indexrelname = ix.indexname
  JOIN pg_index pi             ON pi.indexrelid   = ix.indexrelid::REGCLASS::OID
  JOIN pg_stat_user_tables t   ON t.relname       = ix.tablename
  WHERE ix.schemaname = 'public'
),
table_stats AS (
  SELECT
    relname AS tablename,
    seq_scan,
    seq_tup_read,
    n_live_tup,
    -- Is this table getting seq scanned a LOT?
    seq_scan > 100 AND n_live_tup > 100000 AS needs_index
  FROM pg_stat_user_tables
)
SELECT
  ts.tablename,
  ts.n_live_tup                              AS row_count,
  -- UNUSED indexes (wasting write performance):
  COUNT(*) FILTER (WHERE is.idx_scan = 0
    AND NOT is.is_constraint)                AS unused_indexes,
  -- USED indexes:
  COUNT(*) FILTER (WHERE is.idx_scan > 0)   AS used_indexes,
  -- Table seq scan rate (high = missing index):
  ts.seq_scan                                AS seq_scans,
  ts.needs_index                             AS likely_missing_index,
  -- Total wasted index space:
  pg_size_pretty(SUM(
    CASE WHEN is.idx_scan = 0 AND NOT is.is_constraint
         THEN pg_relation_size(is.indexname::REGCLASS) ELSE 0 END
  )::BIGINT)                                AS wasted_index_space
FROM table_stats ts
LEFT JOIN index_stats is ON is.tablename = ts.tablename
GROUP BY ts.tablename, ts.n_live_tup, ts.seq_scan, ts.needs_index
HAVING ts.n_live_tup > 10000               -- only tables with real data
ORDER BY ts.seq_scan DESC;
```
**When to run:** Weekly. Catches unused indexes (slowing writes) and missing indexes (slowing reads) before they become emergencies.

---

**D5. Table Bloat — Which Tables Need VACUUM**

```sql
-- PostgreSQL — find tables with dead tuple bloat

SELECT
  schemaname,
  relname                                       AS tablename,
  n_live_tup                                    AS live_rows,
  n_dead_tup                                    AS dead_rows,
  ROUND(100.0 * n_dead_tup /
    NULLIF(n_live_tup + n_dead_tup, 0), 1)     AS dead_pct,
  last_autovacuum,
  last_autoanalyze,
  now() - last_autovacuum                       AS since_vacuum,
  now() - last_autoanalyze                      AS since_analyze,
  n_mod_since_analyze                           AS rows_changed_since_analyze,
  -- Urgency:
  CASE
    WHEN n_dead_tup > n_live_tup               THEN 'CRITICAL — more dead than live'
    WHEN dead_pct > 20                         THEN 'HIGH — vacuum needed'
    WHEN n_mod_since_analyze > n_live_tup*0.1  THEN 'STALE STATS — analyze needed'
    ELSE 'OK'
  END AS status
FROM pg_stat_user_tables
WHERE n_live_tup > 1000
ORDER BY dead_pct DESC NULLS LAST;

-- Fix immediately (replace tablename):
-- VACUUM ANALYZE your_table;
-- For severe bloat with no downtime:
-- VACUUM (VERBOSE, ANALYZE) your_table;
```

---

## 🔴 PART 2: REUSABLE QUERY PATTERNS — APPLY TO ANY TABLE

---

**P1. Safe Pagination — Works at Any Scale (Generic Template)**

```sql
-- ✅ TEMPLATE: Replace table_name, sort_col, id_col, filter_col

-- FIRST PAGE (no cursor):
SELECT
  id,          -- your PK column
  col1,
  col2,
  col3,
  -- Return these as cursor to client:
  sort_col     AS next_cursor_sort,
  id           AS next_cursor_id
FROM your_table
WHERE filter_col = $filter_value      -- your WHERE condition (optional)
ORDER BY sort_col DESC, id DESC       -- two-col sort = stable even with duplicate timestamps
LIMIT 50;

-- NEXT PAGE (client sends back cursor values):
SELECT
  id,
  col1, col2, col3,
  sort_col AS next_cursor_sort,
  id       AS next_cursor_id
FROM your_table
WHERE filter_col = $filter_value
  -- Cursor condition: strictly after last seen row
  -- Works because (sort_col, id) tuple comparison is exact
  AND (sort_col, id) < ($last_cursor_sort, $last_cursor_id)
ORDER BY sort_col DESC, id DESC
LIMIT 50;

-- Required index (create this for every paginated table):
CREATE INDEX CONCURRENTLY idx_your_table_pagination
ON your_table (filter_col, sort_col DESC, id DESC);
-- This single index handles: WHERE filter + ORDER BY + LIMIT
-- Query reads EXACTLY 50 rows regardless of page depth
-- Works identically for page 1 and page 10,000,000

-- MySQL version (same logic, slightly different syntax):
-- WHERE filter_col = ? AND (sort_col < ? OR (sort_col = ? AND id < ?))
-- ORDER BY sort_col DESC, id DESC LIMIT 50;
```
**Copy this pattern for:** Any list view, audit log, activity feed, notification list, admin table.

---

**P2. Upsert — Safe on Any Table (No Race Conditions)**

```sql
-- PostgreSQL template:
INSERT INTO your_table (
  unique_key_col,   -- the column that determines uniqueness
  data_col1,
  data_col2,
  updated_at
)
VALUES (
  $unique_key,
  $data1,
  $data2,
  NOW()
)
ON CONFLICT (unique_key_col) DO UPDATE SET
  data_col1  = EXCLUDED.data_col1,
  data_col2  = EXCLUDED.data_col2,
  updated_at = NOW()
  -- Only update if incoming data is actually different (avoid dirty writes):
  WHERE your_table.data_col1 IS DISTINCT FROM EXCLUDED.data_col1
     OR your_table.data_col2 IS DISTINCT FROM EXCLUDED.data_col2
RETURNING
  id,
  xmax = 0 AS was_insert,  -- TRUE = new row, FALSE = updated existing
  updated_at;

-- MySQL equivalent:
-- INSERT INTO your_table (unique_key_col, data_col1, data_col2, updated_at)
-- VALUES (?, ?, ?, NOW())
-- ON DUPLICATE KEY UPDATE
--   data_col1  = VALUES(data_col1),
--   data_col2  = VALUES(data_col2),
--   updated_at = NOW();

-- SQL Server equivalent:
-- MERGE your_table AS target
-- USING (VALUES(?,?,?)) AS src(unique_key_col, data_col1, data_col2)
-- ON target.unique_key_col = src.unique_key_col
-- WHEN MATCHED THEN UPDATE SET data_col1=src.data_col1, data_col2=src.data_col2
-- WHEN NOT MATCHED THEN INSERT(unique_key_col,data_col1,data_col2) VALUES(src.unique_key_col,...);

-- Batch upsert (1000 rows at once — critical for throughput):
INSERT INTO your_table (unique_key_col, data_col1, data_col2, updated_at)
SELECT
  t.unique_key_col,
  t.data_col1,
  t.data_col2,
  NOW()
FROM (
  VALUES
    ('key1', 'val1a', 'val1b'),
    ('key2', 'val2a', 'val2b')
    -- add up to 1000 rows here
) AS t(unique_key_col, data_col1, data_col2)
ON CONFLICT (unique_key_col) DO UPDATE SET
  data_col1  = EXCLUDED.data_col1,
  data_col2  = EXCLUDED.data_col2,
  updated_at = NOW();
```
**Copy this pattern for:** User profiles, settings, cache tables, metric counters, config rows.

---

**P3. Aggregate-Then-Join — Faster Than Join-Then-Aggregate**

```sql
-- ❌ SLOW PATTERN (everyone writes this by instinct):
SELECT
  parent.id,
  parent.name,
  COUNT(child.id) AS child_count,
  SUM(child.amount) AS total_amount
FROM parent_table parent
JOIN child_table child ON child.parent_id = parent.id
WHERE parent.status = 'active'
GROUP BY parent.id, parent.name;
-- Problem: JOINs ALL child rows to parent THEN aggregates
-- If parent has 10K rows and avg 500 children = 5M intermediate rows

-- ✅ FAST PATTERN — aggregate child FIRST, join summary to parent:
WITH child_summary AS (
  SELECT
    parent_id,
    COUNT(*)     AS child_count,
    SUM(amount)  AS total_amount,
    MAX(created_at) AS last_child_date
  FROM child_table
  -- Filter on child table BEFORE joining (reduces rows early):
  WHERE created_at >= '2024-01-01'  -- your child filter here
  GROUP BY parent_id
)
SELECT
  p.id,
  p.name,
  COALESCE(cs.child_count, 0)    AS child_count,
  COALESCE(cs.total_amount, 0)   AS total_amount,
  cs.last_child_date
FROM parent_table p
LEFT JOIN child_summary cs ON cs.parent_id = p.id
WHERE p.status = 'active';
-- Intermediate rows: 10K parent rows joined to 10K aggregate rows = 10K
-- Was: 5M intermediate rows
-- Works for: orders+items, users+events, accounts+transactions, posts+comments

-- Apply this rule: if you GROUP BY after a JOIN, restructure to CTE first
```

---

**P4. Safe Batch DELETE — Resumable, No Lock Explosion**

```sql
-- ❌ DANGEROUS (single massive delete):
-- DELETE FROM your_table WHERE created_at < '2022-01-01';
-- Locks table, generates massive WAL, blocks everything

-- ✅ GENERIC BATCH DELETE TEMPLATE (works on any table):
DO $$
DECLARE
  v_deleted   INT;
  v_total     INT := 0;
  v_cutoff    TIMESTAMPTZ := NOW() - INTERVAL '2 years';  -- your cutoff
  v_batch     INT := 2000;                                -- tune per table size
BEGIN
  LOOP
    DELETE FROM your_table           -- ← change this
    WHERE id IN (
      SELECT id FROM your_table      -- ← change this
      WHERE created_at < v_cutoff    -- ← change this filter
      LIMIT v_batch
    );

    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    v_total := v_total + v_deleted;

    -- Commit each batch independently (releases locks, WAL checkpoints):
    COMMIT;

    EXIT WHEN v_deleted < v_batch;  -- stop when partial batch = done

    -- Pause: let replication catch up, give other queries a turn:
    PERFORM pg_sleep(0.1);
  END LOOP;

  RAISE NOTICE 'Done. Deleted % total rows.', v_total;
END $$;

-- Tune v_batch based on:
-- Small rows (<200 bytes): 5000-10000 per batch
-- Large rows (>1KB):       500-1000 per batch
-- Tables with many indexes: halve the batch size per extra index
-- Target: each batch completes in <500ms

-- Required: index on the filter column (created_at in this example)
CREATE INDEX CONCURRENTLY idx_your_table_created
ON your_table (created_at)
WHERE created_at < '2022-01-01';  -- partial index: tiny, fast
```

---

**P5. Running Total / Cumulative Sum — Any Time Series**

```sql
-- Generic pattern for: revenue over time, signups, events, any cumulative metric

SELECT
  time_bucket,         -- the time period (day, week, month)
  period_value,        -- value in this period only
  SUM(period_value) OVER (
    ORDER BY time_bucket
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS cumulative_total,
  -- Period-over-period change:
  period_value - LAG(period_value) OVER (ORDER BY time_bucket) AS change_vs_prev,
  -- Percentage change:
  ROUND(100.0 * (period_value - LAG(period_value) OVER (ORDER BY time_bucket)) /
    NULLIF(LAG(period_value) OVER (ORDER BY time_bucket), 0), 1) AS pct_change,
  -- 7-period rolling average:
  ROUND(AVG(period_value) OVER (
    ORDER BY time_bucket
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  )::NUMERIC, 2) AS rolling_7_avg
FROM (
  -- ↓ REPLACE THIS INNER QUERY with your actual data source:
  SELECT
    DATE_TRUNC('day', created_at) AS time_bucket,  -- or 'week', 'month'
    SUM(amount)                   AS period_value   -- or COUNT(*), SUM(anything)
  FROM your_table
  WHERE created_at BETWEEN $start_date AND $end_date
    AND status = 'completed'     -- your filter
  GROUP BY 1
) daily_data
ORDER BY time_bucket;

-- Fill gaps (days with no data appear as 0, not missing):
-- Wrap the above in a generate_series join:
WITH date_spine AS (
  SELECT generate_series(
    $start_date::DATE,
    $end_date::DATE,
    INTERVAL '1 day'
  )::DATE AS time_bucket
),
your_data AS (
  SELECT DATE(created_at) AS time_bucket, SUM(amount) AS period_value
  FROM your_table
  WHERE created_at BETWEEN $start_date AND $end_date
  GROUP BY 1
)
SELECT
  ds.time_bucket,
  COALESCE(yd.period_value, 0) AS period_value,
  SUM(COALESCE(yd.period_value, 0)) OVER (ORDER BY ds.time_bucket) AS cumulative
FROM date_spine ds
LEFT JOIN your_data yd ON yd.time_bucket = ds.time_bucket
ORDER BY ds.time_bucket;
```

---

**P6. Deduplication — Keep One Row Per Group**

```sql
-- Pattern: keep the LATEST row per (group_col) — delete or ignore duplicates

-- FIND duplicates first (always verify before deleting):
SELECT
  group_col,           -- the column that defines "duplicate" (e.g., email, external_id)
  COUNT(*) AS copies,
  MIN(id) AS oldest_id,
  MAX(id) AS newest_id,
  MAX(created_at) AS latest_created
FROM your_table
GROUP BY group_col
HAVING COUNT(*) > 1
ORDER BY copies DESC
LIMIT 100;

-- DELETE duplicates (keep the row with MAX id = most recently inserted):
DELETE FROM your_table
WHERE id NOT IN (
  SELECT MAX(id)       -- keep the newest
  FROM your_table
  GROUP BY group_col   -- one per group
);

-- PostgreSQL faster version using ctid (no subquery):
DELETE FROM your_table a
USING your_table b
WHERE a.group_col = b.group_col   -- same group
  AND a.id < b.id;                -- a is the older duplicate → delete it

-- After dedup: prevent future duplicates:
CREATE UNIQUE INDEX CONCURRENTLY idx_your_table_unique_group
ON your_table (group_col)
WHERE deleted_at IS NULL;         -- partial: ignores soft-deleted rows

-- SELECT dedup (return one row per group without modifying data):
SELECT DISTINCT ON (group_col)   -- PostgreSQL
  id, group_col, col1, col2, created_at
FROM your_table
ORDER BY group_col, created_at DESC;  -- keeps latest per group
-- MySQL: use ROW_NUMBER() OVER (PARTITION BY group_col ORDER BY created_at DESC)
```

---

**P7. Rank / Top-N Per Group — Generic Template**

```sql
-- Pattern: top 3 orders per customer, latest event per session, 
--          best performing product per category, etc.

-- PostgreSQL (cleanest):
SELECT DISTINCT ON (group_col)    -- keep 1 per group (top-1)
  id,
  group_col,
  sort_col,
  col1, col2
FROM your_table
WHERE status = 'active'           -- your filter
ORDER BY group_col, sort_col DESC;-- within each group: highest sort_col first

-- For top-N per group (N > 1), use ROW_NUMBER:
WITH ranked AS (
  SELECT
    id,
    group_col,
    sort_col,
    col1, col2,
    ROW_NUMBER() OVER (
      PARTITION BY group_col        -- one ranking per group
      ORDER BY sort_col DESC        -- highest first
    ) AS rn
  FROM your_table
  WHERE status = 'active'           -- filter INSIDE window function source
    AND created_at >= NOW() - INTERVAL '30 days'
)
SELECT id, group_col, sort_col, col1, col2
FROM ranked
WHERE rn <= 3;                      -- top 3 per group (change N here)

-- Required index (critical — without this it's O(N) for each group):
CREATE INDEX CONCURRENTLY idx_your_table_topn
ON your_table (group_col, sort_col DESC)
INCLUDE (col1, col2)                -- covering: no heap fetch
WHERE status = 'active';            -- partial: only active rows

-- Real examples:
-- Latest order per user:      PARTITION BY user_id ORDER BY created_at DESC
-- Highest invoice per account: PARTITION BY account_id ORDER BY amount DESC
-- Most recent login per device: PARTITION BY device_id ORDER BY login_at DESC
-- Best score per player per game: PARTITION BY player_id, game_id ORDER BY score DESC
```

---

**P8. Conditional Aggregation — Pivot Without Extra Joins**

```sql
-- Pattern: multiple aggregates with different WHERE conditions in ONE scan
-- Use instead of multiple queries or multiple JOINs to subqueries

-- Generic template:
SELECT
  group_col,
  -- Total:
  COUNT(*)                                              AS total_count,
  SUM(amount_col)                                       AS total_amount,
  -- Conditional buckets (no extra table scans):
  COUNT(*) FILTER (WHERE status_col = 'completed')      AS completed_count,
  COUNT(*) FILTER (WHERE status_col = 'pending')        AS pending_count,
  COUNT(*) FILTER (WHERE status_col = 'failed')         AS failed_count,
  SUM(amount_col) FILTER (WHERE status_col = 'completed') AS completed_revenue,
  -- Time buckets (this week vs last week vs this month):
  COUNT(*) FILTER (WHERE created_at >= date_trunc('week', now())) AS this_week,
  COUNT(*) FILTER (WHERE created_at >= date_trunc('month', now())) AS this_month,
  -- Conditional avg (only non-zero):
  ROUND(AVG(amount_col) FILTER (WHERE amount_col > 0)::NUMERIC, 2) AS avg_nonzero,
  -- Percentages:
  ROUND(100.0 * COUNT(*) FILTER (WHERE status_col = 'completed') /
    NULLIF(COUNT(*), 0), 1)                             AS completion_rate_pct
FROM your_table
WHERE created_at >= NOW() - INTERVAL '90 days'
  AND tenant_id = $tenant_id       -- your partition filter (ALWAYS filter first!)
GROUP BY group_col
ORDER BY total_amount DESC;

-- MySQL equivalent uses CASE WHEN:
-- SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count
-- SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) AS completed_revenue

-- This replaces:
-- SELECT ... WHERE status='completed' → 1 query
-- SELECT ... WHERE status='pending'   → 1 query
-- SELECT ... WHERE status='failed'    → 1 query
-- = 3 queries, 3 table scans
-- vs FILTER version: 1 query, 1 table scan
```

---

**P9. Existence Check — Fastest Pattern for "Does This Exist?"**

```sql
-- ❌ SLOW — COUNT(*) to check existence:
SELECT COUNT(*) FROM your_table WHERE condition = $value;
-- Counts ALL matching rows even if you only need to know "any?"

-- ❌ SLOW — SELECT * with LIMIT:
SELECT * FROM your_table WHERE condition = $value LIMIT 1;
-- Fetches row data you don't need

-- ✅ FASTEST — EXISTS with literal:
SELECT EXISTS(
  SELECT 1              -- return constant, not row data
  FROM your_table
  WHERE condition_col = $value
    AND status = 'active'
  LIMIT 1               -- PostgreSQL: stop at first match
);
-- Returns: TRUE or FALSE immediately, stops at first matching row

-- ✅ ALSO FAST — Used in WHERE clause (no subquery overhead):
SELECT id, name, email
FROM parent_table p
WHERE EXISTS (
  SELECT 1 FROM child_table c
  WHERE c.parent_id = p.id
    AND c.status = 'active'
);
-- vs NOT EXISTS (better than NOT IN when NULLs possible):
SELECT id, name FROM parent_table p
WHERE NOT EXISTS (
  SELECT 1 FROM child_table c
  WHERE c.parent_id = p.id
);

-- Batch existence check (check many IDs at once):
SELECT
  t.id,
  t.id = ANY(
    SELECT id FROM your_table WHERE id = t.id AND condition = $value
  ) AS exists_with_condition
FROM (VALUES (1), (2), (3), (1000)) AS t(id);

-- Required index: whatever column(s) appear in EXISTS subquery WHERE
CREATE INDEX CONCURRENTLY idx_child_parent_status
ON child_table (parent_id, status);
```

---

**P10. Efficient NULL Handling — Patterns That Actually Execute Fast**

```sql
-- ❌ SLOW — Functions on indexed column break index:
SELECT * FROM your_table WHERE COALESCE(col, 'default') = 'default';
SELECT * FROM your_table WHERE UPPER(email) = 'USER@EXAMPLE.COM';
SELECT * FROM your_table WHERE DATE(created_at) = '2024-01-15';
-- All of these: COALESCE/UPPER/DATE wraps column → index unused → full scan

-- ✅ FAST — Rewrite to keep column bare:
SELECT * FROM your_table WHERE col IS NULL OR col = 'default';
SELECT * FROM your_table WHERE email = LOWER('USER@EXAMPLE.COM');  -- apply to VALUE not column
SELECT * FROM your_table
WHERE created_at >= '2024-01-15' AND created_at < '2024-01-16'; -- range, not DATE()

-- ✅ NULL-safe patterns:
-- Instead of: WHERE col != 'value' (misses NULLs)
WHERE (col != 'value' OR col IS NULL)       -- includes NULLs in result

-- Instead of: WHERE col = NULL (always false!)
WHERE col IS NULL                           -- correct NULL check

-- COALESCE in SELECT (not WHERE) is fine:
SELECT
  id,
  COALESCE(nickname, first_name, 'Anonymous') AS display_name,   -- OK in SELECT
  COALESCE(amount, 0)                         AS safe_amount,    -- OK
  NULLIF(denominator, 0)                      AS safe_denominator -- division guard
FROM your_table
WHERE col IS NULL                            -- bare column in WHERE = index used
  OR col = '';

-- Safe division (never divide by zero):
SELECT
  numerator / NULLIF(denominator, 0)         AS safe_ratio,       -- returns NULL not ERROR
  COALESCE(numerator / NULLIF(denominator, 0), 0) AS ratio_or_zero
FROM your_table;
```

---

## 🔴 PART 3: INDEX DECISION QUERIES

---

**I1. Should I Add This Index? — Measure Before and After**

```sql
-- Step 1: Check if index already exists (avoid duplicates):
SELECT
  indexname,
  indexdef,
  pg_size_pretty(pg_relation_size(indexname::REGCLASS)) AS size
FROM pg_indexes
WHERE tablename = 'your_table'            -- ← your table
  AND schemaname = 'public';

-- Step 2: Estimate if index will be used (check column selectivity):
SELECT
  'your_col'                              AS column_name,
  COUNT(DISTINCT your_col)                AS distinct_values,
  COUNT(*)                                AS total_rows,
  ROUND(100.0 * COUNT(DISTINCT your_col) / COUNT(*), 2) AS selectivity_pct,
  -- Decision rule:
  CASE
    WHEN COUNT(DISTINCT your_col)::FLOAT / COUNT(*) > 0.01
    THEN 'HIGH selectivity — index WILL help'
    WHEN COUNT(DISTINCT your_col)::FLOAT / COUNT(*) > 0.001
    THEN 'MEDIUM selectivity — index may help for point queries'
    ELSE 'LOW selectivity — index WON''T help (full scan faster)'
  END AS recommendation
FROM your_table;

-- Step 3: Test the query with EXPLAIN before creating index:
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, col1, col2
FROM your_table
WHERE your_col = $test_value
  AND other_col > $other_value;
-- Look for: "Seq Scan" + high "rows removed" = index needed
-- Look for: "Rows Removed by Filter" >> "Rows" = very selective = index helps

-- Step 4: Create index non-destructively:
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_your_table_your_col
ON your_table (your_col, other_col)    -- equality col first, range col second
INCLUDE (col1, col2);                  -- add columns from SELECT to avoid heap fetch

-- Step 5: Verify query uses the new index:
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, col1, col2
FROM your_table
WHERE your_col = $test_value AND other_col > $other_value;
-- Now should show: "Index Only Scan" or "Index Scan" (not "Seq Scan")

-- Step 6: Check index is being used in production after 24 hours:
SELECT indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename = 'your_table'
  AND indexname = 'idx_your_table_your_col';
-- idx_scan = 0 after 24 hours? Either drop it or your query isn't running as expected.
```

---

**I2. Composite Index Column Order — Get It Right First Time**

```sql
-- Rule: Put columns in this order:
-- 1. Equality columns (WHERE col = value)  → leftmost
-- 2. Range columns   (WHERE col > value)   → after equality
-- 3. ORDER BY columns                      → after range
-- 4. INCLUDE columns (SELECT cols)         → in INCLUDE clause

-- Template for the most common query pattern:
-- SELECT a, b FROM t WHERE x = ? AND y > ? ORDER BY z DESC LIMIT N

CREATE INDEX CONCURRENTLY idx_template
ON your_table (
  equality_col_1,      -- WHERE col = ?         (most selective equality first)
  equality_col_2,      -- WHERE col = ?         (second equality)
  range_col,           -- WHERE col > ? / BETWEEN (range always after equality)
  order_col DESC       -- ORDER BY col DESC      (match exact query sort direction)
)
INCLUDE (
  select_col_1,        -- columns in SELECT but not WHERE/ORDER BY
  select_col_2         -- avoids heap fetch → "Index Only Scan"
);

-- Verify column order is correct by checking EXPLAIN:
EXPLAIN SELECT select_col_1, select_col_2
FROM your_table
WHERE equality_col_1 = $v1
  AND equality_col_2 = $v2
  AND range_col > $v3
ORDER BY order_col DESC
LIMIT 50;
-- Must show: "Index Only Scan" using your new index
-- Must NOT show: "Sort" step (sort was eliminated by index order)
-- Must NOT show: "Filter" removing rows (all predicates covered by index)
```

---

## 🔴 PART 4: LOCK / BLOCKING DETECTION

---

**L1. Real-Time Lock Monitor — Complete Picture**

```sql
-- PostgreSQL — Run when app slows or times out on writes

SELECT
  -- What is waiting:
  wait_act.pid                           AS waiting_pid,
  wait_act.application_name             AS waiting_app,
  LEFT(wait_act.query, 100)             AS waiting_query,
  ROUND(EXTRACT(EPOCH FROM
    now() - wait_act.query_start))      AS waiting_secs,
  wait_lock.locktype,
  wait_lock.mode                        AS requested_mode,
  -- What is blocking:
  hold_act.pid                          AS holding_pid,
  hold_act.application_name            AS holding_app,
  LEFT(hold_act.query, 100)            AS holding_query,
  ROUND(EXTRACT(EPOCH FROM
    now() - hold_act.xact_start))      AS holding_txn_age_secs,
  hold_lock.mode                        AS holding_mode
FROM pg_locks wait_lock
JOIN pg_stat_activity wait_act  ON wait_act.pid  = wait_lock.pid
JOIN pg_locks hold_lock         ON  hold_lock.relation IS NOT DISTINCT FROM wait_lock.relation
                                AND hold_lock.locktype   = wait_lock.locktype
                                AND hold_lock.granted    = TRUE
                                AND hold_lock.pid       != wait_lock.pid
JOIN pg_stat_activity hold_act  ON hold_act.pid = hold_lock.pid
WHERE wait_lock.granted = FALSE
ORDER BY waiting_secs DESC;

-- See chain: who is blocked by whom by whom (multi-level):
SELECT
  pid,
  LEFT(query, 80) AS query,
  pg_blocking_pids(pid) AS blocked_by,
  CARDINALITY(pg_blocking_pids(pid)) AS blocked_by_count
FROM pg_stat_activity
WHERE CARDINALITY(pg_blocking_pids(pid)) > 0;

-- Immediate fix if blocker is idle-in-transaction (safe to kill):
SELECT pid, state, xact_start, LEFT(query,80)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND xact_start < now() - INTERVAL '2 minutes';
-- Kill it:
-- SELECT pg_terminate_backend(pid_from_above);
```

---

**L2. Idle-in-Transaction Killer — Auto-Protection Query**

```sql
-- PostgreSQL: Find and kill connections that opened a transaction
-- and then did nothing for too long (common app bug: forgot to commit)

WITH idle_txn_offenders AS (
  SELECT
    pid,
    usename,
    application_name,
    client_addr,
    xact_start,
    now() - xact_start AS idle_duration,
    state,
    LEFT(query, 150) AS last_query
  FROM pg_stat_activity
  WHERE state = 'idle in transaction'
    AND xact_start < now() - INTERVAL '5 minutes'  -- idle for 5+ minutes
    AND pid != pg_backend_pid()
  ORDER BY xact_start ASC
)
SELECT
  pid,
  usename,
  idle_duration,
  last_query,
  -- Safe termination (returns true if killed):
  pg_terminate_backend(pid) AS terminated
FROM idle_txn_offenders;

-- PostgreSQL 14+ automatic setting (add to postgresql.conf):
-- idle_in_transaction_session_timeout = '5min'  -- auto-kills after 5 min

-- Monitor connection pool health continuously:
SELECT
  state,
  COUNT(*) AS connections,
  MAX(now() - state_change) AS longest_in_state,
  MAX(now() - xact_start) FILTER (WHERE xact_start IS NOT NULL) AS oldest_txn
FROM pg_stat_activity
WHERE datname = current_database()
  AND pid != pg_backend_pid()
GROUP BY state
ORDER BY connections DESC;
```

---

**L3. Table-Level Lock Detection (Schema Changes Blocking Everything)**

```sql
-- PostgreSQL — detects when ALTER TABLE, CREATE INDEX, VACUUM FULL
-- are holding AccessExclusiveLock blocking ALL queries

SELECT
  pg_class.relname AS locked_table,
  pg_locks.mode AS lock_mode,
  pg_locks.granted,
  pg_stat_activity.pid,
  pg_stat_activity.usename,
  pg_stat_activity.application_name,
  LEFT(pg_stat_activity.query, 200) AS query,
  now() - pg_stat_activity.query_start AS lock_duration,
  -- Impact: how many queries are waiting for this lock?
  (SELECT COUNT(*) FROM pg_locks waiting
   WHERE waiting.relation = pg_locks.relation
     AND waiting.granted = FALSE) AS queries_waiting
FROM pg_locks
JOIN pg_class ON pg_class.oid = pg_locks.relation
JOIN pg_stat_activity ON pg_stat_activity.pid = pg_locks.pid
WHERE pg_locks.locktype = 'relation'
  AND pg_class.relkind = 'r'               -- regular tables only
  AND pg_locks.mode IN (
    'AccessExclusiveLock',                  -- DDL (ALTER, DROP, VACUUM FULL)
    'ExclusiveLock',                        -- explicit LOCK TABLE
    'ShareUpdateExclusiveLock'              -- VACUUM, ANALYZE, CREATE INDEX CONCURRENTLY
  )
ORDER BY lock_duration DESC;
```

---

## 🔴 PART 5: PATTERNS THAT EXECUTE FAST IN ALL ENGINES

---

**F1. The Anti-N+1 Pattern — One Query Replaces N Queries**

```sql
-- ❌ N+1 (what ORMs generate by default):
-- Query 1: SELECT id FROM orders WHERE status='pending' → returns 500 IDs
-- Query 2-501: SELECT * FROM users WHERE id = $each_order_user_id
-- Total: 501 queries, 500 × round-trip latency

-- ✅ Fix: fetch everything in ONE query using IN or JOIN:

-- Option A — JOIN (best when you need columns from both tables):
SELECT
  o.id AS order_id,
  o.amount,
  o.status,
  u.id AS user_id,
  u.email,
  u.tier
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE o.status = 'pending'
  AND o.created_at >= NOW() - INTERVAL '24 hours';

-- Option B — Batch IN lookup (when you already have IDs):
SELECT id, email, tier, name
FROM users
WHERE id = ANY($array_of_ids::BIGINT[]);  -- PostgreSQL
-- MySQL: WHERE id IN (id1, id2, ..., idN)  -- max 1000 for MySQL

-- Option C — JSON aggregation (return nested data in one query):
SELECT
  o.id,
  o.amount,
  o.status,
  -- Nested user object (no second query):
  jsonb_build_object(
    'id',    u.id,
    'email', u.email,
    'tier',  u.tier
  ) AS user,
  -- Nested items array (no third query):
  COALESCE(
    jsonb_agg(jsonb_build_object(
      'product_id', oi.product_id,
      'quantity',   oi.quantity,
      'price',      oi.unit_price
    ) ORDER BY oi.id),
    '[]'::JSONB
  ) AS items
FROM orders o
JOIN users u ON u.id = o.user_id
LEFT JOIN order_items oi ON oi.order_id = o.id
WHERE o.id = ANY($order_ids::BIGINT[])
GROUP BY o.id, o.amount, o.status, u.id, u.email, u.tier;
-- Returns: 1 row per order, with user + items embedded
-- Replaces: 1 + N + N queries with exactly 1 query
```

---

**F2. Fast Reporting Query — Any Date Range, Any Granularity**

```sql
-- Generic reporting template: replace table/columns, works for any metric

-- The key: use date_trunc with variable granularity + conditional aggregation

SELECT
  -- Time bucket (change 'day' to 'week', 'month', 'quarter', 'year'):
  DATE_TRUNC('day', created_at)::DATE      AS period,

  -- Dimensions (group by any combination):
  status_col                               AS status,
  category_col                             AS category,

  -- Core metrics:
  COUNT(*)                                 AS total_count,
  COUNT(DISTINCT user_id_col)              AS unique_users,
  SUM(amount_col)                          AS total_amount,
  ROUND(AVG(amount_col)::NUMERIC, 2)       AS avg_amount,
  MIN(amount_col)                          AS min_amount,
  MAX(amount_col)                          AS max_amount,

  -- Percentiles (PostgreSQL):
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY amount_col) AS median,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY amount_col) AS p95,

  -- Comparison to previous period:
  SUM(amount_col) - LAG(SUM(amount_col)) OVER (
    PARTITION BY status_col, category_col
    ORDER BY DATE_TRUNC('day', created_at)
  ) AS change_vs_prev_period,

  -- Running total:
  SUM(SUM(amount_col)) OVER (
    PARTITION BY status_col, category_col
    ORDER BY DATE_TRUNC('day', created_at)
    ROWS UNBOUNDED PRECEDING
  ) AS running_total

FROM your_table
WHERE created_at BETWEEN $start_date AND $end_date  -- always bound by date
  AND tenant_id = $tenant_id                         -- always filter by tenant first
  AND status_col != 'cancelled'                      -- your exclusion filter
GROUP BY
  DATE_TRUNC('day', created_at),
  status_col,
  category_col
ORDER BY period, total_amount DESC;

-- Required index for this query to execute fast:
CREATE INDEX CONCURRENTLY idx_reporting
ON your_table (tenant_id, created_at, status_col)
INCLUDE (amount_col, user_id_col, category_col);
-- With this index: query reads ONLY the date range rows, no heap fetch
```

---

**F3. Idempotent Batch Insert — Safe to Retry Anytime**

```sql
-- Pattern: insert a batch of rows where some may already exist
-- Safe to run multiple times (duplicates silently ignored)
-- Works for: ETL loads, event ingestion, sync jobs, migrations

-- PostgreSQL:
INSERT INTO your_table (
  natural_key_col,    -- the business key (not surrogate)
  data_col1,
  data_col2,
  data_col3,
  source_system,
  loaded_at
)
SELECT
  src.natural_key_col,
  src.data_col1,
  src.data_col2,
  src.data_col3,
  'source_system_name',
  NOW()
FROM (
  VALUES
    ('key001', 'val1', 100.00, 'active'),
    ('key002', 'val2', 200.00, 'active'),
    ('key003', 'val3', NULL,   'pending')
    -- up to 10,000 rows per batch (tune based on row size)
) AS src(natural_key_col, data_col1, data_col2, data_col3)
ON CONFLICT (natural_key_col) DO NOTHING;  -- ignore if already exists
-- Completely safe to re-run: already-loaded rows untouched

-- With update on conflict (upsert):
ON CONFLICT (natural_key_col) DO UPDATE SET
  data_col1  = EXCLUDED.data_col1,
  data_col2  = EXCLUDED.data_col2,
  loaded_at  = NOW()
  -- Only update if data changed (skip no-op updates):
  WHERE (your_table.data_col1, your_table.data_col2)
     IS DISTINCT FROM (EXCLUDED.data_col1, EXCLUDED.data_col2);

-- Track what was inserted vs skipped (for logging):
WITH inserted AS (
  INSERT INTO your_table ... ON CONFLICT DO NOTHING
  RETURNING natural_key_col
)
SELECT
  COUNT(*) AS rows_inserted,
  $total_attempted - COUNT(*) AS rows_skipped
FROM inserted;
```

---

**F4. Efficient Full-Text Search (No Elasticsearch Needed)**

```sql
-- PostgreSQL built-in full-text search — fast at millions of rows

-- Setup (one time):
ALTER TABLE your_table ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;

-- Populate (run once, then maintain via trigger):
UPDATE your_table SET
  search_vector = TO_TSVECTOR('english',
    COALESCE(title, '') || ' ' ||
    COALESCE(description, '') || ' ' ||
    COALESCE(tags, '')          -- combine all searchable text
  );

-- Index (GIN for full-text — mandatory for performance):
CREATE INDEX CONCURRENTLY idx_your_table_fts
ON your_table USING GIN (search_vector);

-- Keep it current via trigger:
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := TO_TSVECTOR('english',
    COALESCE(NEW.title, '') || ' ' ||
    COALESCE(NEW.description, '') || ' ' ||
    COALESCE(NEW.tags, '')
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_search_vector
BEFORE INSERT OR UPDATE ON your_table
FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Search query (generic, replace 'your search terms'):
SELECT
  id, title, description,
  -- Relevance rank (higher = better match):
  TS_RANK(search_vector, query) AS rank,
  -- Highlighted snippet:
  TS_HEADLINE('english', description, query,
    'MaxWords=30, MinWords=15, StartSel=<b>, StopSel=</b>'
  ) AS snippet
FROM your_table,
  TO_TSQUERY('english', $search_terms) AS query  -- 'apple & iphone | samsung'
WHERE search_vector @@ query
  AND status = 'active'              -- your filter
ORDER BY rank DESC, created_at DESC
LIMIT 20;
```
**Execution speed:** GIN index = ~5-50ms for millions of rows vs Elasticsearch round-trip ~50-200ms + infrastructure cost.

---

## Quick Reference — Copy These Every Time

```sql
-- ① Check if query uses index (run before AND after any index change):
EXPLAIN (ANALYZE, BUFFERS) your_query_here;
-- Seq Scan  = no index (bad for large tables)
-- Index Scan = uses index, still fetches heap
-- Index Only Scan = uses index, NO heap fetch (best)
-- Heap Fetches: 0 = perfect

-- ② Add index without locking table:
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_name ON table(col);

-- ③ Check if index is actually being used (wait 24h after create):
SELECT idx_scan, idx_tup_read FROM pg_stat_user_indexes
WHERE indexrelname = 'idx_name';  -- 0 = not used, consider dropping

-- ④ Force query to use specific index (test before making permanent):
SET enable_seqscan = OFF;         -- forces index scan (PostgreSQL, session only)
SELECT ...;
SET enable_seqscan = ON;

-- ⑤ Kill a specific query safely:
SELECT pg_cancel_backend(pid);    -- sends cancel signal (query stops, connection lives)
SELECT pg_terminate_backend(pid); -- kills connection (use if cancel doesn't work)

-- ⑥ See live row counts without COUNT(*) scan:
SELECT reltuples::BIGINT AS estimated_rows FROM pg_class WHERE relname = 'your_table';

-- ⑦ Table size breakdown:
SELECT
  pg_size_pretty(pg_relation_size('your_table')) AS table_size,
  pg_size_pretty(pg_indexes_size('your_table')) AS indexes_size,
  pg_size_pretty(pg_total_relation_size('your_table')) AS total_size;

-- ⑧ Reset pg_stat_statements (start fresh after fixing a problem):
SELECT pg_stat_statements_reset();

-- ⑨ Safe way to check if a value exists (faster than COUNT > 0):
SELECT EXISTS(SELECT 1 FROM your_table WHERE col = $value LIMIT 1);

-- ⑩ Find tables missing indexes on FK columns:
SELECT conrelid::REGCLASS AS table, a.attname AS fk_column
FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid
  AND a.attnum = ANY(c.conkey)
WHERE c.contype = 'f'
  AND NOT EXISTS (
    SELECT 1 FROM pg_index i
    WHERE i.indrelid = c.conrelid
      AND a.attnum = ANY(i.indkey)
  );
```
# Production SQL — All 4 Problem Classes, Generic Templates, Real Execution

> **Every query here**: copy → replace table/column names → run. No theory. Each section solves one specific execution problem you described.

---

## 🔴 PROBLEM 1: SCHEDULED JOBS GETTING SLOWER EVERY WEEK

**Why it happens:** Job was designed for 1M rows. Now table has 500M. Same query, linear growth in execution time.

---

**1. Diagnose Why Your Job Is Slowing Down Week Over Week**

```sql
-- Run this BEFORE touching anything else
-- Shows exactly what's happening to your slow job over time

-- PostgreSQL
SELECT
  DATE_TRUNC('day', NOW())               AS checked_at,
  relname                                AS table_name,
  n_live_tup                             AS live_rows,
  n_dead_tup                             AS dead_rows,
  ROUND(100.0 * n_dead_tup /
    NULLIF(n_live_tup + n_dead_tup, 0),1) AS dead_pct,
  n_mod_since_analyze                    AS rows_changed_since_last_analyze,
  -- This is why your job slows: planner uses stale row counts
  ROUND(100.0 * n_mod_since_analyze /
    NULLIF(n_live_tup, 0), 1)            AS pct_stale,
  last_autovacuum::DATE                  AS last_vacuum,
  last_autoanalyze::DATE                 AS last_analyze,
  -- How long since last analyze (stale stats = bad plans)
  NOW() - last_autoanalyze               AS analyze_age,
  seq_scan                               AS full_table_scans,
  idx_scan                               AS index_scans,
  -- Red flag: high seq_scan on big table = missing index
  CASE
    WHEN n_live_tup > 1000000
     AND seq_scan > idx_scan            THEN '🔴 MISSING INDEX'
    WHEN n_mod_since_analyze >
         n_live_tup * 0.1              THEN '🟡 STALE STATS'
    WHEN n_dead_tup > n_live_tup * 0.2 THEN '🟡 NEEDS VACUUM'
    ELSE '✅ OK'
  END                                    AS diagnosis
FROM pg_stat_user_tables
WHERE n_live_tup > 100000                -- only tables worth caring about
ORDER BY n_live_tup DESC;

-- Fix stale stats immediately (replace your_table):
ANALYZE your_table;
-- Or for entire database:
ANALYZE;
```

---

**2. Job Growth Tracker — Compare This Week vs Last Week**

```sql
-- Paste this at the START of every scheduled job
-- Gives you a growth report before it runs

-- PostgreSQL
WITH table_sizes AS (
  SELECT
    relname                                           AS table_name,
    reltuples::BIGINT                                 AS est_rows,
    pg_size_pretty(pg_total_relation_size(oid))       AS total_size,
    pg_total_relation_size(oid)                       AS total_bytes,
    pg_size_pretty(pg_relation_size(oid))             AS table_size,
    pg_size_pretty(pg_indexes_size(oid))              AS index_size,
    -- Growth since last stats reset
    (SELECT SUM(n_tup_ins) FROM pg_stat_user_tables
     WHERE relname = c.relname)                       AS total_inserts,
    (SELECT SUM(n_tup_del) FROM pg_stat_user_tables
     WHERE relname = c.relname)                       AS total_deletes
  FROM pg_class c
  WHERE relkind = 'r'
    AND relnamespace = 'public'::REGNAMESPACE
    AND reltuples > 100000               -- only big tables
)
SELECT
  table_name,
  est_rows,
  total_size,
  table_size,
  index_size,
  -- Index-to-table ratio (>3x = over-indexed, slowing writes)
  ROUND(pg_indexes_size(table_name::REGCLASS)::NUMERIC /
    NULLIF(pg_relation_size(table_name::REGCLASS), 0), 2) AS index_ratio,
  CASE
    WHEN pg_indexes_size(table_name::REGCLASS) >
         pg_relation_size(table_name::REGCLASS) * 3
    THEN '🔴 OVER-INDEXED — writes slowing down'
    ELSE '✅'
  END AS index_health
FROM table_sizes
ORDER BY total_bytes DESC
LIMIT 20;
```

---

**3. Generic Chunked Job Template — Stops Getting Slower as Data Grows**

```sql
-- Replace: your_table, your_filter_col, your_filter_value, your_batch_size
-- This pattern: job time stays CONSTANT as table grows

-- PostgreSQL / works similarly in all engines

DO $$
DECLARE
  v_batch_size    INT         := 5000;       -- tune: aim for <500ms per batch
  v_last_id       BIGINT      := 0;          -- start from beginning
  v_max_id        BIGINT;
  v_processed     INT         := 0;
  v_total         INT         := 0;
  v_start_time    TIMESTAMPTZ := clock_timestamp();
  v_batch_start   TIMESTAMPTZ;
  v_batch_ms      NUMERIC;
BEGIN
  -- Get max ID once (don't recalculate each loop)
  SELECT MAX(id) INTO v_max_id FROM your_table
  WHERE your_filter_col = your_filter_value;  -- ← your filter

  RAISE NOTICE 'Starting. Max ID: %, Est rows: %',
    v_max_id,
    (SELECT COUNT(*) FROM your_table WHERE your_filter_col = your_filter_value);

  WHILE v_last_id < v_max_id LOOP
    v_batch_start := clock_timestamp();

    -- YOUR ACTUAL JOB LOGIC HERE:
    UPDATE your_table SET
      processed_col  = TRUE,
      processed_at   = NOW()
    WHERE id > v_last_id
      AND id <= v_last_id + v_batch_size
      AND your_filter_col = your_filter_value   -- ← your filter
      AND processed_col = FALSE;                -- ← skip already done

    GET DIAGNOSTICS v_processed = ROW_COUNT;
    v_total   := v_total + v_processed;
    v_last_id := v_last_id + v_batch_size;

    -- Measure batch time (tells you if batch_size needs tuning)
    v_batch_ms := EXTRACT(EPOCH FROM clock_timestamp() - v_batch_start) * 1000;

    -- Auto-tune: if batch takes >800ms, warn
    IF v_batch_ms > 800 THEN
      RAISE WARNING 'Batch slow: %ms. Consider reducing batch_size to %',
        ROUND(v_batch_ms), v_batch_size / 2;
    END IF;

    -- Progress every 100 batches
    IF MOD(v_last_id / v_batch_size, 100) = 0 THEN
      RAISE NOTICE 'Progress: id=%, rows done=%, elapsed=%s',
        v_last_id, v_total,
        ROUND(EXTRACT(EPOCH FROM clock_timestamp() - v_start_time));
    END IF;

    -- Adaptive sleep: back off if DB is under load
    PERFORM pg_sleep(CASE
      WHEN v_batch_ms > 500 THEN 0.5   -- batch slow = DB busy, wait longer
      WHEN v_batch_ms > 200 THEN 0.2
      ELSE 0.05                         -- fast batch = minimal wait
    END);

  END LOOP;

  RAISE NOTICE 'Done. Total: %, Time: %s',
    v_total,
    ROUND(EXTRACT(EPOCH FROM clock_timestamp() - v_start_time));
END $$;

-- Required index for this pattern to stay fast as data grows:
-- Must cover: id (range) + your_filter_col + processed_col
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_your_table_job
ON your_table (your_filter_col, processed_col, id)
WHERE processed_col = FALSE;   -- partial index: only unprocessed rows
                                -- stays small as rows get processed
```
**Why it stays fast:** Partial index shrinks as rows are processed. Each batch reads exactly `batch_size` rows. Job time = (rows_to_process / batch_size) × batch_time — linear, not quadratic.

---

**4. Auto-Detecting When a Job Needs Re-Indexing**

```sql
-- Run this at the START of every weekly job
-- Tells you: "your index is bloated, rebuild before running the job"

-- PostgreSQL
WITH index_health AS (
  SELECT
    s.relname                                          AS table_name,
    s.indexrelname                                     AS index_name,
    pg_size_pretty(pg_relation_size(s.indexrelid))    AS index_size,
    pg_relation_size(s.indexrelid)                     AS index_bytes,
    pg_size_pretty(pg_relation_size(s.relid))         AS table_size,
    pg_relation_size(s.relid)                          AS table_bytes,
    s.idx_scan                                         AS scans,
    s.idx_tup_read                                     AS rows_read,
    -- Bloat signal: index much larger than table = bloated
    ROUND(pg_relation_size(s.indexrelid)::NUMERIC /
      NULLIF(pg_relation_size(s.relid), 0), 2)        AS index_to_table_ratio,
    -- Efficiency: rows returned per scan
    ROUND(s.idx_tup_read::NUMERIC /
      NULLIF(s.idx_scan, 0), 0)                       AS rows_per_scan
  FROM pg_stat_user_indexes s
  WHERE pg_relation_size(s.relid) > 100 * 1024 * 1024 -- tables >100MB
),
bloat_check AS (
  SELECT
    table_name,
    index_name,
    index_size,
    table_size,
    index_to_table_ratio,
    scans,
    rows_per_scan,
    CASE
      WHEN scans = 0
       AND index_name NOT IN (
         SELECT indexname FROM pg_indexes
         WHERE indexdef ILIKE '%UNIQUE%'
           OR indexdef ILIKE '%PRIMARY%'
       )                              THEN '🔴 UNUSED — drop it'
      WHEN index_to_table_ratio > 2  THEN '🟡 BLOATED — REINDEX CONCURRENTLY'
      WHEN index_to_table_ratio > 1  THEN '🟡 LARGE — monitor'
      ELSE                                '✅ HEALTHY'
    END                              AS recommendation,
    -- Generate the fix command
    CASE
      WHEN scans = 0                 THEN 'DROP INDEX CONCURRENTLY ' || index_name || ';'
      WHEN index_to_table_ratio > 2  THEN 'REINDEX INDEX CONCURRENTLY ' || index_name || ';'
      ELSE NULL
    END                              AS fix_command
  FROM index_health
)
SELECT * FROM bloat_check
WHERE recommendation != '✅ HEALTHY'
ORDER BY index_bytes DESC;
```

---

## 🔴 PROBLEM 2: RUNS FINE FIRST TIME, SLOWER AFTER DATA GROWS

**Why it happens:** Query plan made for small table. Statistics go stale. Optimizer picks wrong join order or index.

---

**5. Generic EXPLAIN Interpreter — Know Exactly What's Wrong**

```sql
-- Run this on ANY slow query to get a human-readable diagnosis
-- Replace the SELECT at the bottom with your actual query

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
-- ↓ PASTE YOUR QUERY HERE
SELECT *
FROM your_table
WHERE your_col = $value;

-- HOW TO READ THE OUTPUT:
-- ┌─────────────────────────────────────────────────────────────────┐
-- │ Node Type        │ What it means          │ Is it bad?          │
-- ├─────────────────────────────────────────────────────────────────┤
-- │ Seq Scan         │ Read every row         │ BAD on >100K rows   │
-- │ Index Scan       │ Use index + heap fetch │ GOOD                │
-- │ Index Only Scan  │ Use index, no heap     │ BEST                │
-- │ Hash Join        │ Build hash + probe     │ OK for large sets   │
-- │ Nested Loop      │ For each row, lookup   │ BAD if outer is big │
-- │ Sort             │ Sort in memory/disk    │ BAD if Disk: true   │
-- │ Hash             │ Build hash table       │ BAD if Batches>1    │
-- └─────────────────────────────────────────────────────────────────┘

-- KEY NUMBERS TO LOOK FOR:
-- 1. "rows=X" vs "(actual rows=Y)" — if Y >> X: stale stats (run ANALYZE)
-- 2. "Heap Fetches: N" — N > 0 means index not covering (add INCLUDE columns)
-- 3. "Batches: N" on Hash — N > 1 means spilling to disk (increase work_mem)
-- 4. "Rows Removed by Filter: N" — N >> actual rows = wrong index or no index
-- 5. "actual time=X..Y" — Y is total node time. Find the highest Y.

-- Quick diagnosis query — runs EXPLAIN and summarizes problems:
DO $$
DECLARE
  v_plan JSONB;
BEGIN
  EXECUTE 'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' ||
          'SELECT * FROM your_table WHERE your_col = $1'  -- ← your query
  INTO v_plan USING 'your_value';

  RAISE NOTICE 'Plan: %', jsonb_pretty(v_plan);
END $$;
```

---

**6. Statistics Quality Check — Why Planner Makes Wrong Choices**

```sql
-- PostgreSQL
-- Shows which columns have statistics too low for your data distribution
-- Run this when EXPLAIN shows estimated rows very different from actual rows

SELECT
  s.tablename,
  s.attname                              AS column_name,
  s.n_distinct                           AS distinct_values,
  -- n_distinct > 0 = actual count, < 0 = fraction of rows
  CASE WHEN s.n_distinct < 0
    THEN ROUND(ABS(s.n_distinct) * c.reltuples)::TEXT || ' (estimate)'
    ELSE s.n_distinct::TEXT
  END                                    AS est_distinct_count,
  ROUND(s.null_frac * 100, 1)           AS null_pct,
  s.most_common_vals::TEXT               AS top_values,
  s.most_common_freqs::TEXT              AS top_value_freqs,
  -- Current stats depth (default 100, max 10000)
  s.stadistinct::TEXT                    AS stats_depth,
  -- Is this column used in WHERE clauses? If so, stats matter a lot
  EXISTS (
    SELECT 1 FROM pg_stat_user_indexes si
    WHERE si.relname = s.tablename
      AND si.indexrelname LIKE '%' || s.attname || '%'
  )                                      AS has_index,
  -- Should we increase statistics?
  CASE
    WHEN s.most_common_freqs IS NOT NULL
      AND (s.most_common_freqs::TEXT::FLOAT[] && ARRAY[0.01])
    THEN '🟡 SKEWED — increase stats: ALTER TABLE ' ||
         s.tablename || ' ALTER COLUMN ' || s.attname ||
         ' SET STATISTICS 500;'
    WHEN ABS(s.n_distinct) > 10000
    THEN '🟡 HIGH CARDINALITY — increase stats target'
    ELSE '✅ OK'
  END                                    AS recommendation
FROM pg_stats s
JOIN pg_class c ON c.relname = s.tablename
WHERE s.schemaname = 'public'
  AND c.reltuples > 100000               -- only tables with real data
  AND s.tablename = 'your_table'         -- ← focus on your problem table
ORDER BY s.tablename, s.attname;

-- Fix: increase statistics target for a column
ALTER TABLE your_table ALTER COLUMN your_col SET STATISTICS 500;
ANALYZE your_table (your_col);  -- analyze only this column (faster)

-- Verify fix: check planner estimate matches reality
EXPLAIN (ANALYZE)
SELECT * FROM your_table WHERE your_col = $your_typical_value;
-- "rows=X" should now be close to "(actual rows=Y)"
```

---

**7. The Plan Stability Test — Catch Plans That Change Under Load**

```sql
-- PostgreSQL
-- Run this to detect if your query uses different plans at different data sizes
-- Catches: parameter sniffing, plan cache pollution, stats staleness

-- Step 1: capture current plan as baseline
EXPLAIN (FORMAT JSON, ANALYZE)
SELECT your_columns
FROM your_table
WHERE your_filter = $value_1;   -- ← typical value

-- Step 2: test with a different value (different selectivity)
EXPLAIN (FORMAT JSON, ANALYZE)
SELECT your_columns
FROM your_table
WHERE your_filter = $value_2;   -- ← rare value (should trigger different selectivity)

-- Step 3: compare plan node types
-- If Step 1 shows "Hash Join" and Step 2 shows "Nested Loop":
-- = plan instability. Fix with:

-- Fix A — Force generic plan (PostgreSQL):
SET plan_cache_mode = 'force_generic_plan';

-- Fix B — Increase stats so planner sees true distribution:
ALTER TABLE your_table ALTER COLUMN your_filter SET STATISTICS 1000;
ANALYZE your_table;

-- Fix C — SQL Server parameter sniffing fix:
-- Add OPTION(RECOMPILE) to stored procedure
-- Or: OPTION(OPTIMIZE FOR (@param UNKNOWN))

-- Fix D — MySQL: force index when optimizer picks wrong one:
SELECT /*+ INDEX(t idx_your_index) */ *
FROM your_table t
WHERE your_filter = $value;

-- Monitor plan changes in production (PostgreSQL):
SELECT
  LEFT(query, 100)                       AS query,
  calls,
  ROUND(mean_exec_time::NUMERIC, 1)      AS avg_ms,
  ROUND(stddev_exec_time::NUMERIC, 1)    AS stddev_ms,
  -- High stddev relative to mean = plan instability
  ROUND(stddev_exec_time /
    NULLIF(mean_exec_time, 0), 2)        AS cv_ratio,
  CASE
    WHEN stddev_exec_time > mean_exec_time
    THEN '🔴 UNSTABLE PLAN — sometimes fast, sometimes slow'
    WHEN stddev_exec_time > mean_exec_time * 0.5
    THEN '🟡 VARIABLE PLAN — investigate'
    ELSE '✅ STABLE'
  END                                    AS stability
FROM pg_stat_statements
WHERE calls > 50
ORDER BY cv_ratio DESC
LIMIT 20;
```

---

**8. Auto-Detecting Missing Index for Any Growing Query**

```sql
-- PostgreSQL
-- Run this after noticing a query getting slower
-- Tells you EXACTLY which index to create

-- Step 1: Find which queries are doing full scans on big tables
SELECT
  s.relname                              AS table_name,
  s.seq_scan                             AS full_scans,
  s.seq_tup_read                         AS rows_read_by_scans,
  s.idx_scan                             AS index_scans,
  n.n_live_tup                           AS total_rows,
  pg_size_pretty(pg_relation_size(s.relid)) AS table_size,
  -- Avg rows read per full scan
  ROUND(s.seq_tup_read::NUMERIC /
    NULLIF(s.seq_scan, 0))               AS avg_rows_per_scan,
  -- Cost of these scans
  ROUND(s.seq_tup_read::NUMERIC /
    1000000.0, 2)                        AS millions_of_rows_scanned
FROM pg_stat_user_tables s
JOIN pg_stat_user_tables n USING (relname)
WHERE s.seq_scan > 10                    -- getting scanned a lot
  AND n.n_live_tup > 100000             -- table is not tiny
  AND s.seq_scan > s.idx_scan           -- seq scans outnumber index scans
ORDER BY s.seq_tup_read DESC
LIMIT 20;

-- Step 2: For your specific slow query — find what columns to index
-- Run EXPLAIN and look for these patterns:

-- Pattern A: "Filter: (col = value)" under Seq Scan
-- → CREATE INDEX ON table (col);

-- Pattern B: "Filter: (col = v1 AND col2 = v2)"
-- → CREATE INDEX ON table (col, col2);  -- equality cols, most selective first

-- Pattern C: "Filter: (col > v)" under Seq Scan
-- → CREATE INDEX ON table (col);

-- Pattern D: "Sort: col DESC" after Seq Scan
-- → CREATE INDEX ON table (col DESC);   -- index sort matches query sort

-- Pattern E: "Index Scan" + "Heap Fetches: 10000"
-- → CREATE INDEX ON table (col) INCLUDE (selected_col1, selected_col2);

-- Generic index creation template:
CREATE INDEX CONCURRENTLY IF NOT EXISTS
  idx_{tablename}_{col1}_{col2}          -- naming convention
ON your_table (
  equality_col,                          -- WHERE col = ?   (most selective first)
  range_col,                             -- WHERE col > ?   (range after equality)
  sort_col DESC                          -- ORDER BY col DESC
)
INCLUDE (
  select_col1,                           -- columns in SELECT only
  select_col2
)
WHERE filter_col = 'constant_value';     -- partial: only when filter is constant
```

---

## 🔴 PROBLEM 3: WORKS FINE ALONE, SLOW UNDER CONCURRENT LOAD

**Why it happens:** Locks, connection pool exhaustion, hot rows, shared buffer contention.

---

**9. Complete Concurrent Load Diagnosis — One Query**

```sql
-- PostgreSQL
-- Run this WHILE the system is under load
-- Shows everything: locks, waits, idle connections, long transactions

SELECT
  pid,
  state,
  wait_event_type,
  wait_event,
  -- How long has this been running/waiting?
  ROUND(EXTRACT(EPOCH FROM
    NOW() - COALESCE(query_start, backend_start)))   AS age_secs,
  -- Transaction age (long txn = holding locks)
  ROUND(EXTRACT(EPOCH FROM
    NOW() - xact_start))                             AS txn_age_secs,
  -- Is this blocking others?
  CARDINALITY(pg_blocking_pids(pid)) > 0             AS is_being_blocked,
  pg_blocking_pids(pid)                              AS blocked_by_pids,
  -- Is this blocking others?
  (SELECT COUNT(*) FROM pg_stat_activity a2
   WHERE pid = ANY(pg_blocking_pids(a2.pid))
   GROUP BY pid LIMIT 1)                             AS blocking_n_others,
  application_name,
  client_addr,
  usename,
  LEFT(query, 150)                                   AS query_snippet,
  -- Classify the problem:
  CASE
    WHEN state = 'idle in transaction'
     AND xact_start < NOW() - INTERVAL '30 seconds'
    THEN '🔴 IDLE TXN — holding locks, kill it'
    WHEN wait_event_type = 'Lock'
    THEN '🔴 LOCK WAIT — blocked'
    WHEN state = 'active'
     AND query_start < NOW() - INTERVAL '30 seconds'
    THEN '🟡 LONG QUERY — investigate'
    WHEN wait_event_type = 'Client'
    THEN '🟡 WAITING FOR APP — app slow or dead'
    ELSE '✅ NORMAL'
  END                                                AS diagnosis
FROM pg_stat_activity
WHERE pid != pg_backend_pid()
  AND backend_type = 'client backend'
ORDER BY
  -- Show worst problems first
  CASE diagnosis
    WHEN '🔴 IDLE TXN — holding locks, kill it' THEN 1
    WHEN '🔴 LOCK WAIT — blocked'               THEN 2
    WHEN '🟡 LONG QUERY — investigate'          THEN 3
    ELSE 4
  END,
  age_secs DESC;
```

---

**10. Lock Chain Visualizer — Full Blocking Tree**

```sql
-- PostgreSQL
-- Shows the COMPLETE chain: who blocked whom blocked whom
-- Critical when one bad query blocks hundreds of others

WITH RECURSIVE lock_tree AS (
  -- Base: queries being blocked right now
  SELECT
    pid                                  AS blocked_pid,
    pg_blocking_pids(pid)                AS blocked_by,
    LEFT(query, 100)                     AS query,
    state,
    xact_start,
    ARRAY[pid]                           AS chain,
    1                                    AS depth,
    pid::TEXT                            AS tree_path
  FROM pg_stat_activity
  WHERE CARDINALITY(pg_blocking_pids(pid)) > 0
    AND pid != pg_backend_pid()

  UNION ALL

  -- Recurse: follow blockers up the chain
  SELECT
    sa.pid,
    pg_blocking_pids(sa.pid),
    LEFT(sa.query, 100),
    sa.state,
    sa.xact_start,
    lt.chain || sa.pid,
    lt.depth + 1,
    lt.tree_path || ' → ' || sa.pid::TEXT
  FROM lock_tree lt
  JOIN pg_stat_activity sa
    ON sa.pid = ANY(lt.blocked_by)
  WHERE sa.pid != ALL(lt.chain)    -- prevent cycles
    AND lt.depth < 10
)
SELECT
  REPEAT('  ', depth - 1) || '↳ PID ' ||
    blocked_pid::TEXT                    AS lock_tree,
  state,
  ROUND(EXTRACT(EPOCH FROM
    NOW() - xact_start))                AS txn_age_secs,
  query,
  tree_path,
  -- Root blocker = highest depth in chain = fix this first
  depth = MAX(depth) OVER ()            AS is_root_blocker
FROM lock_tree
ORDER BY tree_path;

-- Kill root blocker (get pid from is_root_blocker = TRUE above):
-- Safe cancel first (won't kill connection):
SELECT pg_cancel_backend(root_blocker_pid);
-- If cancel doesn't work after 10 seconds, terminate:
SELECT pg_terminate_backend(root_blocker_pid);
```

---

**11. Connection Pool Health Monitor**

```sql
-- PostgreSQL
-- Run this when app says "could not get connection from pool"

SELECT
  -- Connection state breakdown
  COUNT(*) FILTER (WHERE state = 'active')              AS active,
  COUNT(*) FILTER (WHERE state = 'idle')                AS idle,
  COUNT(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_txn,
  COUNT(*) FILTER (WHERE state = 'idle in transaction (aborted)') AS idle_aborted,
  COUNT(*)                                              AS total,
  -- Max connections allowed
  (SELECT setting::INT FROM pg_settings WHERE name = 'max_connections') AS max_allowed,
  -- How full is the pool?
  ROUND(100.0 * COUNT(*) /
    (SELECT setting::INT FROM pg_settings WHERE name = 'max_connections'), 1) AS pool_pct_used,
  -- Oldest transaction (sign of stuck connection)
  MAX(NOW() - xact_start)
    FILTER (WHERE xact_start IS NOT NULL)               AS oldest_txn_age,
  -- Worst wait
  MAX(NOW() - query_start)
    FILTER (WHERE state = 'active')                     AS longest_active_query,
  -- Which apps are using connections
  MODE() WITHIN GROUP (ORDER BY application_name)       AS top_app_name,
  -- How many apps are idle-in-txn (connection leak)
  COUNT(*) FILTER (
    WHERE state = 'idle in transaction'
      AND xact_start < NOW() - INTERVAL '1 minute'
  )                                                     AS leaked_connections
FROM pg_stat_activity
WHERE backend_type = 'client backend';

-- Break down by application (find connection hog):
SELECT
  application_name,
  COUNT(*)                                              AS connections,
  COUNT(*) FILTER (WHERE state = 'active')              AS active,
  COUNT(*) FILTER (WHERE state = 'idle in transaction') AS idle_in_txn,
  MAX(NOW() - xact_start)
    FILTER (WHERE xact_start IS NOT NULL)               AS longest_txn
FROM pg_stat_activity
WHERE backend_type = 'client backend'
GROUP BY application_name
ORDER BY connections DESC;

-- Kill leaked connections (idle-in-transaction > 5 minutes):
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND xact_start < NOW() - INTERVAL '5 minutes'
  AND pid != pg_backend_pid();
```

---

**12. Hot Row Contention Detector**

```sql
-- PostgreSQL
-- Finds which specific ROWS are causing lock contention
-- Critical for: inventory tables, counter tables, status fields

-- Find tables with most lock waits right now:
SELECT
  relation::REGCLASS                     AS table_name,
  locktype,
  mode,
  COUNT(*) FILTER (WHERE granted)        AS locks_held,
  COUNT(*) FILTER (WHERE NOT granted)    AS locks_waiting,
  -- Contention ratio: waiting / (held + waiting)
  ROUND(100.0 *
    COUNT(*) FILTER (WHERE NOT granted) /
    NULLIF(COUNT(*), 0), 1)             AS contention_pct
FROM pg_locks
WHERE relation IS NOT NULL
GROUP BY relation, locktype, mode
HAVING COUNT(*) FILTER (WHERE NOT granted) > 0
ORDER BY locks_waiting DESC;

-- See which specific transactions are in deadlock risk:
SELECT
  a.pid,
  a.state,
  a.wait_event_type,
  a.wait_event,
  l.locktype,
  l.relation::REGCLASS                   AS table_name,
  l.mode,
  l.granted,
  LEFT(a.query, 120)                     AS query
FROM pg_locks l
JOIN pg_stat_activity a ON a.pid = l.pid
WHERE l.granted = FALSE                  -- only waiting locks
ORDER BY a.query_start;

-- Fix: for hot counter rows, use this instead of UPDATE SET count = count + 1:
-- See Pattern #17 below (partitioned counter)
```

---

**13. Real-Time Throughput and Wait Analysis**

```sql
-- PostgreSQL
-- Shows what your database is spending time doing RIGHT NOW

SELECT
  wait_event_type,
  wait_event,
  COUNT(*)                               AS sessions,
  -- What percentage of active sessions are waiting
  ROUND(100.0 * COUNT(*) /
    NULLIF(SUM(COUNT(*)) OVER (), 0), 1) AS pct_of_sessions,
  -- What they're waiting for
  CASE wait_event_type
    WHEN 'Lock'     THEN '🔴 Row/table lock — find and kill blocker'
    WHEN 'LWLock'   THEN '🟡 Internal PG lock — may need tuning'
    WHEN 'IO'       THEN '🟡 Disk I/O — check indexes or add RAM'
    WHEN 'Client'   THEN '🟡 Waiting for app — app too slow to read results'
    WHEN 'CPU'      THEN '🟡 CPU bound — query doing too much work'
    ELSE                 '✅ Normal'
  END                                    AS meaning
FROM pg_stat_activity
WHERE state = 'active'
  AND pid != pg_backend_pid()
GROUP BY wait_event_type, wait_event
ORDER BY sessions DESC;

-- Database-level throughput (transactions per second):
SELECT
  datname,
  ROUND(xact_commit /
    GREATEST(EXTRACT(EPOCH FROM
      NOW() - stats_reset) / 60, 1))    AS commits_per_min,
  ROUND(xact_rollback /
    GREATEST(EXTRACT(EPOCH FROM
      NOW() - stats_reset) / 60, 1))    AS rollbacks_per_min,
  ROUND(100.0 * xact_rollback /
    NULLIF(xact_commit + xact_rollback, 0), 2) AS rollback_pct,
  ROUND(100.0 * blks_hit /
    NULLIF(blks_hit + blks_read, 0), 2) AS cache_hit_pct,
  deadlocks,
  temp_files,
  pg_size_pretty(temp_bytes)            AS temp_data_written
FROM pg_stat_database
WHERE datname = current_database();
```

---

## 🔴 PROBLEM 4: QUERY RUNS FAST IN DEV, SLOW IN PROD

**Why it happens:** Different data volume, different data distribution, different concurrent load, different statistics.

---

**14. Dev vs Prod Gap Finder**

```sql
-- PostgreSQL
-- Shows every factor that's different between dev and prod
-- Run in BOTH environments and compare output

SELECT
  -- Environment fingerprint
  current_database()                     AS database,
  version()                              AS pg_version,

  -- Data sizes (usually very different dev vs prod)
  (SELECT COUNT(*) FROM your_table)      AS row_count,
  pg_size_pretty(pg_total_relation_size('your_table')) AS total_size,

  -- Statistics quality
  (SELECT last_autoanalyze FROM pg_stat_user_tables
   WHERE relname = 'your_table')         AS last_analyze,
  (SELECT n_mod_since_analyze FROM pg_stat_user_tables
   WHERE relname = 'your_table')         AS rows_changed_since_analyze,

  -- Memory settings (huge impact on plan choice)
  (SELECT setting || 'kB'
   FROM pg_settings WHERE name = 'work_mem')          AS work_mem,
  (SELECT setting || 'kB'
   FROM pg_settings WHERE name = 'shared_buffers')    AS shared_buffers,
  (SELECT setting
   FROM pg_settings WHERE name = 'effective_cache_size') AS effective_cache_size,

  -- Planner cost settings (different settings = different plans)
  (SELECT setting
   FROM pg_settings WHERE name = 'random_page_cost')  AS random_page_cost,
  (SELECT setting
   FROM pg_settings WHERE name = 'seq_page_cost')     AS seq_page_cost,

  -- Indexes present
  (SELECT COUNT(*) FROM pg_indexes
   WHERE tablename = 'your_table')       AS index_count,

  -- Column statistics depth
  (SELECT AVG(attstattarget)
   FROM pg_attribute a
   JOIN pg_class c ON c.oid = a.attrelid
   WHERE c.relname = 'your_table'
     AND a.attnum > 0)                   AS avg_stats_target;

-- Common fixes when dev is faster than prod:
-- 1. Stats stale in prod:  ANALYZE your_table;
-- 2. random_page_cost too high in prod: SET random_page_cost = 1.1; (SSD)
-- 3. work_mem too low in prod: SET LOCAL work_mem = '256MB'; (per session)
-- 4. Missing index in prod: check pg_indexes on both environments
-- 5. effective_cache_size wrong: SET effective_cache_size = '24GB'; (75% of RAM)
```

---

**15. One-Command Query Tuning Checklist**

```sql
-- PostgreSQL
-- Run this on any slow query — gives you a prioritized action list

-- Step 1: Capture execution stats
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
your_slow_query_here;

-- Step 2: This query reads the plan and diagnoses problems
-- (saves you from reading raw EXPLAIN output)

DO $$
DECLARE
  v_plan   JSON;
  v_result TEXT := '';
BEGIN
  EXECUTE $q$
    EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
    SELECT 1 FROM your_table WHERE your_col = 'test'   -- ← your query
  $q$ INTO v_plan;

  -- Check for Seq Scan
  IF v_plan::TEXT ILIKE '%Seq Scan%' THEN
    v_result := v_result || '🔴 SEQ SCAN found — check for missing index' || E'\n';
  END IF;

  -- Check for disk sort
  IF v_plan::TEXT ILIKE '%Sort Method: external%' THEN
    v_result := v_result || '🔴 DISK SORT — increase work_mem: SET LOCAL work_mem = ''256MB'';' || E'\n';
  END IF;

  -- Check for hash batch spill
  IF v_plan::TEXT ILIKE '%Batches: [^1]%' THEN
    v_result := v_result || '🔴 HASH SPILL — increase work_mem for this session' || E'\n';
  END IF;

  -- Check for nested loop on big table
  IF v_plan::TEXT ILIKE '%Nested Loop%' THEN
    v_result := v_result || '🟡 NESTED LOOP — verify outer table is small (<1000 rows)' || E'\n';
  END IF;

  -- Check for heap fetches
  IF v_plan::TEXT ILIKE '%Heap Fetches%' THEN
    v_result := v_result || '🟡 HEAP FETCHES — add INCLUDE columns to your index' || E'\n';
  END IF;

  IF v_result = '' THEN
    v_result := '✅ Plan looks reasonable. Check stats freshness next.';
  END IF;

  RAISE NOTICE E'\n=== QUERY DIAGNOSIS ===\n%', v_result;
END $$;

-- Step 3: Force prod-like conditions in dev to reproduce the slow plan:
SET work_mem = '4MB';              -- simulate low prod work_mem
SET random_page_cost = 4;          -- simulate HDD (higher = prefers seq scan)
SET effective_cache_size = '512MB'; -- simulate low prod cache
-- Now re-run EXPLAIN — should reproduce prod plan
```

---

**16. Index Decision Framework — 5 Questions Before Creating Any Index**

```sql
-- PostgreSQL
-- Answer these 5 questions before creating any index
-- Replace 'your_table' and 'your_col' throughout

-- QUESTION 1: Is the table big enough for an index to matter?
SELECT
  relname,
  reltuples::BIGINT                      AS est_rows,
  pg_size_pretty(pg_relation_size(oid))  AS table_size,
  CASE
    WHEN reltuples < 1000    THEN '🚫 TOO SMALL — index wont help, seq scan is faster'
    WHEN reltuples < 100000  THEN '🟡 SMALL — index may help for exact lookups only'
    ELSE                          '✅ BIG ENOUGH — index will help'
  END                                    AS verdict
FROM pg_class
WHERE relname = 'your_table'
  AND relkind = 'r';

-- QUESTION 2: Is the column selective enough?
SELECT
  COUNT(DISTINCT your_col)::FLOAT /
    COUNT(*)                             AS selectivity,
  CASE
    WHEN COUNT(DISTINCT your_col)::FLOAT / COUNT(*) > 0.1
    THEN '✅ SELECTIVE — index will help'
    WHEN COUNT(DISTINCT your_col)::FLOAT / COUNT(*) > 0.01
    THEN '🟡 MODERATE — helps for rare values, not common ones'
    ELSE '🚫 NOT SELECTIVE — index wont help (full scan faster)'
  END                                    AS verdict
FROM your_table;

-- QUESTION 3: How often is this query actually run?
SELECT
  calls,
  ROUND(mean_exec_time::NUMERIC, 1)      AS avg_ms,
  ROUND(total_exec_time::NUMERIC / 1000) AS total_secs,
  LEFT(query, 100)
FROM pg_stat_statements
WHERE query ILIKE '%your_table%'
  AND query ILIKE '%your_col%'
ORDER BY total_exec_time DESC
LIMIT 5;
-- If total_secs is low: index won't move the needle
-- If total_secs is high AND avg_ms is high: index critical

-- QUESTION 4: Will this index be maintained for free?
-- Estimate write overhead of adding an index:
SELECT
  (SELECT SUM(n_tup_ins + n_tup_upd + n_tup_del)
   FROM pg_stat_user_tables
   WHERE relname = 'your_table')         AS total_write_ops,
  -- Each index adds one write per DML operation
  -- Rule: if write_ops > 10x read_ops, think twice about the index
  (SELECT SUM(idx_scan) FROM pg_stat_user_indexes
   WHERE relname = 'your_table')         AS total_index_scans,
  (SELECT COUNT(*) FROM pg_indexes
   WHERE tablename = 'your_table')       AS current_index_count;

-- QUESTION 5: Does a similar index already exist?
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'your_table'
  AND indexdef ILIKE '%your_col%';
-- If yes: extend the existing index with INCLUDE instead of creating new one

-- DECISION SUMMARY:
-- rows > 100K AND selectivity > 1% AND total_secs > 60 AND no similar index exists
-- → CREATE INDEX
-- Otherwise → investigate other causes first
```

---

## 🔴 PART 5: GENERIC PATTERNS — COPY AND ADAPT

---

**17. Generic Safe Counter Update — Replaces Any Hot Row UPDATE**

```sql
-- Use instead of: UPDATE table SET count = count + 1 WHERE id = X
-- Works for: view counters, inventory, rate limiters, any high-write counter

-- Schema (works with your existing table if it has these concepts):
-- your_counter_table(entity_id, slot_id, count)

-- Write (each caller picks random slot — distributes lock contention):
INSERT INTO your_counter_table (entity_id, slot_id, count)
VALUES (
  $entity_id,
  (random() * 31)::INT,   -- 32 slots (0–31): tune up for higher concurrency
  $increment_amount
)
ON CONFLICT (entity_id, slot_id) DO UPDATE
  SET count = your_counter_table.count + EXCLUDED.count;

-- Read (aggregate slots — ~32 rows, always fast):
SELECT
  entity_id,
  SUM(count) AS total_count
FROM your_counter_table
WHERE entity_id = $entity_id
GROUP BY entity_id;

-- Read multiple entities at once (batch read):
SELECT
  entity_id,
  SUM(count) AS total_count
FROM your_counter_table
WHERE entity_id = ANY($entity_ids::BIGINT[])
GROUP BY entity_id;

-- Compact periodically (optional, collapses 32 slots back to 1):
WITH total AS (
  SELECT entity_id, SUM(count) AS total
  FROM your_counter_table
  WHERE entity_id = $entity_id
  GROUP BY entity_id
),
deleted AS (
  DELETE FROM your_counter_table WHERE entity_id = $entity_id
)
INSERT INTO your_counter_table (entity_id, slot_id, count)
SELECT entity_id, 0, total FROM total;

-- Required index:
CREATE UNIQUE INDEX ON your_counter_table (entity_id, slot_id);
```
**Replaces:** Any `UPDATE SET count = count + 1` pattern. Scales from 500 TPS to 16,000 TPS by eliminating the single hot row bottleneck.

---

**18. Generic Deduplication Query — Any Table, Any Key**

```sql
-- Use when: table has duplicates on some business key
-- Safe: find first, delete second (never deletes all copies)

-- Step 1: Count duplicates (always look before deleting)
SELECT
  your_unique_key_col,           -- the column that SHOULD be unique
  COUNT(*) AS copies,
  MIN(id) AS keep_this_id,       -- oldest = keep
  MAX(id) AS delete_this_id,     -- newest duplicate = delete
  MIN(created_at) AS first_seen,
  MAX(created_at) AS last_seen
FROM your_table
GROUP BY your_unique_key_col
HAVING COUNT(*) > 1
ORDER BY copies DESC
LIMIT 50;                        -- look at worst offenders first

-- Step 2: Delete duplicates (keep earliest by id)
-- PostgreSQL (fastest):
DELETE FROM your_table a
USING (
  SELECT MIN(id) AS keep_id
  FROM your_table
  GROUP BY your_unique_key_col
) b
WHERE a.id != b.keep_id
  AND a.your_unique_key_col IN (
    SELECT your_unique_key_col
    FROM your_table
    GROUP BY your_unique_key_col
    HAVING COUNT(*) > 1
  );

-- MySQL (subquery approach):
DELETE FROM your_table
WHERE id NOT IN (
  SELECT keep_id FROM (
    SELECT MIN(id) AS keep_id
    FROM your_table
    GROUP BY your_unique_key_col
  ) AS keepers
);

-- SQL Server:
WITH cte AS (
  SELECT id,
    ROW_NUMBER() OVER (
      PARTITION BY your_unique_key_col
      ORDER BY id ASC         -- keep lowest id
    ) AS rn
  FROM your_table
)
DELETE FROM cte WHERE rn > 1;

-- Step 3: Prevent future duplicates
CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS
  idx_your_table_unique_key
ON your_table (your_unique_key_col);
```

---

**19. Generic Top-N Per Group — Any Table**

```sql
-- Use for: latest order per user, best score per player,
--          most recent login per device, top product per category

-- PostgreSQL (fastest — DISTINCT ON):
SELECT DISTINCT ON (group_col)    -- change group_col
  *                               -- or list specific columns
FROM your_table
WHERE status_col = 'active'       -- your filter (optional)
ORDER BY
  group_col,                      -- must be first in ORDER BY with DISTINCT ON
  sort_col DESC;                  -- highest/latest value wins

-- All engines (ROW_NUMBER approach — top N per group):
WITH ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY group_col      -- one ranking per group value
      ORDER BY sort_col DESC      -- highest sort_col = rank 1
    ) AS rn
  FROM your_table
  WHERE status_col = 'active'     -- filter inside: faster than filtering after
)
SELECT *
FROM ranked
WHERE rn <= 3;                    -- change 3 to any N you need

-- Required index (without this, full sort per group):
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topn
ON your_table (group_col, sort_col DESC)
INCLUDE (col1, col2, col3);      -- add all columns you SELECT
-- With this index: each group is a short range scan, no sort needed
```

---

**20. Generic Incremental Aggregation — Any Fact Table**

```sql
-- Use for: daily/weekly summaries, reporting tables, dashboards
-- Pattern: only process NEW rows since last run (not all rows every time)

-- Required: a watermark tracking table
-- (if you can't create tables, use a config row in an existing table)
CREATE TABLE IF NOT EXISTS job_watermarks (
  job_name    TEXT PRIMARY KEY,
  last_max_id BIGINT  DEFAULT 0,
  last_run_at TIMESTAMPTZ,
  rows_processed BIGINT DEFAULT 0
);

-- Initialize:
INSERT INTO job_watermarks (job_name) VALUES ('your_summary_job')
ON CONFLICT DO NOTHING;

-- The incremental aggregation job:
DO $$
DECLARE
  v_last_id   BIGINT;
  v_max_id    BIGINT;
  v_rows      INT;
BEGIN
  -- Get watermark
  SELECT last_max_id INTO v_last_id
  FROM job_watermarks WHERE job_name = 'your_summary_job';

  -- Get new max (5-min buffer to avoid in-flight rows)
  SELECT COALESCE(MAX(id), v_last_id) INTO v_max_id
  FROM your_source_table
  WHERE created_at < NOW() - INTERVAL '5 minutes';

  EXIT WHEN v_max_id = v_last_id;  -- nothing new

  -- Aggregate ONLY new rows (not the full table):
  INSERT INTO your_summary_table (
    group_col,
    time_bucket,
    total_count,
    total_amount,
    updated_at
  )
  SELECT
    group_col,
    DATE_TRUNC('day', created_at)  AS time_bucket,   -- or 'hour', 'week', 'month'
    COUNT(*)                       AS total_count,
    SUM(amount_col)                AS total_amount,
    NOW()
  FROM your_source_table
  WHERE id > v_last_id             -- ONLY new rows
    AND id <= v_max_id
  GROUP BY group_col, DATE_TRUNC('day', created_at)
  ON CONFLICT (group_col, time_bucket) DO UPDATE SET
    total_count  = your_summary_table.total_count  + EXCLUDED.total_count,
    total_amount = your_summary_table.total_amount + EXCLUDED.total_amount,
    updated_at   = NOW();

  GET DIAGNOSTICS v_rows = ROW_COUNT;

  -- Advance watermark
  UPDATE job_watermarks SET
    last_max_id    = v_max_id,
    last_run_at    = NOW(),
    rows_processed = rows_processed + v_rows
  WHERE job_name = 'your_summary_job';

  RAISE NOTICE 'Processed IDs % to %, aggregated % summary rows',
    v_last_id, v_max_id, v_rows;
END $$;

-- Required index on source table:
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_source_watermark
ON your_source_table (id, created_at)
INCLUDE (group_col, amount_col);  -- covering: no heap fetch for aggregation
```

---

## Quick Reference Card — Paste Into Any Investigation

```sql
-- ① WHAT IS SLOW RIGHT NOW?
SELECT pid, now()-query_start AS age, wait_event, LEFT(query,100)
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < now() - INTERVAL '3 seconds'
ORDER BY query_start;

-- ② WHAT IS BLOCKING WHAT?
SELECT blocked.pid, LEFT(ba.query,80) AS blocked_q,
       blocking.pid AS blocker, LEFT(bla.query,80) AS blocker_q
FROM pg_locks blocked
JOIN pg_stat_activity ba  ON ba.pid  = blocked.pid
JOIN pg_locks blocking    ON blocking.relation = blocked.relation
                         AND blocking.granted  = TRUE
                         AND blocking.pid     != blocked.pid
JOIN pg_stat_activity bla ON bla.pid = blocking.pid
WHERE blocked.granted = FALSE;

-- ③ WHERE DOES DB TIME GO?
SELECT LEFT(query,100), calls,
       ROUND(mean_exec_time::NUMERIC,1) AS avg_ms,
       ROUND(100.0*total_exec_time/SUM(total_exec_time) OVER(),2) AS pct_db_time
FROM pg_stat_statements WHERE calls > 10
ORDER BY total_exec_time DESC LIMIT 10;

-- ④ WHICH INDEXES ARE UNUSED?
SELECT indexname, pg_size_pretty(pg_relation_size(indexrelid::REGCLASS)) AS size
FROM pg_stat_user_indexes WHERE idx_scan = 0 AND schemaname = 'public';

-- ⑤ WHICH TABLES NEED VACUUM/ANALYZE?
SELECT relname, n_dead_tup, n_live_tup,
       ROUND(100.0*n_dead_tup/NULLIF(n_live_tup+n_dead_tup,0),1) AS dead_pct
FROM pg_stat_user_tables WHERE n_dead_tup > 10000 ORDER BY dead_pct DESC;

-- ⑥ IS MY INDEX BEING USED?
SELECT idx_scan, idx_tup_read FROM pg_stat_user_indexes
WHERE indexrelname = 'your_index_name';

-- ⑦ KILL IDLE-IN-TRANSACTION CONNECTIONS (run when pool exhausted):
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND xact_start < NOW() - INTERVAL '5 minutes';

-- ⑧ CURRENT CACHE HIT RATE (below 95% = need more RAM or better indexes):
SELECT ROUND(100.0*blks_hit/NULLIF(blks_hit+blks_read,0),2) AS cache_hit_pct
FROM pg_stat_database WHERE datname = current_database();

-- ⑨ TABLE + INDEX SIZE:
SELECT pg_size_pretty(pg_relation_size('t')) AS table,
       pg_size_pretty(pg_indexes_size('t'))  AS indexes,
       pg_size_pretty(pg_total_relation_size('t')) AS total;

-- ⑩ ESTIMATED ROW COUNT (instant, no COUNT(*) scan):
SELECT reltuples::BIGINT FROM pg_class WHERE relname = 'your_table';
```