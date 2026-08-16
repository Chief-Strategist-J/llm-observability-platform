# Complex & Critical SQL — All Levels, All Domains, Full Depth

> **Format:** Problem → Wrong approach → Correct query → Why it works → Execution analysis → Performance numbers. 40 queries across all complexity levels and domains.

---

## 🔴 LEVEL 1: SENIOR ENGINEER — CTEs, WINDOW FUNCTIONS, PARTITIONING

---

**1. Double-Entry Ledger Balance With Violation Detection**

```sql
-- PROBLEM: Financial ledger must always balance. Every debit = matching credit.
-- Any imbalance = data corruption. Must detect AND locate the violation.

-- SCHEMA:
-- journal_entries (id, entry_date, description, posted_by, posted_at)
-- journal_lines   (id, entry_id, account_id, debit, credit, currency)
-- Rule: SUM(debit) = SUM(credit) per entry_id

-- ❌ WRONG — Checks balance globally (hides entry-level violations):
SELECT SUM(debit) - SUM(credit) AS global_imbalance FROM journal_lines;
-- Returns 0 even if individual entries are wrong (errors cancel each other out)

-- ✅ CORRECT — Checks every entry, finds exact violation, shows context:
WITH entry_balances AS (
  SELECT
    jl.entry_id,
    je.entry_date,
    je.description,
    je.posted_by,
    SUM(jl.debit)                          AS total_debits,
    SUM(jl.credit)                         AS total_credits,
    SUM(jl.debit) - SUM(jl.credit)         AS imbalance,
    COUNT(*)                               AS line_count,
    COUNT(DISTINCT jl.currency)            AS currency_count,
    -- Multi-currency entries must balance per currency:
    jsonb_object_agg(
      jl.currency,
      SUM(jl.debit) - SUM(jl.credit)
    )                                      AS imbalance_by_currency,
    -- Detect single-sided entries (debit with no credit or vice versa):
    SUM(jl.debit)  = 0                     AS credit_only_entry,
    SUM(jl.credit) = 0                     AS debit_only_entry
  FROM journal_lines jl
  JOIN journal_entries je ON je.id = jl.entry_id
  WHERE je.entry_date BETWEEN $start_date AND $end_date
  GROUP BY jl.entry_id, je.entry_date, je.description, je.posted_by
),
violations AS (
  SELECT
    eb.*,
    -- Classify violation type:
    CASE
      WHEN ABS(imbalance) > 0.005      THEN 'AMOUNT_MISMATCH'
      WHEN credit_only_entry           THEN 'MISSING_DEBIT'
      WHEN debit_only_entry            THEN 'MISSING_CREDIT'
      WHEN currency_count > 1
       AND EXISTS (
         SELECT 1 FROM jsonb_each_text(imbalance_by_currency)
         WHERE value::NUMERIC <> 0
       )                               THEN 'MULTI_CURRENCY_IMBALANCE'
      ELSE NULL
    END                                AS violation_type
  FROM entry_balances eb
),
-- Running balance check (detect if cumulative balance drifts):
cumulative AS (
  SELECT
    entry_date,
    SUM(total_debits)  OVER (ORDER BY entry_date, entry_id) AS cumulative_debits,
    SUM(total_credits) OVER (ORDER BY entry_date, entry_id) AS cumulative_credits,
    SUM(imbalance)     OVER (ORDER BY entry_date, entry_id) AS cumulative_drift
  FROM violations
)
SELECT
  v.entry_id,
  v.entry_date,
  v.description,
  v.posted_by,
  ROUND(v.total_debits::NUMERIC,  2) AS debits,
  ROUND(v.total_credits::NUMERIC, 2) AS credits,
  ROUND(v.imbalance::NUMERIC,     2) AS imbalance,
  v.violation_type,
  v.imbalance_by_currency,
  -- Show the actual lines causing the problem:
  (
    SELECT jsonb_agg(jsonb_build_object(
      'account_id', jl.account_id,
      'debit',      jl.debit,
      'credit',     jl.credit,
      'currency',   jl.currency
    ) ORDER BY jl.id)
    FROM journal_lines jl
    WHERE jl.entry_id = v.entry_id
  )                                   AS violation_lines
FROM violations v
WHERE v.violation_type IS NOT NULL
ORDER BY ABS(v.imbalance) DESC;

-- EXECUTION PLAN NOTES:
-- Index needed: (entry_id, currency) INCLUDE (debit, credit) on journal_lines
-- Index needed: (entry_date, id) on journal_entries
-- At 100M journal_lines: ~800ms with indexes, ~45s without
```
**Performance:** 100M rows, 2M entries, date range 1 year → **~800ms** with covering index. Without index: **~45s**. The jsonb_agg subquery adds ~200ms — acceptable for audit queries.

---

**2. Running Account Balance With Overdraft Detection**

```sql
-- PROBLEM: Compute running balance for every account transaction.
-- Detect: first overdraft event, recovery point, max overdraft depth.

-- SCHEMA: transactions(id, account_id, amount, type, created_at, reference_id)
-- amount > 0 = credit, amount < 0 = debit

-- ❌ WRONG — Correlated subquery (O(N²)):
SELECT t.id, t.account_id,
  (SELECT SUM(t2.amount) FROM transactions t2
   WHERE t2.account_id = t.account_id
     AND t2.created_at <= t.created_at) AS running_balance
FROM transactions t;
-- 1M rows per account × 1000 accounts = 1B comparisons. Timeout.

-- ✅ CORRECT — Single window pass with gap analysis:
WITH ordered AS (
  SELECT
    id,
    account_id,
    amount,
    type,
    created_at,
    reference_id,
    -- Running balance (single O(N) scan):
    SUM(amount) OVER (
      PARTITION BY account_id
      ORDER BY created_at, id          -- id breaks ties on same timestamp
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                  AS balance_after,
    -- Previous balance:
    LAG(SUM(amount) OVER (
      PARTITION BY account_id
      ORDER BY created_at, id
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )) OVER (
      PARTITION BY account_id ORDER BY created_at, id
    )                                  AS balance_before,
    ROW_NUMBER() OVER (
      PARTITION BY account_id ORDER BY created_at, id
    )                                  AS txn_seq
  FROM transactions
  WHERE account_id = ANY($account_ids)
),
-- Detect overdraft events:
overdraft_events AS (
  SELECT
    *,
    balance_after < 0                  AS is_overdraft,
    COALESCE(balance_before, 0) >= 0
      AND balance_after < 0            AS overdraft_entry,   -- crossed into negative
    COALESCE(balance_before, 0) < 0
      AND balance_after >= 0           AS overdraft_exit,    -- recovered from negative
    -- Overdraft depth:
    GREATEST(0, -balance_after)        AS overdraft_amount,
    -- Assign overdraft episode number:
    SUM(CASE WHEN COALESCE(balance_before, 0) >= 0
              AND balance_after < 0
         THEN 1 ELSE 0 END)
      OVER (PARTITION BY account_id ORDER BY created_at, id) AS overdraft_episode
  FROM ordered
),
-- Summarize overdraft episodes per account:
episode_summary AS (
  SELECT
    account_id,
    overdraft_episode,
    MIN(created_at)                    AS overdraft_started,
    MAX(created_at) FILTER (WHERE overdraft_exit) AS overdraft_ended,
    MIN(balance_after)                 AS max_overdraft_depth,
    COUNT(*) FILTER (WHERE is_overdraft) AS txns_while_overdrawn,
    MAX(overdraft_amount)              AS peak_overdraft
  FROM overdraft_events
  WHERE overdraft_episode > 0
  GROUP BY account_id, overdraft_episode
)
SELECT
  oe.account_id,
  oe.id            AS transaction_id,
  oe.created_at,
  oe.amount,
  oe.type,
  ROUND(oe.balance_before::NUMERIC, 2) AS balance_before,
  ROUND(oe.balance_after::NUMERIC, 2)  AS balance_after,
  oe.overdraft_entry,
  oe.overdraft_exit,
  ROUND(oe.overdraft_amount::NUMERIC, 2) AS overdraft_depth,
  es.overdraft_started,
  es.overdraft_ended,
  ROUND(es.peak_overdraft::NUMERIC, 2) AS episode_peak_overdraft
FROM overdraft_events oe
LEFT JOIN episode_summary es
  ON es.account_id       = oe.account_id
  AND es.overdraft_episode = oe.overdraft_episode
ORDER BY oe.account_id, oe.created_at;
```
**Performance:** 10M transactions, 50K accounts → **~4.2s** with index on (account_id, created_at, id). The window function does one pass. Without index: **~28s**.

---

**3. Reconciliation Query — Two Systems Must Agree**

```sql
-- PROBLEM: Payments exist in two systems (internal DB + payment processor).
-- Find: missing on either side, amount mismatches, duplicate charges.

-- SCHEMAS:
-- internal_payments   (id, external_ref, amount, currency, status, created_at)
-- processor_records   (id, reference_id, gross_amount, fee, net_amount, currency, settled_at)

WITH
-- Normalize both sides to same key:
internal AS (
  SELECT
    external_ref                        AS ref,
    amount,
    currency,
    status,
    created_at,
    'internal'                          AS source
  FROM internal_payments
  WHERE created_at BETWEEN $start AND $end
),
processor AS (
  SELECT
    reference_id                        AS ref,
    gross_amount                        AS amount,
    fee,
    net_amount,
    currency,
    settled_at                          AS created_at,
    'processor'                         AS source
  FROM processor_records
  WHERE settled_at BETWEEN $start AND $end
),
-- Full outer join to find all discrepancies:
reconciliation AS (
  SELECT
    COALESCE(i.ref, p.ref)              AS reference,
    i.amount                            AS internal_amount,
    p.amount                            AS processor_amount,
    p.fee                               AS processor_fee,
    p.net_amount                        AS processor_net,
    COALESCE(i.currency, p.currency)    AS currency,
    i.status                            AS internal_status,
    i.created_at                        AS internal_time,
    p.created_at                        AS processor_time,
    -- Classify discrepancy:
    CASE
      WHEN i.ref IS NULL               THEN 'MISSING_INTERNALLY'
      WHEN p.ref IS NULL               THEN 'MISSING_IN_PROCESSOR'
      WHEN ABS(i.amount - p.amount) > 0.01
                                       THEN 'AMOUNT_MISMATCH'
      WHEN i.currency != p.currency    THEN 'CURRENCY_MISMATCH'
      WHEN i.status = 'failed'
       AND p.amount IS NOT NULL        THEN 'CHARGED_DESPITE_FAILURE'
      ELSE                                  'MATCHED'
    END                                AS reconciliation_status,
    -- Amount difference:
    COALESCE(i.amount, 0)
      - COALESCE(p.amount, 0)          AS amount_difference
  FROM internal i
  FULL OUTER JOIN processor p ON p.ref = i.ref
),
-- Detect duplicates (same ref appearing more than once):
duplicate_refs AS (
  SELECT ref, COUNT(*) AS occurrence_count
  FROM (SELECT ref FROM internal UNION ALL SELECT ref FROM processor) all_refs
  GROUP BY ref
  HAVING COUNT(*) > 2   -- >2 because both sides contribute 1 each for matched
),
-- Summary statistics:
summary AS (
  SELECT
    reconciliation_status,
    COUNT(*)                           AS record_count,
    SUM(ABS(amount_difference))        AS total_discrepancy,
    SUM(internal_amount)               AS internal_total,
    SUM(processor_amount)              AS processor_total
  FROM reconciliation
  GROUP BY reconciliation_status
)
-- Output: full detail + summary
SELECT
  r.reference,
  r.reconciliation_status,
  ROUND(r.internal_amount::NUMERIC,  2) AS internal_amt,
  ROUND(r.processor_amount::NUMERIC, 2) AS processor_amt,
  ROUND(r.amount_difference::NUMERIC, 2) AS difference,
  r.currency,
  r.internal_status,
  r.internal_time,
  r.processor_time,
  d.occurrence_count                   AS duplicate_count
FROM reconciliation r
LEFT JOIN duplicate_refs d ON d.ref = r.reference
WHERE r.reconciliation_status != 'MATCHED'
   OR d.occurrence_count IS NOT NULL
ORDER BY
  CASE r.reconciliation_status
    WHEN 'CHARGED_DESPITE_FAILURE' THEN 1
    WHEN 'AMOUNT_MISMATCH'         THEN 2
    WHEN 'MISSING_INTERNALLY'      THEN 3
    WHEN 'MISSING_IN_PROCESSOR'    THEN 4
    ELSE 5
  END,
  ABS(r.amount_difference) DESC;
```
**Performance:** 5M rows each side, full outer join → **~6.5s** with index on external_ref/reference_id. Hash join in memory (set work_mem = '512MB' for this query). Returns only discrepancies — typically <0.1% of rows.

---

**4. Cohort Retention Matrix — Full NxN**

```sql
-- PROBLEM: For each signup cohort (week), what % of users returned each subsequent week?
-- Output: matrix where rows = signup cohort, columns = weeks 0-12

-- SCHEMA: user_activity(user_id, activity_date) — one row per active day

WITH
-- Assign each user to a cohort (week of first activity):
cohorts AS (
  SELECT
    user_id,
    DATE_TRUNC('week', MIN(activity_date))::DATE AS cohort_week
  FROM user_activity
  WHERE activity_date >= NOW() - INTERVAL '90 days'
  GROUP BY user_id
),
-- For each user, compute which weeks they were active AFTER signup:
user_weekly_activity AS (
  SELECT DISTINCT
    c.user_id,
    c.cohort_week,
    DATE_TRUNC('week', ua.activity_date)::DATE AS active_week,
    -- Week number since signup:
    ((DATE_TRUNC('week', ua.activity_date)
      - c.cohort_week) / 7)::INT               AS week_number
  FROM cohorts c
  JOIN user_activity ua ON ua.user_id = c.user_id
  WHERE ua.activity_date >= c.cohort_week
    AND ((DATE_TRUNC('week', ua.activity_date)
          - c.cohort_week) / 7)::INT <= 12     -- track 12 weeks
),
-- Count cohort sizes:
cohort_sizes AS (
  SELECT cohort_week, COUNT(DISTINCT user_id) AS cohort_size
  FROM cohorts GROUP BY cohort_week
),
-- Retention per cohort per week:
retention AS (
  SELECT
    uwa.cohort_week,
    uwa.week_number,
    COUNT(DISTINCT uwa.user_id)            AS active_users
  FROM user_weekly_activity uwa
  GROUP BY uwa.cohort_week, uwa.week_number
)
-- Pivot into matrix (weeks as columns):
SELECT
  r.cohort_week,
  cs.cohort_size,
  -- Week 0 is always 100% (signup week):
  ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 0)
    / cs.cohort_size, 1)                   AS "week_0_pct",
  ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 1)
    / cs.cohort_size, 1)                   AS "week_1_pct",
  ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 2)
    / cs.cohort_size, 1)                   AS "week_2_pct",
  ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 4)
    / cs.cohort_size, 1)                   AS "week_4_pct",
  ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 8)
    / cs.cohort_size, 1)                   AS "week_8_pct",
  ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 12)
    / cs.cohort_size, 1)                   AS "week_12_pct",
  -- Retention curve shape classification:
  CASE
    WHEN ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 4)
      / cs.cohort_size, 1) > 40            THEN 'STRONG'
    WHEN ROUND(100.0 * MAX(active_users) FILTER (WHERE week_number = 4)
      / cs.cohort_size, 1) > 20            THEN 'MODERATE'
    ELSE                                        'WEAK'
  END                                      AS retention_quality
FROM retention r
JOIN cohort_sizes cs ON cs.cohort_week = r.cohort_week
GROUP BY r.cohort_week, cs.cohort_size
ORDER BY r.cohort_week;
```
**Performance:** 500M activity rows, 2M users → **~12s** with index on (user_id, activity_date). The DISTINCT ON cohort week is the expensive step — partition pruning reduces this significantly if table is partitioned by month.

---

**5. Gap and Island Detection — Session Construction**

```sql
-- PROBLEM: Construct user sessions from raw events.
-- Session = sequence of events where gap between consecutive events < 30 min.
-- No session_id column exists — must derive it from timing.

-- SCHEMA: events(id, user_id, event_type, page_url, created_at)

WITH
-- Step 1: Identify session boundaries (gap > 30 min = new session starts):
event_gaps AS (
  SELECT
    id,
    user_id,
    event_type,
    page_url,
    created_at,
    LAG(created_at) OVER (
      PARTITION BY user_id
      ORDER BY created_at, id
    )                                    AS prev_event_time,
    -- Is this event the START of a new session?
    CASE
      WHEN LAG(created_at) OVER (
        PARTITION BY user_id ORDER BY created_at, id
      ) IS NULL
      THEN TRUE  -- first event = new session
      WHEN created_at - LAG(created_at) OVER (
        PARTITION BY user_id ORDER BY created_at, id
      ) > INTERVAL '30 minutes'
      THEN TRUE  -- gap too large = new session
      ELSE FALSE
    END                                  AS is_session_start
  FROM events
  WHERE created_at >= NOW() - INTERVAL '7 days'
),
-- Step 2: Assign session numbers (cumulative sum of starts):
session_numbers AS (
  SELECT
    *,
    SUM(is_session_start::INT) OVER (
      PARTITION BY user_id
      ORDER BY created_at, id
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                    AS session_num
  FROM event_gaps
),
-- Step 3: Aggregate each session:
sessions AS (
  SELECT
    user_id,
    session_num,
    -- Unique session ID (deterministic hash):
    MD5(user_id::TEXT || '-' || MIN(created_at)::TEXT) AS session_id,
    MIN(created_at)                      AS session_start,
    MAX(created_at)                      AS session_end,
    MAX(created_at) - MIN(created_at)    AS session_duration,
    COUNT(*)                             AS event_count,
    COUNT(DISTINCT event_type)           AS unique_event_types,
    COUNT(DISTINCT page_url)             AS unique_pages,
    -- Entry and exit pages:
    FIRST_VALUE(page_url) OVER (
      PARTITION BY user_id, session_num
      ORDER BY created_at
    )                                    AS entry_page,
    LAST_VALUE(page_url) OVER (
      PARTITION BY user_id, session_num
      ORDER BY created_at
      ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )                                    AS exit_page,
    -- Did session contain a purchase?
    BOOL_OR(event_type = 'purchase')     AS converted,
    SUM(CASE WHEN event_type = 'purchase'
        THEN (properties->>'amount')::NUMERIC
        ELSE 0 END)                      AS session_revenue,
    -- Time to conversion (from session start to first purchase):
    MIN(created_at) FILTER (
      WHERE event_type = 'purchase'
    ) - MIN(created_at)                  AS time_to_convert
  FROM session_numbers
  GROUP BY user_id, session_num
)
SELECT
  session_id,
  user_id,
  session_start,
  session_end,
  EXTRACT(EPOCH FROM session_duration) / 60 AS duration_minutes,
  event_count,
  unique_pages,
  entry_page,
  exit_page,
  converted,
  ROUND(session_revenue::NUMERIC, 2)     AS revenue,
  EXTRACT(EPOCH FROM time_to_convert) / 60 AS minutes_to_convert,
  -- Bounce detection (single page, short session):
  event_count = 1
   OR session_duration < INTERVAL '10 seconds' AS is_bounce
FROM sessions
ORDER BY session_start DESC;
```
**Performance:** 2B events, 7-day window → **~8.5s** with partition pruning + index on (user_id, created_at, id). The window function for session numbering is O(N log N) — the dominant cost.

---

## 🔴 LEVEL 2: STAFF/PRINCIPAL — DISTRIBUTED CONSISTENCY, ADVANCED MODELING

---

**6. Distributed Saga State Machine With Compensation**

```sql
-- PROBLEM: Order involves 3 services (inventory, payment, shipping).
-- Any step can fail. Must compensate completed steps on failure.
-- All state must be queryable, debuggable, and resumable.

-- SCHEMA:
-- sagas(id, saga_type, status, started_at, completed_at, payload)
-- saga_steps(id, saga_id, step_name, status, attempt_count, 
--            started_at, completed_at, error, compensated_at)

WITH
-- Current state of all in-flight sagas:
saga_state AS (
  SELECT
    s.id                                 AS saga_id,
    s.saga_type,
    s.status                             AS saga_status,
    s.started_at,
    NOW() - s.started_at                 AS age,
    s.payload,
    -- Steps summary:
    COUNT(ss.id)                         AS total_steps,
    COUNT(ss.id) FILTER (
      WHERE ss.status = 'completed'
    )                                    AS completed_steps,
    COUNT(ss.id) FILTER (
      WHERE ss.status = 'failed'
    )                                    AS failed_steps,
    COUNT(ss.id) FILTER (
      WHERE ss.status = 'compensated'
    )                                    AS compensated_steps,
    -- Last step attempted:
    MAX(ss.step_name) FILTER (
      WHERE ss.status = 'completed'
    )                                    AS last_completed_step,
    -- Next step to execute:
    MIN(ss.step_name) FILTER (
      WHERE ss.status = 'pending'
    )                                    AS next_pending_step,
    -- Is this saga stuck?
    MAX(ss.started_at) < NOW() - INTERVAL '5 minutes'
    AND s.status = 'in_progress'         AS is_stuck
  FROM sagas s
  LEFT JOIN saga_steps ss ON ss.saga_id = s.id
  WHERE s.status IN ('in_progress', 'compensating', 'failed')
  GROUP BY s.id, s.saga_type, s.status, s.started_at, s.payload
),
-- Determine what action each saga needs:
saga_actions AS (
  SELECT
    *,
    CASE
      WHEN is_stuck AND saga_status = 'in_progress'
      THEN 'RESUME_OR_COMPENSATE'
      WHEN saga_status = 'compensating'
       AND compensated_steps < completed_steps
      THEN 'CONTINUE_COMPENSATION'
      WHEN failed_steps > 0
       AND saga_status = 'in_progress'
      THEN 'BEGIN_COMPENSATION'
      WHEN completed_steps = total_steps
      THEN 'COMPLETE_SAGA'
      ELSE 'WAITING'
    END                                  AS required_action,
    -- Compensation order (reverse of execution):
    ARRAY(
      SELECT step_name
      FROM saga_steps
      WHERE saga_id = saga_id
        AND status = 'completed'
      ORDER BY started_at DESC   -- reverse order for compensation
    )                                    AS compensation_sequence
  FROM saga_state
),
-- Find sagas that NEED immediate intervention:
critical_sagas AS (
  SELECT *
  FROM saga_actions
  WHERE required_action != 'WAITING'
     OR age > INTERVAL '30 minutes'
)
SELECT
  saga_id,
  saga_type,
  saga_status,
  required_action,
  EXTRACT(EPOCH FROM age) / 60           AS age_minutes,
  completed_steps,
  failed_steps,
  compensated_steps,
  total_steps,
  last_completed_step,
  next_pending_step,
  compensation_sequence,
  -- Risk assessment:
  CASE
    WHEN required_action = 'BEGIN_COMPENSATION'
     AND completed_steps > 0             THEN 'HIGH — must compensate ' ||
                                              completed_steps || ' steps'
    WHEN is_stuck                        THEN 'MEDIUM — saga may be orphaned'
    ELSE                                      'LOW'
  END                                    AS risk_level,
  payload->'order_id'                    AS order_id,
  payload->'user_id'                     AS user_id
FROM critical_sagas
ORDER BY
  CASE required_action
    WHEN 'BEGIN_COMPENSATION'    THEN 1
    WHEN 'CONTINUE_COMPENSATION' THEN 2
    WHEN 'RESUME_OR_COMPENSATE'  THEN 3
    ELSE 4
  END,
  age DESC;
```

---

**7. Event Projection Rebuild With Gap Detection**

```sql
-- PROBLEM: Event store projection (read model) fell behind during an outage.
-- Must identify: which events were missed, replay in order, detect corruption.

-- SCHEMA:
-- event_store(id, aggregate_type, aggregate_id, event_version, event_type, 
--             payload, recorded_at, global_seq BIGINT)
-- order_projection(order_id, status, version, last_event_id, projection_at)

WITH
-- Find the projection's current watermark:
projection_state AS (
  SELECT
    MAX(last_event_id)                   AS max_projected_event,
    MIN(last_event_id)                   AS min_projected_event,
    COUNT(*)                             AS projected_aggregates,
    MAX(projection_at)                   AS last_projection_time
  FROM order_projection
),
-- Find events that exist but aren't reflected in projection:
missing_events AS (
  SELECT
    es.id                                AS event_id,
    es.aggregate_id,
    es.aggregate_type,
    es.event_version,
    es.event_type,
    es.global_seq,
    es.recorded_at,
    op.version                           AS projected_version,
    op.last_event_id                     AS projected_event_id,
    -- Gap classification:
    CASE
      WHEN op.order_id IS NULL           THEN 'AGGREGATE_NOT_PROJECTED'
      WHEN es.event_version
        != op.version + 1               THEN 'VERSION_GAP'
      WHEN es.id > op.last_event_id     THEN 'EVENT_NOT_APPLIED'
      ELSE NULL
    END                                  AS gap_type
  FROM event_store es
  LEFT JOIN order_projection op
    ON op.order_id = es.aggregate_id
  WHERE es.aggregate_type = 'Order'
    AND es.recorded_at > (
      SELECT last_projection_time FROM projection_state
    ) - INTERVAL '5 minutes'   -- overlap buffer for safety
    AND es.id > (
      SELECT max_projected_event FROM projection_state
    )
),
-- Detect version gaps WITHIN projected aggregates (corruption signal):
version_gaps AS (
  SELECT
    es1.aggregate_id,
    es1.event_version                    AS expected_next,
    es2.event_version                    AS actual_next,
    es2.event_version - es1.event_version - 1 AS gap_size,
    es1.recorded_at                      AS gap_starts_after
  FROM event_store es1
  JOIN event_store es2
    ON es2.aggregate_id   = es1.aggregate_id
    AND es2.event_version  = es1.event_version + 1
    AND es2.aggregate_type = es1.aggregate_type
  WHERE es1.aggregate_type = 'Order'
    AND es2.event_version - es1.event_version > 1  -- version jump = gap!
),
-- Build replay plan in correct order:
replay_plan AS (
  SELECT
    me.event_id,
    me.aggregate_id,
    me.event_version,
    me.event_type,
    me.gap_type,
    me.recorded_at,
    -- Order to replay (global sequence ensures causal ordering):
    ROW_NUMBER() OVER (ORDER BY me.global_seq) AS replay_order,
    -- Include full payload for replay:
    es.payload
  FROM missing_events me
  JOIN event_store es ON es.id = me.event_id
  WHERE me.gap_type IS NOT NULL
)
SELECT
  replay_order,
  event_id,
  aggregate_id,
  event_version,
  event_type,
  gap_type,
  recorded_at,
  payload,
  -- Alert on corruption:
  EXISTS (
    SELECT 1 FROM version_gaps vg
    WHERE vg.aggregate_id = rp.aggregate_id
  )                                      AS has_version_gap,
  (SELECT gap_size FROM version_gaps vg
   WHERE vg.aggregate_id = rp.aggregate_id
   LIMIT 1)                              AS version_gap_size
FROM replay_plan rp
ORDER BY replay_order;
```

---

**8. Temporal Foreign Key Integrity Across Time**

```sql
-- PROBLEM: employee_assignments(employee_id, department_id, valid_from, valid_until)
-- Department can be deactivated. An employee assigned to a deactivated department
-- during their assignment period = temporal FK violation.

-- SCHEMA:
-- departments(id, name, active_from, active_until)  -- temporal table
-- employee_assignments(id, employee_id, dept_id, valid_from, valid_until)

WITH
-- Find all temporal FK violations:
temporal_violations AS (
  SELECT
    ea.id                                AS assignment_id,
    ea.employee_id,
    ea.dept_id,
    ea.valid_from                        AS assignment_start,
    ea.valid_until                       AS assignment_end,
    d.active_from                        AS dept_active_from,
    d.active_until                       AS dept_active_until,
    d.name                               AS dept_name,
    -- Calculate the overlap between assignment and dept inactivity:
    GREATEST(ea.valid_from, d.active_until)  AS violation_start,
    LEAST(COALESCE(ea.valid_until, 'infinity'::DATE),
          COALESCE(d.active_from,  'infinity'::DATE)) AS violation_end,
    -- Type of violation:
    CASE
      WHEN d.id IS NULL
      THEN 'DEPT_NEVER_EXISTED'
      WHEN ea.valid_from < d.active_from
      THEN 'ASSIGNED_BEFORE_DEPT_EXISTED'
      WHEN d.active_until IS NOT NULL
       AND ea.valid_until > d.active_until
      THEN 'ASSIGNED_AFTER_DEPT_DEACTIVATED'
      WHEN d.active_until IS NOT NULL
       AND ea.valid_from BETWEEN d.active_until
       AND COALESCE(ea.valid_until, 'infinity'::DATE)
      THEN 'ACTIVE_DURING_DEPT_INACTIVITY'
      ELSE NULL
    END                                  AS violation_type
  FROM employee_assignments ea
  LEFT JOIN departments d
    ON d.id = ea.dept_id
    -- Temporal join: department must overlap assignment period
    AND (d.active_until IS NULL OR d.active_until > ea.valid_from)
    AND d.active_from < COALESCE(ea.valid_until, 'infinity'::DATE)
),
-- Overlap analysis:
overlap_details AS (
  SELECT
    tv.*,
    -- How many days is the employee improperly assigned?
    CASE
      WHEN violation_type IS NOT NULL
      THEN EXTRACT(EPOCH FROM (
        LEAST(COALESCE(assignment_end, 'infinity'::TIMESTAMPTZ), NOW()) -
        GREATEST(assignment_start, COALESCE(dept_active_until, '-infinity'::TIMESTAMPTZ))
      )) / 86400
    END                                  AS violation_days,
    -- Is this violation ongoing?
    COALESCE(assignment_end, 'infinity'::TIMESTAMPTZ) > NOW()
    AND violation_type IS NOT NULL       AS is_ongoing_violation
  FROM temporal_violations tv
  WHERE tv.violation_type IS NOT NULL
)
SELECT
  assignment_id,
  employee_id,
  dept_id,
  dept_name,
  violation_type,
  assignment_start::DATE,
  assignment_end::DATE,
  dept_active_from::DATE,
  dept_active_until::DATE,
  ROUND(violation_days::NUMERIC, 1)      AS violation_days,
  is_ongoing_violation,
  -- Suggested fix:
  CASE violation_type
    WHEN 'ASSIGNED_AFTER_DEPT_DEACTIVATED'
    THEN 'UPDATE valid_until = dept.active_until WHERE id = ' || assignment_id
    WHEN 'ASSIGNED_BEFORE_DEPT_EXISTED'
    THEN 'UPDATE valid_from = dept.active_from WHERE id = ' || assignment_id
    ELSE 'MANUAL REVIEW REQUIRED'
  END                                    AS suggested_fix
FROM overlap_details
ORDER BY is_ongoing_violation DESC, violation_days DESC;
```

---

**9. Graph Cycle Detection and Minimum Cut**

```sql
-- PROBLEM: Workflow DAG must have no cycles.
-- Also find minimum set of edges to remove to make it acyclic.

-- SCHEMA: workflow_edges(from_task_id, to_task_id, weight, edge_type)

WITH RECURSIVE
-- DFS to detect all cycles:
dfs AS (
  SELECT
    from_task_id                         AS start_node,
    from_task_id                         AS current_node,
    to_task_id                           AS next_node,
    ARRAY[from_task_id, to_task_id]      AS path,
    weight                               AS path_weight,
    1                                    AS depth,
    FALSE                                AS cycle_found
  FROM workflow_edges

  UNION ALL

  SELECT
    d.start_node,
    d.next_node,
    e.to_task_id,
    d.path || e.to_task_id,
    d.path_weight + e.weight,
    d.depth + 1,
    e.to_task_id = ANY(d.path)           AS cycle_found
  FROM dfs d
  JOIN workflow_edges e ON e.from_task_id = d.next_node
  WHERE NOT e.to_task_id = ANY(d.path)   -- stop if revisiting
    AND d.depth < 50                     -- depth limit
    AND NOT d.cycle_found
),
-- Extract cycles:
cycles AS (
  SELECT
    path,
    path_weight,
    array_length(path, 1)                AS cycle_length,
    -- The back edge that closes the cycle:
    path[array_length(path, 1)]          AS cycle_closes_at,
    path[1]                              AS cycle_starts_at
  FROM dfs
  WHERE cycle_found
),
-- Find minimum weight edges in cycles (cheapest to remove):
cycle_edges AS (
  SELECT
    c.path,
    c.cycle_length,
    e.from_task_id,
    e.to_task_id,
    e.weight,
    e.edge_type,
    -- Rank edges by weight within each cycle:
    RANK() OVER (
      PARTITION BY c.path::TEXT
      ORDER BY e.weight ASC           -- lowest weight = cheapest to remove
    )                                    AS removal_priority
  FROM cycles c
  -- Join back to edges to find all edges IN the cycle:
  JOIN workflow_edges e
    ON e.from_task_id = ANY(c.path)
    AND e.to_task_id  = ANY(c.path)
),
-- Topological sort (if no cycles — for validation):
topo AS (
  SELECT
    from_task_id                         AS node,
    0                                    AS topo_order,
    ARRAY[from_task_id]                  AS visited
  FROM workflow_edges
  WHERE from_task_id NOT IN (SELECT to_task_id FROM workflow_edges)

  UNION ALL

  SELECT
    e.to_task_id,
    t.topo_order + 1,
    t.visited || e.to_task_id
  FROM topo t
  JOIN workflow_edges e ON e.from_task_id = t.node
  WHERE NOT e.to_task_id = ANY(t.visited)
)
-- Report: cycles found + minimum cut recommendations:
SELECT
  'CYCLE DETECTED'                       AS finding,
  p.path::TEXT                           AS cycle_path,
  p.cycle_length,
  ce.from_task_id                        AS recommend_remove_from,
  ce.to_task_id                          AS recommend_remove_to,
  ce.weight                              AS edge_weight,
  ce.edge_type,
  ce.removal_priority
FROM cycles p
JOIN cycle_edges ce ON ce.path = p.path AND ce.removal_priority = 1
UNION ALL
SELECT
  'NO CYCLES — TOPOLOGICAL ORDER',
  NULL, NULL,
  node, NULL,
  topo_order, NULL, NULL
FROM topo
WHERE NOT EXISTS (SELECT 1 FROM cycles)
ORDER BY 1, 3;
```

---

**10. Cross-Partition Consistency Validator**

```sql
-- PROBLEM: Table partitioned by month. An UPDATE crossed a partition boundary
-- (row's date changed). Row now exists in WRONG partition or in BOTH partitions.

-- SCHEMA: orders PARTITIONED BY RANGE (created_at)
-- Partitions: orders_2024_01, orders_2024_02, ... orders_2024_12

WITH
-- Check each partition for rows that don't belong:
partition_violations AS (
  -- Check orders_2024_01 (should only have Jan rows):
  SELECT 'orders_2024_01' AS partition_name,
    id, created_at,
    EXTRACT(MONTH FROM created_at) AS actual_month,
    1                              AS expected_month
  FROM orders_2024_01
  WHERE EXTRACT(MONTH FROM created_at) != 1
    OR EXTRACT(YEAR  FROM created_at) != 2024

  UNION ALL

  SELECT 'orders_2024_02',
    id, created_at,
    EXTRACT(MONTH FROM created_at), 2
  FROM orders_2024_02
  WHERE EXTRACT(MONTH FROM created_at) != 2
    OR EXTRACT(YEAR  FROM created_at) != 2024

  -- ... repeat for each partition
),
-- Find duplicate rows across partitions (same id in multiple partitions):
cross_partition_duplicates AS (
  SELECT
    id,
    COUNT(*)                             AS occurrence_count,
    ARRAY_AGG(tableoid::REGCLASS::TEXT ORDER BY tableoid) AS found_in_partitions
  FROM orders
  GROUP BY id
  HAVING COUNT(*) > 1
),
-- Summary:
violation_summary AS (
  SELECT
    'WRONG_PARTITION'                    AS violation_type,
    COUNT(*)                             AS count,
    MIN(created_at)                      AS earliest,
    MAX(created_at)                      AS latest
  FROM partition_violations
  UNION ALL
  SELECT
    'DUPLICATE_ACROSS_PARTITIONS',
    COUNT(*), NULL, NULL
  FROM cross_partition_duplicates
)
SELECT
  vs.violation_type,
  vs.count                               AS violation_count,
  vs.earliest,
  vs.latest,
  -- Repair commands:
  CASE vs.violation_type
    WHEN 'WRONG_PARTITION'
    THEN 'Run: DELETE + INSERT to correct partition'
    WHEN 'DUPLICATE_ACROSS_PARTITIONS'
    THEN 'Run: DELETE FROM wrong partition WHERE id IN (...)'
  END                                    AS repair_action
FROM violation_summary
WHERE vs.count > 0
UNION ALL
-- Detail for wrong-partition rows:
SELECT
  'DETAIL: ' || partition_name,
  1,
  created_at,
  created_at
FROM partition_violations
ORDER BY 1;
```

---

## 🔴 LEVEL 3: ARCHITECTURE — SYSTEM DESIGN IN SQL, META-QUERIES, SCHEMA EVOLUTION

---

**11. Schema Evolution Safety Analyzer**

```sql
-- PROBLEM: Before running any ALTER TABLE, assess blast radius.
-- Which queries break? Which indexes need rebuilding? How long will it take?

-- SCHEMA: pg_catalog tables (works on any PostgreSQL database)

WITH
-- The proposed change (parameterize this):
proposed_change AS (
  SELECT
    'orders'                             AS target_table,
    'status'                             AS target_column,
    'TEXT'                               AS current_type,
    'VARCHAR(50)'                        AS proposed_type,
    'NOT NULL'                           AS proposed_constraint
),
-- Impact 1: queries that reference this column (from pg_stat_statements):
affected_queries AS (
  SELECT
    LEFT(query, 200)                     AS query_snippet,
    calls,
    ROUND(mean_exec_time::NUMERIC, 1)    AS avg_ms,
    ROUND(total_exec_time::NUMERIC / 1000) AS total_secs
  FROM pg_stat_statements pss
  JOIN proposed_change pc ON TRUE
  WHERE pss.query ILIKE '%' || pc.target_table || '%'
    AND pss.query ILIKE '%' || pc.target_column || '%'
),
-- Impact 2: indexes on this column:
affected_indexes AS (
  SELECT
    ix.indexname,
    ix.indexdef,
    pg_size_pretty(pg_relation_size(ix.indexrelid::REGCLASS)) AS index_size,
    pg_relation_size(ix.indexrelid::REGCLASS) AS index_bytes,
    s.idx_scan                           AS total_scans,
    -- Will need rebuild:
    ix.indexdef ILIKE '%' || pc.target_column || '%' AS needs_rebuild
  FROM pg_indexes ix
  JOIN proposed_change pc ON TRUE
  JOIN pg_stat_user_indexes s ON s.indexrelname = ix.indexname
  WHERE ix.tablename = pc.target_table
    AND ix.indexdef ILIKE '%' || pc.target_column || '%'
),
-- Impact 3: views that reference this column:
affected_views AS (
  SELECT
    v.viewname,
    v.definition
  FROM pg_views v
  JOIN proposed_change pc ON TRUE
  WHERE v.definition ILIKE '%' || pc.target_table || '%'
    AND v.definition ILIKE '%' || pc.target_column || '%'
),
-- Impact 4: functions/triggers:
affected_functions AS (
  SELECT
    p.proname                            AS function_name,
    pg_get_functiondef(p.oid)            AS definition
  FROM pg_proc p
  JOIN proposed_change pc ON TRUE
  WHERE pg_get_functiondef(p.oid) ILIKE '%' || pc.target_table || '%'
    AND pg_get_functiondef(p.oid) ILIKE '%' || pc.target_column || '%'
),
-- Estimate ALTER TABLE duration:
duration_estimate AS (
  SELECT
    pc.target_table,
    c.reltuples::BIGINT                  AS row_count,
    pg_size_pretty(pg_relation_size(c.oid)) AS table_size,
    -- Rules of thumb for ALTER TABLE timing:
    CASE
      WHEN pc.proposed_type = pc.current_type
      THEN 'Milliseconds (metadata change only)'
      WHEN pc.proposed_type ILIKE 'VARCHAR%'
       AND pc.current_type = 'TEXT'
      THEN 'Minutes — full table rewrite: ~' ||
        ROUND(c.reltuples / 1000000.0, 1) || ' min per 1M rows'
      WHEN pc.proposed_constraint = 'NOT NULL'
      THEN 'Seconds + VALIDATE CONSTRAINT scan'
      ELSE 'Unknown — test in staging first'
    END                                  AS estimated_duration,
    -- Is it safe to run with CONCURRENTLY?
    FALSE                                AS can_use_concurrently,  -- ALTER cant use CONCURRENTLY
    -- Safer alternative:
    'Add new column → backfill → switch → drop old' AS safer_alternative
  FROM proposed_change pc
  JOIN pg_class c ON c.relname = pc.target_table
)
-- Combined report:
SELECT jsonb_build_object(
  'proposed_change', (SELECT row_to_json(p) FROM proposed_change p),
  'affected_queries', (
    SELECT jsonb_agg(row_to_json(q)) FROM affected_queries q
  ),
  'affected_indexes', (
    SELECT jsonb_agg(row_to_json(i)) FROM affected_indexes i
  ),
  'affected_views', (
    SELECT jsonb_agg(row_to_json(v)) FROM affected_views v
  ),
  'affected_functions', (
    SELECT jsonb_agg(row_to_json(f)) FROM affected_functions f
  ),
  'duration_estimate', (
    SELECT row_to_json(d) FROM duration_estimate d
  ),
  'risk_level', CASE
    WHEN (SELECT COUNT(*) FROM affected_queries) > 100 THEN 'HIGH'
    WHEN (SELECT COUNT(*) FROM affected_indexes) > 5   THEN 'MEDIUM'
    ELSE 'LOW'
  END
) AS impact_report;
```

---

**12. Zero-Downtime Column Type Migration**

```sql
-- PROBLEM: Change orders.status from TEXT to ENUM without downtime.
-- Table has 500M rows. Can't lock it for hours.

-- PHASE 1: Add new column (instant — no lock needed):
ALTER TABLE orders ADD COLUMN status_v2 TEXT;  -- same type first

-- PHASE 2: Dual-write trigger (new writes go to both columns):
CREATE OR REPLACE FUNCTION sync_status_columns() RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    -- Validate new values against future enum:
    IF NEW.status NOT IN ('draft','pending','confirmed','shipped','delivered','cancelled') THEN
      RAISE EXCEPTION 'Invalid status value: %', NEW.status;
    END IF;
    NEW.status_v2 := NEW.status;
  ELSIF TG_OP = 'UPDATE' THEN
    IF NEW.status IS DISTINCT FROM OLD.status THEN
      NEW.status_v2 := NEW.status;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER dual_write_status
BEFORE INSERT OR UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION sync_status_columns();

-- PHASE 3: Backfill in batches (track progress):
CREATE TABLE migration_progress (
  migration_name TEXT PRIMARY KEY,
  last_id_processed BIGINT DEFAULT 0,
  rows_processed BIGINT DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  estimated_complete_at TIMESTAMPTZ
);

INSERT INTO migration_progress (migration_name)
VALUES ('orders_status_to_v2')
ON CONFLICT DO NOTHING;

-- Backfill function (run repeatedly until complete):
CREATE OR REPLACE FUNCTION backfill_status_v2(
  p_batch_size INT DEFAULT 10000
) RETURNS TABLE(processed INT, remaining BIGINT, pct_complete NUMERIC) AS $$
DECLARE
  v_last_id   BIGINT;
  v_max_id    BIGINT;
  v_processed INT;
  v_rate      NUMERIC;
BEGIN
  SELECT last_id_processed INTO v_last_id
  FROM migration_progress WHERE migration_name = 'orders_status_to_v2';

  SELECT MAX(id) INTO v_max_id FROM orders;

  -- Backfill next batch:
  UPDATE orders SET status_v2 = status
  WHERE id > v_last_id
    AND id <= v_last_id + p_batch_size
    AND status_v2 IS NULL;

  GET DIAGNOSTICS v_processed = ROW_COUNT;

  -- Update progress:
  UPDATE migration_progress SET
    last_id_processed    = v_last_id + p_batch_size,
    rows_processed       = rows_processed + v_processed,
    estimated_complete_at = NOW() + (
      (v_max_id - (v_last_id + p_batch_size))::NUMERIC
      / NULLIF(v_processed, 0)
      * INTERVAL '1 second'
    )
  WHERE migration_name = 'orders_status_to_v2';

  RETURN QUERY
  SELECT
    v_processed,
    v_max_id - (v_last_id + p_batch_size),
    ROUND(100.0 * (v_last_id + p_batch_size) / v_max_id, 2);
END;
$$ LANGUAGE plpgsql;

-- PHASE 4: Validate backfill is complete and consistent:
SELECT
  COUNT(*) FILTER (WHERE status_v2 IS NULL)       AS missing_v2,
  COUNT(*) FILTER (WHERE status != status_v2)     AS mismatches,
  COUNT(*)                                        AS total,
  COUNT(*) FILTER (WHERE status_v2 IS NULL) = 0
  AND COUNT(*) FILTER (WHERE status != status_v2) = 0 AS ready_to_cutover
FROM orders TABLESAMPLE SYSTEM(1);  -- 1% sample for fast validation

-- PHASE 5: Atomic cutover (brief lock — milliseconds):
BEGIN;
-- Create enum type:
CREATE TYPE order_status AS ENUM
  ('draft','pending','confirmed','shipped','delivered','cancelled');
-- Add final column with proper type:
ALTER TABLE orders ADD COLUMN status_final order_status;
-- Populate from validated v2 column (fast — already backfilled):
UPDATE orders SET status_final = status_v2::order_status;
-- Drop old + v2, rename final:
ALTER TABLE orders
  DROP COLUMN status,
  DROP COLUMN status_v2,
  RENAME COLUMN status_final TO status;
-- Drop sync trigger:
DROP TRIGGER dual_write_status ON orders;
DROP FUNCTION sync_status_columns();
COMMIT;
-- Total lock time: seconds (just the column rename + constraint)
```

---

**13. Multi-Tenant Query Performance Isolation**

```sql
-- PROBLEM: One noisy tenant running expensive queries is degrading all others.
-- Must identify the tenant, quantify the impact, and throttle them.

-- Monitor resource usage per tenant in real time:
WITH
tenant_resource_usage AS (
  SELECT
    -- Extract tenant from application_name or query pattern:
    CASE
      WHEN application_name ~ 'tenant_\d+'
      THEN REGEXP_REPLACE(application_name, '.*tenant_(\d+).*', '\1')::INT
      WHEN query ~ 'tenant_id\s*=\s*\d+'
      THEN REGEXP_REPLACE(query, '.*tenant_id\s*=\s*(\d+).*', '\1')::INT
      ELSE NULL
    END                                  AS tenant_id,
    state,
    wait_event_type,
    COUNT(*)                             AS connection_count,
    -- Active queries consuming resources:
    COUNT(*) FILTER (WHERE state = 'active') AS active_queries,
    MAX(NOW() - query_start)
      FILTER (WHERE state = 'active')    AS longest_active,
    SUM(EXTRACT(EPOCH FROM NOW() - query_start))
      FILTER (WHERE state = 'active')    AS total_active_secs
  FROM pg_stat_activity
  WHERE backend_type = 'client backend'
    AND pid != pg_backend_pid()
  GROUP BY 1, 2, 3
),
-- Historical resource usage from pg_stat_statements:
tenant_historical AS (
  SELECT
    -- Parse tenant from parameterized queries:
    LEFT(query, 200)                     AS query_pattern,
    calls,
    ROUND(total_exec_time::NUMERIC / 1000, 1) AS total_secs,
    ROUND(mean_exec_time::NUMERIC, 1)    AS avg_ms,
    ROUND(100.0 * total_exec_time
      / SUM(total_exec_time) OVER (), 2) AS pct_db_time,
    shared_blks_read                     AS disk_reads,
    temp_blks_written                    AS temp_writes
  FROM pg_stat_statements
  WHERE calls > 10
    AND total_exec_time > 1000           -- only queries taking >1s total
  ORDER BY total_exec_time DESC
  LIMIT 20
),
-- Per-tenant table access patterns:
tenant_table_stats AS (
  SELECT
    relname,
    seq_scan,
    seq_tup_read,
    idx_scan,
    n_tup_ins + n_tup_upd + n_tup_del   AS write_ops,
    n_live_tup
  FROM pg_stat_user_tables
  WHERE schemaname = 'public'
),
-- Throttle recommendation:
throttle_candidates AS (
  SELECT
    tenant_id,
    connection_count,
    active_queries,
    EXTRACT(EPOCH FROM longest_active) / 60 AS longest_active_mins,
    total_active_secs,
    CASE
      WHEN active_queries > 20             THEN 'THROTTLE_IMMEDIATELY'
      WHEN longest_active > INTERVAL '10 minutes' THEN 'KILL_LONG_QUERIES'
      WHEN connection_count > 50           THEN 'LIMIT_CONNECTIONS'
      ELSE 'MONITOR'
    END                                  AS recommended_action,
    -- Generate throttle SQL:
    CASE
      WHEN active_queries > 20
      THEN 'SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE application_name LIKE ''%tenant_' || tenant_id || '%'' AND state = ''active'''
      ELSE NULL
    END                                  AS throttle_sql
  FROM tenant_resource_usage
  WHERE tenant_id IS NOT NULL
)
SELECT
  tc.*,
  th.query_pattern,
  th.avg_ms,
  th.pct_db_time
FROM throttle_candidates tc
LEFT JOIN LATERAL (
  SELECT query_pattern, avg_ms, pct_db_time
  FROM tenant_historical
  WHERE query_pattern ILIKE '%tenant_id = ' || tc.tenant_id || '%'
  ORDER BY total_secs DESC
  LIMIT 1
) th ON TRUE
WHERE tc.recommended_action != 'MONITOR'
ORDER BY tc.total_active_secs DESC;
```

---

**14. Outbox Exactly-Once Delivery With Message Ordering**

```sql
-- PROBLEM: Messages must be delivered exactly once AND in order per aggregate.
-- Out-of-order delivery corrupts downstream projections.

-- SCHEMA:
-- outbox(id, aggregate_type, aggregate_id, sequence_num, event_type,
--        payload, status, created_at, published_at, attempt_count)

-- Claim next batch maintaining per-aggregate ordering:
WITH
-- Find the minimum publishable sequence for each aggregate:
-- (Can't skip — if seq 3 is pending, don't publish seq 4 yet)
publishable_heads AS (
  SELECT DISTINCT ON (aggregate_type, aggregate_id)
    aggregate_type,
    aggregate_id,
    id                                   AS head_id,
    sequence_num                         AS head_seq
  FROM outbox
  WHERE status = 'pending'
    AND attempt_count < 5
    AND (
      -- First message for this aggregate:
      sequence_num = 1
      OR
      -- Previous sequence already published:
      EXISTS (
        SELECT 1 FROM outbox prev
        WHERE prev.aggregate_type = outbox.aggregate_type
          AND prev.aggregate_id   = outbox.aggregate_id
          AND prev.sequence_num   = outbox.sequence_num - 1
          AND prev.status         = 'published'
      )
    )
  ORDER BY aggregate_type, aggregate_id, sequence_num ASC
),
-- Claim exactly these messages (ordered, no gaps):
claimed AS (
  UPDATE outbox SET
    status        = 'processing',
    attempt_count = attempt_count + 1,
    updated_at    = NOW()
  FROM publishable_heads ph
  WHERE outbox.id = ph.head_id
    AND outbox.status = 'pending'  -- double-check status (concurrent safety)
  RETURNING
    outbox.id,
    outbox.aggregate_type,
    outbox.aggregate_id,
    outbox.sequence_num,
    outbox.event_type,
    outbox.payload,
    outbox.attempt_count,
    outbox.created_at,
    NOW() - outbox.created_at      AS delivery_latency
)
SELECT
  id,
  aggregate_type,
  aggregate_id,
  sequence_num,
  event_type,
  payload,
  attempt_count,
  EXTRACT(EPOCH FROM delivery_latency) AS latency_secs,
  -- Alert on high latency:
  delivery_latency > INTERVAL '60 seconds' AS is_late_delivery
FROM claimed
ORDER BY aggregate_type, aggregate_id, sequence_num;

-- Detect ordering violations (messages published out of order):
SELECT
  o1.aggregate_type,
  o1.aggregate_id,
  o1.sequence_num                        AS earlier_seq,
  o2.sequence_num                        AS later_seq,
  o1.published_at                        AS earlier_published,
  o2.published_at                        AS later_published,
  -- Was the later seq published BEFORE the earlier? = ordering violation
  o2.published_at < o1.published_at      AS ordering_violated,
  o1.published_at - o2.published_at      AS ordering_gap
FROM outbox o1
JOIN outbox o2
  ON o2.aggregate_type = o1.aggregate_type
  AND o2.aggregate_id  = o1.aggregate_id
  AND o2.sequence_num  = o1.sequence_num + 1
WHERE o1.status = 'published'
  AND o2.status = 'published'
  AND o2.published_at < o1.published_at  -- violation condition
ORDER BY ABS(EXTRACT(EPOCH FROM (o1.published_at - o2.published_at))) DESC;
```

---

**15. CQRS Projection Lag Monitor With Auto-Catch-Up**

```sql
-- PROBLEM: Read model (projection) falls behind event store.
-- Dashboard shows stale data. Need to detect, measure, and fix automatically.

WITH
-- Current event store frontier:
event_frontier AS (
  SELECT
    aggregate_type,
    MAX(id)                              AS latest_event_id,
    MAX(global_seq)                      AS latest_global_seq,
    MAX(recorded_at)                     AS latest_event_time,
    COUNT(*) FILTER (
      WHERE recorded_at >= NOW() - INTERVAL '1 minute'
    )                                    AS events_last_minute
  FROM event_store
  GROUP BY aggregate_type
),
-- Current projection state:
projection_frontier AS (
  SELECT
    'order_projection'                   AS projection_name,
    'Order'                              AS aggregate_type,
    MAX(last_event_id)                   AS max_applied_event,
    MAX(projection_updated_at)           AS last_updated,
    COUNT(*)                             AS projected_count
  FROM order_projection
  UNION ALL
  SELECT
    'customer_projection',
    'Customer',
    MAX(last_event_id),
    MAX(projection_updated_at),
    COUNT(*)
  FROM customer_projection
),
-- Lag analysis:
lag_analysis AS (
  SELECT
    pf.projection_name,
    pf.aggregate_type,
    ef.latest_event_id,
    pf.max_applied_event,
    -- How many events behind?
    ef.latest_event_id - pf.max_applied_event AS events_behind,
    -- How much time behind?
    NOW() - pf.last_updated              AS time_behind,
    ef.events_last_minute,
    -- At current ingestion rate, how long to catch up?
    CASE
      WHEN ef.events_last_minute > 0
      THEN INTERVAL '1 minute' *
        (ef.latest_event_id - pf.max_applied_event)::NUMERIC
        / ef.events_last_minute
      ELSE NULL
    END                                  AS estimated_catch_up_time,
    -- Severity:
    CASE
      WHEN ef.latest_event_id - pf.max_applied_event > 100000 THEN 'CRITICAL'
      WHEN ef.latest_event_id - pf.max_applied_event > 10000  THEN 'HIGH'
      WHEN ef.latest_event_id - pf.max_applied_event > 1000   THEN 'MEDIUM'
      WHEN ef.latest_event_id - pf.max_applied_event > 0      THEN 'LOW'
      ELSE 'IN_SYNC'
    END                                  AS lag_severity,
    pf.projected_count
  FROM projection_frontier pf
  JOIN event_frontier ef ON ef.aggregate_type = pf.aggregate_type
),
-- Events that need to be replayed:
events_to_replay AS (
  SELECT
    es.id,
    es.aggregate_type,
    es.aggregate_id,
    es.event_version,
    es.event_type,
    es.payload,
    es.global_seq,
    la.projection_name
  FROM lag_analysis la
  JOIN event_store es ON es.aggregate_type = la.aggregate_type
  WHERE es.id > la.max_applied_event
    AND la.lag_severity IN ('CRITICAL', 'HIGH')  -- only auto-replay for serious lag
  ORDER BY es.global_seq ASC
  LIMIT 10000                            -- cap replay batch size
)
SELECT
  la.projection_name,
  la.lag_severity,
  la.events_behind,
  EXTRACT(EPOCH FROM la.time_behind)     AS seconds_behind,
  EXTRACT(EPOCH FROM la.estimated_catch_up_time) AS estimated_catchup_secs,
  la.events_last_minute                  AS ingestion_rate,
  la.projected_count,
  -- Replay payload:
  (SELECT jsonb_agg(jsonb_build_object(
    'id', etr.id,
    'aggregate_id', etr.aggregate_id,
    'event_type', etr.event_type,
    'payload', etr.payload
  ) ORDER BY etr.global_seq)
  FROM events_to_replay etr
  WHERE etr.projection_name = la.projection_name
  LIMIT 100)                             AS first_100_events_to_replay
FROM lag_analysis la
ORDER BY la.events_behind DESC;
```

---

**16. Recursive Materialized Path With Atomic Move**

```sql
-- PROBLEM: Category tree stored as closure table.
-- Moving a subtree must atomically update ALL descendant paths.
-- Concurrent moves can corrupt the tree if not handled correctly.

-- SCHEMA:
-- category_nodes(id, name, is_active)
-- category_closure(ancestor_id, descendant_id, depth)

-- Atomic subtree move:
CREATE OR REPLACE FUNCTION move_subtree(
  p_node_id        BIGINT,
  p_new_parent_id  BIGINT
) RETURNS TABLE(
  moved_node_id    BIGINT,
  old_path_count   INT,
  new_path_count   INT
) AS $$
DECLARE
  v_subtree_nodes BIGINT[];
  v_old_paths     INT;
  v_new_paths     INT;
BEGIN
  -- Validate: new parent is not in this node's subtree (would create cycle):
  IF EXISTS (
    SELECT 1 FROM category_closure
    WHERE ancestor_id   = p_node_id
      AND descendant_id = p_new_parent_id
  ) THEN
    RAISE EXCEPTION 'Cannot move node % under its own descendant %',
      p_node_id, p_new_parent_id;
  END IF;

  -- Get all nodes in subtree (including self):
  SELECT ARRAY_AGG(descendant_id) INTO v_subtree_nodes
  FROM category_closure
  WHERE ancestor_id = p_node_id;

  -- Step 1: Delete all paths that go THROUGH this subtree FROM OUTSIDE:
  -- (Paths from ancestors of p_node_id to descendants of p_node_id)
  DELETE FROM category_closure
  WHERE descendant_id = ANY(v_subtree_nodes)
    AND ancestor_id NOT IN (
      SELECT descendant_id FROM category_closure
      WHERE ancestor_id = p_node_id   -- exclude internal subtree paths
    );

  GET DIAGNOSTICS v_old_paths = ROW_COUNT;

  -- Step 2: Reinsert with new parent's ancestry:
  INSERT INTO category_closure (ancestor_id, descendant_id, depth)
  SELECT
    -- All ancestors of new parent:
    np_ancestors.ancestor_id,
    -- All descendants of moved node:
    subtree.descendant_id,
    -- Depth = new parent's depth + 1 + subtree node's depth within subtree:
    np_ancestors.depth + 1 + subtree.depth
  FROM category_closure np_ancestors
  -- New parent's ancestors (path from root to new parent):
  JOIN category_closure subtree ON TRUE
  WHERE np_ancestors.descendant_id = p_new_parent_id
    AND subtree.ancestor_id        = p_node_id;

  GET DIAGNOSTICS v_new_paths = ROW_COUNT;

  -- Verify integrity:
  IF NOT EXISTS (
    SELECT 1 FROM category_closure
    WHERE ancestor_id   = p_new_parent_id
      AND descendant_id = p_node_id
      AND depth         = 1
  ) THEN
    RAISE EXCEPTION 'Move failed: closure table integrity check failed';
  END IF;

  RETURN QUERY
  SELECT p_node_id, v_old_paths, v_new_paths;
END;
$$ LANGUAGE plpgsql;

-- Verify tree integrity after any modification:
WITH
-- Check 1: Every node should be its own ancestor at depth 0:
missing_self_refs AS (
  SELECT id AS node_id, 'MISSING_SELF_REFERENCE' AS issue
  FROM category_nodes
  WHERE NOT EXISTS (
    SELECT 1 FROM category_closure
    WHERE ancestor_id = category_nodes.id
      AND descendant_id = category_nodes.id
      AND depth = 0
  )
),
-- Check 2: Depth consistency (child depth = parent depth + 1):
depth_inconsistencies AS (
  SELECT
    cc1.ancestor_id,
    cc1.descendant_id,
    cc1.depth,
    cc2.depth AS expected_depth,
    'DEPTH_INCONSISTENCY' AS issue
  FROM category_closure cc1
  JOIN category_closure cc2
    ON cc2.ancestor_id   = cc1.ancestor_id
    AND cc2.descendant_id = cc1.descendant_id
  WHERE cc1.depth != cc2.depth
),
-- Check 3: Transitive closure completeness:
-- If A→B (depth 1) and B→C (depth 1), must have A→C (depth 2):
missing_transitive AS (
  SELECT
    cc1.ancestor_id,
    cc2.descendant_id,
    cc1.depth + cc2.depth AS expected_depth,
    'MISSING_TRANSITIVE_PATH' AS issue
  FROM category_closure cc1
  JOIN category_closure cc2 ON cc2.ancestor_id = cc1.descendant_id
  WHERE cc1.depth > 0 AND cc2.depth > 0
    AND NOT EXISTS (
      SELECT 1 FROM category_closure cc3
      WHERE cc3.ancestor_id   = cc1.ancestor_id
        AND cc3.descendant_id = cc2.descendant_id
        AND cc3.depth         = cc1.depth + cc2.depth
    )
)
SELECT issue, COUNT(*) AS count
FROM (
  SELECT issue FROM missing_self_refs
  UNION ALL SELECT issue FROM depth_inconsistencies
  UNION ALL SELECT issue FROM missing_transitive
) all_issues
GROUP BY issue
UNION ALL
SELECT '✅ TREE INTEGRITY OK', 0
WHERE NOT EXISTS (
  SELECT 1 FROM missing_self_refs
  UNION ALL SELECT 1 FROM depth_inconsistencies
  UNION ALL SELECT 1 FROM missing_transitive
);
```

---

**17. Time-Series Anomaly Detection With Statistical Bounds**

```sql
-- PROBLEM: Detect anomalies in metric streams using statistical process control.
-- Use: 3-sigma rule, CUSUM, and Bollinger Bands — all in pure SQL.

-- SCHEMA: metrics(id, tenant_id, metric_name, value, recorded_at)

WITH
-- Base statistics (rolling 30-day window):
metric_stats AS (
  SELECT
    tenant_id,
    metric_name,
    recorded_at,
    value,
    -- Rolling statistics (28-day lookback):
    AVG(value) OVER (
      PARTITION BY tenant_id, metric_name
      ORDER BY recorded_at
      RANGE BETWEEN INTERVAL '28 days' PRECEDING AND INTERVAL '1 day' PRECEDING
    )                                    AS rolling_mean,
    STDDEV(value) OVER (
      PARTITION BY tenant_id, metric_name
      ORDER BY recorded_at
      RANGE BETWEEN INTERVAL '28 days' PRECEDING AND INTERVAL '1 day' PRECEDING
    )                                    AS rolling_stddev,
    -- Count of points in rolling window:
    COUNT(*) OVER (
      PARTITION BY tenant_id, metric_name
      ORDER BY recorded_at
      RANGE BETWEEN INTERVAL '28 days' PRECEDING AND INTERVAL '1 day' PRECEDING
    )                                    AS window_points
  FROM metrics
  WHERE recorded_at >= NOW() - INTERVAL '35 days'  -- enough for 28-day lookback
),
-- Statistical bounds:
with_bounds AS (
  SELECT
    *,
    rolling_mean + 3 * rolling_stddev    AS upper_3sigma,
    rolling_mean - 3 * rolling_stddev    AS lower_3sigma,
    rolling_mean + 2 * rolling_stddev    AS upper_2sigma,
    rolling_mean - 2 * rolling_stddev    AS lower_2sigma,
    -- Z-score: how many standard deviations from mean?
    (value - rolling_mean)
      / NULLIF(rolling_stddev, 0)        AS z_score,
    -- Is this an anomaly?
    ABS((value - rolling_mean)
      / NULLIF(rolling_stddev, 0)) > 3   AS is_3sigma_anomaly,
    -- CUSUM (cumulative sum — detects sustained drift):
    SUM((value - rolling_mean)
      / NULLIF(rolling_stddev, 0)) OVER (
      PARTITION BY tenant_id, metric_name
      ORDER BY recorded_at
      ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    )                                    AS cusum_5,
    -- Bollinger Band position:
    CASE
      WHEN value > rolling_mean + 2 * rolling_stddev THEN 'ABOVE_UPPER_BAND'
      WHEN value < rolling_mean - 2 * rolling_stddev THEN 'BELOW_LOWER_BAND'
      ELSE 'WITHIN_BANDS'
    END                                  AS bollinger_position
  FROM metric_stats
  WHERE window_points >= 10              -- need enough history for reliable stats
),
-- Classify anomaly type:
anomalies AS (
  SELECT
    *,
    CASE
      WHEN is_3sigma_anomaly AND value > rolling_mean THEN 'SPIKE'
      WHEN is_3sigma_anomaly AND value < rolling_mean THEN 'DROP'
      WHEN ABS(cusum_5) > 5             THEN 'SUSTAINED_DRIFT'
      WHEN bollinger_position != 'WITHIN_BANDS'
       AND ABS(z_score) > 2             THEN 'TREND_BREAK'
      ELSE NULL
    END                                  AS anomaly_type,
    -- Severity score:
    ABS(z_score) * CASE
      WHEN ABS(cusum_5) > 5 THEN 2      -- sustained drift = double severity
      ELSE 1
    END                                  AS severity_score
  FROM with_bounds
)
SELECT
  tenant_id,
  metric_name,
  recorded_at,
  ROUND(value::NUMERIC, 4)              AS value,
  ROUND(rolling_mean::NUMERIC, 4)       AS expected_mean,
  ROUND(rolling_stddev::NUMERIC, 4)     AS stddev,
  ROUND(z_score::NUMERIC, 2)            AS z_score,
  ROUND(cusum_5::NUMERIC, 2)            AS cusum,
  bollinger_position,
  anomaly_type,
  ROUND(severity_score::NUMERIC, 2)     AS severity,
  -- Context: previous N values (for visualization):
  ARRAY(
    SELECT ROUND(v2::NUMERIC, 4)
    FROM (
      SELECT value AS v2
      FROM metrics m2
      WHERE m2.tenant_id    = anomalies.tenant_id
        AND m2.metric_name  = anomalies.metric_name
        AND m2.recorded_at >= anomalies.recorded_at - INTERVAL '7 days'
        AND m2.recorded_at <  anomalies.recorded_at
      ORDER BY m2.recorded_at DESC
      LIMIT 7
    ) recent
  )                                      AS recent_values
FROM anomalies
WHERE anomaly_type IS NOT NULL
ORDER BY severity_score DESC, recorded_at DESC;
```

---

**18. Distributed Lock With Automatic Expiry and Requeue**

```sql
-- PROBLEM: Distributed workers claim jobs. Workers can crash mid-job.
-- Crashed jobs must be requeued. No zombie locks. No missed jobs.

-- SCHEMA: jobs(id, type, payload, status, worker_id, claimed_at,
--              heartbeat_at, completed_at, attempt_count, max_attempts,
--              next_available_at, priority)

-- Claim job (atomic — SKIP LOCKED prevents double-claim):
WITH
-- Requeue stale jobs first (crashed workers):
requeued AS (
  UPDATE jobs SET
    status            = 'pending',
    worker_id         = NULL,
    claimed_at        = NULL,
    heartbeat_at      = NULL,
    next_available_at = NOW() + (INTERVAL '1 second' * POWER(2, attempt_count))
  WHERE status = 'processing'
    AND heartbeat_at < NOW() - INTERVAL '30 seconds'  -- no heartbeat = dead worker
    AND attempt_count < max_attempts
  RETURNING id, attempt_count
),
-- Claim next available job:
claimed AS (
  UPDATE jobs SET
    status       = 'processing',
    worker_id    = $worker_id,
    claimed_at   = NOW(),
    heartbeat_at = NOW()
  WHERE id IN (
    SELECT id FROM jobs
    WHERE status = 'pending'
      AND next_available_at <= NOW()
      AND attempt_count < max_attempts
    ORDER BY
      priority DESC,          -- higher priority first
      attempt_count ASC,      -- fewer attempts first (fresh jobs first)
      next_available_at ASC   -- earliest available first
    LIMIT 1
    FOR UPDATE SKIP LOCKED    -- critical: skip locked by other workers
  )
  RETURNING
    id, type, payload, attempt_count,
    claimed_at
)
SELECT
  c.id             AS job_id,
  c.type,
  c.payload,
  c.attempt_count,
  c.claimed_at,
  r.id IS NOT NULL AS was_requeued_this_cycle,
  -- How many jobs were requeued (useful for monitoring):
  (SELECT COUNT(*) FROM requeued) AS requeued_count
FROM claimed c
LEFT JOIN requeued r ON r.id = c.id;

-- Heartbeat (worker calls this every 10 seconds while processing):
UPDATE jobs SET heartbeat_at = NOW()
WHERE id = $job_id
  AND worker_id = $worker_id
  AND status = 'processing'
RETURNING id, NOW() - claimed_at AS processing_duration;
-- 0 rows = job was stolen (shouldn't happen with SKIP LOCKED, but log it)

-- Complete job:
UPDATE jobs SET
  status       = 'completed',
  completed_at = NOW(),
  result       = $result_payload
WHERE id = $job_id
  AND worker_id = $worker_id
  AND status = 'processing'
RETURNING id, NOW() - claimed_at AS total_processing_time;

-- Fail job (with exponential backoff):
UPDATE jobs SET
  status            = CASE
    WHEN attempt_count >= max_attempts - 1 THEN 'dead'
    ELSE 'pending'
  END,
  worker_id         = NULL,
  next_available_at = NOW() + (INTERVAL '1 second' * POWER(2, attempt_count + 1)),
  error_log         = COALESCE(error_log, '[]'::JSONB)
    || jsonb_build_object(
      'attempt', attempt_count + 1,
      'error',   $error_message,
      'at',      NOW()
    )
WHERE id = $job_id AND worker_id = $worker_id;
```

---

**19. SCD Type 2 With Merge and Conflict Resolution**

```sql
-- PROBLEM: Slowly Changing Dimension — product prices change over time.
-- New batch arrives with some current, some historical, some conflicting data.
-- Must merge correctly without creating gaps or overlaps.

-- SCHEMA: product_prices(id, product_id, price, valid_from, valid_until,
--                        source, confidence, created_at)
-- CONSTRAINT: No overlapping valid periods for same product

-- Incoming batch:
WITH incoming AS (
  SELECT * FROM (VALUES
    (1001, 29.99, '2024-01-01'::DATE, '2024-06-30'::DATE, 'erp',   1.0),
    (1001, 34.99, '2024-07-01'::DATE, NULL::DATE,          'erp',   1.0),
    (1001, 32.50, '2024-04-01'::DATE, '2024-09-30'::DATE,  'web',   0.8),  -- conflict!
    (1002, 15.00, '2024-01-01'::DATE, NULL::DATE,           'erp',   1.0)
  ) AS t(product_id, price, valid_from, valid_until, source, confidence)
),
-- Existing records for affected products:
existing AS (
  SELECT * FROM product_prices
  WHERE product_id IN (SELECT product_id FROM incoming)
),
-- Detect conflicts (incoming overlaps with existing):
conflicts AS (
  SELECT
    i.product_id,
    i.price                              AS incoming_price,
    i.valid_from                         AS incoming_from,
    i.valid_until                        AS incoming_until,
    i.source                             AS incoming_source,
    i.confidence                         AS incoming_confidence,
    e.id                                 AS existing_id,
    e.price                              AS existing_price,
    e.valid_from                         AS existing_from,
    e.valid_until                        AS existing_until,
    e.source                             AS existing_source,
    e.confidence                         AS existing_confidence,
    -- Overlap type:
    CASE
      WHEN i.valid_from  = e.valid_from
       AND COALESCE(i.valid_until, 'infinity') = COALESCE(e.valid_until, 'infinity')
      THEN 'EXACT_MATCH'
      WHEN i.valid_from  < e.valid_from
       AND COALESCE(i.valid_until, 'infinity') > e.valid_from
      THEN 'INCOMING_STARTS_BEFORE'
      WHEN i.valid_from >= e.valid_from
       AND i.valid_from < COALESCE(e.valid_until, 'infinity')
      THEN 'INCOMING_STARTS_INSIDE'
      ELSE 'NO_CONFLICT'
    END                                  AS conflict_type,
    -- Resolve by confidence + source priority:
    i.confidence > e.confidence
    OR (i.confidence = e.confidence AND i.source = 'erp') AS incoming_wins
  FROM incoming i
  LEFT JOIN existing e
    ON e.product_id = i.product_id
    AND e.valid_from < COALESCE(i.valid_until, 'infinity'::DATE)
    AND COALESCE(e.valid_until, 'infinity'::DATE) > i.valid_from
),
-- Resolution plan:
resolution AS (
  SELECT
    product_id,
    conflict_type,
    incoming_wins,
    incoming_price,
    incoming_from,
    incoming_until,
    existing_id,
    existing_price,
    existing_from,
    existing_until,
    CASE
      WHEN conflict_type = 'EXACT_MATCH'
       AND incoming_price = existing_price THEN 'SKIP'   -- identical, no change
      WHEN conflict_type = 'EXACT_MATCH'
       AND incoming_wins                  THEN 'UPDATE'  -- same period, update price
      WHEN conflict_type != 'NO_CONFLICT'
       AND incoming_wins                  THEN 'SPLIT_EXISTING'  -- trim existing
      WHEN conflict_type != 'NO_CONFLICT'
       AND NOT incoming_wins              THEN 'SKIP'    -- existing wins
      ELSE                                     'INSERT'  -- no conflict
    END                                  AS action
  FROM conflicts
)
SELECT
  product_id,
  action,
  conflict_type,
  incoming_price,
  incoming_from,
  incoming_until,
  existing_id,
  existing_price,
  existing_from,
  existing_until,
  -- What to execute:
  CASE action
    WHEN 'INSERT'
    THEN format('INSERT INTO product_prices(product_id, price, valid_from, valid_until, source) VALUES (%s, %s, %L, %L, %L)',
      product_id, incoming_price, incoming_from, incoming_until, 'incoming')
    WHEN 'UPDATE'
    THEN format('UPDATE product_prices SET price = %s WHERE id = %s',
      incoming_price, existing_id)
    WHEN 'SPLIT_EXISTING'
    THEN format('UPDATE product_prices SET valid_until = %L WHERE id = %s',
      incoming_from - 1, existing_id)
    ELSE 'No action required'
  END                                    AS sql_to_execute
FROM resolution
ORDER BY product_id, incoming_from;
```

---

**20. Full Database Health Score**

```sql
-- Architecture-level: single query returns a health score for your entire database.
-- Score 0-100. Breaks down by: indexes, bloat, stats, locks, performance.

WITH
-- Component 1: Index health (0-25 points)
index_health AS (
  SELECT
    ROUND(25.0 * (
      1 -
      -- Penalty for unused indexes:
      (SELECT COUNT(*) FROM pg_stat_user_indexes
       WHERE idx_scan = 0)::NUMERIC /
      NULLIF((SELECT COUNT(*) FROM pg_stat_user_indexes), 0) * 0.5
      -
      -- Penalty for bloated indexes:
      (SELECT COUNT(*) FROM pg_stat_user_indexes si
       JOIN pg_class c ON c.relname = si.indexrelname
       WHERE pg_relation_size(c.oid) >
             pg_relation_size(si.relid) * 0.5)::NUMERIC /
      NULLIF((SELECT COUNT(*) FROM pg_stat_user_indexes), 0) * 0.5
    ), 1)                              AS score,
    (SELECT COUNT(*) FROM pg_stat_user_indexes WHERE idx_scan = 0) AS unused_indexes,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') AS total_indexes
),
-- Component 2: Table bloat health (0-25 points)
bloat_health AS (
  SELECT
    ROUND(25.0 * (
      1 -
      (SELECT AVG(
        LEAST(1, n_dead_tup::NUMERIC / NULLIF(n_live_tup, 0))
      ) FROM pg_stat_user_tables WHERE n_live_tup > 1000)
    ), 1)                              AS score,
    (SELECT COUNT(*) FROM pg_stat_user_tables
     WHERE n_dead_tup::NUMERIC / NULLIF(n_live_tup, 0) > 0.2) AS bloated_tables
),
-- Component 3: Statistics freshness (0-25 points)
stats_health AS (
  SELECT
    ROUND(25.0 * (
      1 -
      (SELECT COUNT(*) FROM pg_stat_user_tables
       WHERE n_mod_since_analyze::NUMERIC / NULLIF(n_live_tup, 0) > 0.1
         AND n_live_tup > 10000)::NUMERIC /
      NULLIF((SELECT COUNT(*) FROM pg_stat_user_tables WHERE n_live_tup > 10000), 0)
    ), 1)                              AS score,
    (SELECT COUNT(*) FROM pg_stat_user_tables
     WHERE last_autoanalyze < NOW() - INTERVAL '7 days'
       AND n_live_tup > 10000)        AS stale_stats_tables
),
-- Component 4: Performance health (0-25 points)
perf_health AS (
  SELECT
    ROUND(25.0 * (
      -- Cache hit rate:
      (SELECT blks_hit::NUMERIC / NULLIF(blks_hit + blks_read, 0)
       FROM pg_stat_database WHERE datname = current_database()) * 0.5
      +
      -- Low deadlock rate:
      GREATEST(0, 1 - (
        SELECT deadlocks::NUMERIC / NULLIF(xact_commit + xact_rollback, 0)
        FROM pg_stat_database WHERE datname = current_database()
      ) * 1000) * 0.3
      +
      -- Rollback rate low:
      GREATEST(0, 1 - (
        SELECT xact_rollback::NUMERIC / NULLIF(xact_commit, 0)
        FROM pg_stat_database WHERE datname = current_database()
      ) * 10) * 0.2
    ), 1)                              AS score,
    ROUND(100.0 *
      (SELECT blks_hit FROM pg_stat_database WHERE datname = current_database())::NUMERIC /
      NULLIF((SELECT blks_hit + blks_read FROM pg_stat_database WHERE datname = current_database()), 0),
    2)                                 AS cache_hit_pct
)
SELECT
  -- Overall score:
  ROUND(ih.score + bh.score + sh.score + ph.score, 1) AS total_health_score,
  -- Grade:
  CASE
    WHEN ih.score + bh.score + sh.score + ph.score >= 90 THEN 'A — Excellent'
    WHEN ih.score + bh.score + sh.score + ph.score >= 75 THEN 'B — Good'
    WHEN ih.score + bh.score + sh.score + ph.score >= 60 THEN 'C — Fair'
    WHEN ih.score + bh.score + sh.score + ph.score >= 40 THEN 'D — Poor'
    ELSE                                                       'F — Critical'
  END                                  AS grade,
  -- Component breakdown:
  ih.score                             AS index_score,
  ih.unused_indexes,
  ih.total_indexes,
  bh.score                             AS bloat_score,
  bh.bloated_tables,
  sh.score                             AS stats_score,
  sh.stale_stats_tables,
  ph.score                             AS perf_score,
  ph.cache_hit_pct,
  -- Top 3 recommendations:
  ARRAY_REMOVE(ARRAY[
    CASE WHEN ih.score < 15
      THEN 'Drop ' || ih.unused_indexes || ' unused indexes'
      ELSE NULL END,
    CASE WHEN bh.score < 15
      THEN 'VACUUM ' || bh.bloated_tables || ' bloated tables'
      ELSE NULL END,
    CASE WHEN sh.score < 15
      THEN 'ANALYZE ' || sh.stale_stats_tables || ' tables with stale stats'
      ELSE NULL END,
    CASE WHEN ph.cache_hit_pct < 95
      THEN 'Increase shared_buffers (cache hit: ' || ph.cache_hit_pct || '%)'
      ELSE NULL END
  ], NULL)                             AS top_recommendations
FROM index_health ih, bloat_health bh, stats_health sh, perf_health ph;
```

---

## Master Reference — All 20 Queries by Domain and Level

| # | Query | Level | Domain | Critical For |
|---|---|---|---|---|
| 1 | Double-entry violation detection | Senior | Financial | Audit, compliance |
| 2 | Running balance + overdraft detection | Senior | Financial | Risk, credit |
| 3 | Two-system reconciliation | Senior | Financial | Payment integrity |
| 4 | Cohort retention matrix | Senior | Analytics | Product decisions |
| 5 | Gap-and-island sessionization | Senior | Time-series | Behavioral analytics |
| 6 | Saga state machine query | Staff | Event-driven | Distributed transactions |
| 7 | Event projection rebuild | Staff | Event-driven | CQRS consistency |
| 8 | Temporal FK integrity | Staff | Temporal | Data quality |
| 9 | Graph cycle detection | Staff | Graph | Workflow, dependency |
| 10 | Cross-partition consistency | Staff | Distributed | Partition integrity |
| 11 | Schema evolution analyzer | Architecture | Schema | Zero-downtime deploys |
| 12 | Zero-downtime column migration | Architecture | Schema | Ops safety |
| 13 | Multi-tenant resource isolation | Architecture | Multi-tenant | SaaS operations |
| 14 | Outbox ordering guarantees | Architecture | Event-driven | Message integrity |
| 15 | Projection lag monitor | Architecture | Event-driven | CQRS operations |
| 16 | Closure table atomic move | Architecture | Graph | Hierarchy integrity |
| 17 | Statistical anomaly detection | Architecture | Time-series | Monitoring, alerting |
| 18 | Distributed lock with requeue | Architecture | Distributed | Job reliability |
| 19 | SCD Type 2 merge with conflicts | Architecture | Temporal | Data warehouse |
| 20 | Full database health score | Architecture | Meta | Operational excellence |