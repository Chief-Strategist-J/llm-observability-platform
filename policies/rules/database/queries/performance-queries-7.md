# Deep Data Modeling — All 4 Areas, Distributed Consistency, Mixed OLTP+OLAP

> **Structure:** Every section = real problem → wrong model → correct model → why it's correct → consistency guarantees → performance at scale

---

## 🔴 PART 1: SCHEMA DESIGN FOR HIGH-PERFORMANCE QUERIES

---

### 1.1 The Foundation — How to Think About Schema Design

Most schemas are designed for **correctness first, performance as an afterthought**. At scale with mixed OLTP+OLAP on the same database, you need to design for **both simultaneously** from day one.

**The three forces pulling in opposite directions:**

```
NORMALIZATION          PERFORMANCE            CONSISTENCY
(3NF, no redundancy)  (denormalize, cache)   (no anomalies)
        ↓                      ↓                    ↓
   Easy to write         Fast to read          Hard to violate
   Hard to read fast     Hard to keep correct  Hard to scale
```

**The resolution:** Design your schema in layers.

```sql
-- LAYER MODEL: every table belongs to one layer
--
-- Layer 1: SOURCE OF TRUTH (fully normalized, 3NF)
--          → writes go here, OLTP queries hit this
--          → strong consistency guaranteed by DB constraints
--
-- Layer 2: READ MODELS (denormalized, pre-aggregated)
--          → reads for OLAP/reporting hit this
--          → consistency maintained by triggers or CDC
--
-- Layer 3: MATERIALIZED VIEWS / CACHE TABLES
--          → dashboard queries, expensive aggregations
--          → acceptable staleness: seconds to minutes

-- Example: orders domain across all 3 layers

-- LAYER 1: Source of truth (write here)
CREATE TABLE orders (
  id            BIGSERIAL PRIMARY KEY,
  tenant_id     INT       NOT NULL,
  user_id       BIGINT    NOT NULL,
  status        TEXT      NOT NULL
                CHECK (status IN ('draft','pending','confirmed','shipped','delivered','cancelled')),
  currency      CHAR(3)   NOT NULL DEFAULT 'USD',
  subtotal      NUMERIC(15,4) NOT NULL CHECK (subtotal >= 0),
  tax           NUMERIC(15,4) NOT NULL DEFAULT 0 CHECK (tax >= 0),
  total         NUMERIC(15,4) GENERATED ALWAYS AS (subtotal + tax) STORED,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);  -- partition for OLAP query isolation

-- LAYER 2: Read model (query here for reports)
CREATE TABLE orders_summary (
  tenant_id     INT       NOT NULL,
  user_id       BIGINT    NOT NULL,
  month         DATE      NOT NULL,  -- first day of month
  order_count   INT       NOT NULL DEFAULT 0,
  total_revenue NUMERIC(15,4) NOT NULL DEFAULT 0,
  avg_order     NUMERIC(15,4),
  last_order_at TIMESTAMPTZ,
  PRIMARY KEY (tenant_id, user_id, month)
);

-- LAYER 3: Dashboard cache (query here for live dashboards)
CREATE TABLE tenant_daily_metrics (
  tenant_id     INT       NOT NULL,
  date          DATE      NOT NULL,
  orders_placed INT       NOT NULL DEFAULT 0,
  revenue       NUMERIC(15,4) NOT NULL DEFAULT 0,
  unique_buyers INT       NOT NULL DEFAULT 0,
  computed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (tenant_id, date)
);
```

---

### 1.2 Index Architecture for Mixed OLTP + OLAP

```sql
-- THE RULE: different query patterns need different index strategies
-- OLTP: point lookups, range by PK, writes critical
-- OLAP: aggregations, wide scans, reads critical

-- YOUR TABLE (realistic mixed-use table):
CREATE TABLE events (
  id            BIGSERIAL,
  tenant_id     INT           NOT NULL,
  user_id       BIGINT        NOT NULL,
  session_id    UUID          NOT NULL,
  event_type    TEXT          NOT NULL,
  page_url      TEXT,
  properties    JSONB,
  revenue       NUMERIC(10,4),
  created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Monthly partitions (OLAP queries prune to 1 partition instead of scanning all):
CREATE TABLE events_2024_01 PARTITION OF events
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE events_2024_02 PARTITION OF events
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... create 12 months, use pg_partman for automation

-- INDEX 1: OLTP — user's event history (point lookup by user+time)
CREATE INDEX CONCURRENTLY idx_events_user_time
ON events (tenant_id, user_id, created_at DESC)
INCLUDE (event_type, session_id);
-- Covers: SELECT event_type FROM events WHERE tenant_id=? AND user_id=? ORDER BY created_at DESC LIMIT 20

-- INDEX 2: OLTP — session lookup (find all events in a session)
CREATE INDEX CONCURRENTLY idx_events_session
ON events (session_id, created_at)
INCLUDE (event_type, properties);
-- Covers: SELECT * FROM events WHERE session_id = ? ORDER BY created_at

-- INDEX 3: OLAP — revenue aggregation (partial: only revenue-generating events)
CREATE INDEX CONCURRENTLY idx_events_revenue
ON events (tenant_id, created_at, event_type)
INCLUDE (revenue, user_id)
WHERE revenue IS NOT NULL AND revenue > 0;
-- Covers: SELECT SUM(revenue), COUNT(DISTINCT user_id) FROM events WHERE tenant_id=? AND created_at BETWEEN ? AND ? AND revenue > 0

-- INDEX 4: OLAP — event type distribution queries
CREATE INDEX CONCURRENTLY idx_events_type_tenant
ON events (event_type, tenant_id, created_at)
INCLUDE (user_id);
-- Covers: SELECT COUNT(*) FROM events WHERE event_type='purchase' AND tenant_id=? AND created_at >= ?

-- INDEX 5: JSONB properties search (GIN — for semi-structured OLAP queries)
CREATE INDEX CONCURRENTLY idx_events_properties
ON events USING GIN (properties jsonb_path_ops)
WHERE properties IS NOT NULL;
-- Covers: SELECT * FROM events WHERE properties @> '{"product_id": 123}'

-- VALIDATE index coverage (run after creating indexes):
EXPLAIN (ANALYZE, BUFFERS)
-- OLTP query:
SELECT event_type, session_id
FROM events
WHERE tenant_id = 42 AND user_id = 99999
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC LIMIT 20;
-- Should show: "Index Only Scan" on idx_events_user_time, Heap Fetches: 0

EXPLAIN (ANALYZE, BUFFERS)
-- OLAP query:
SELECT DATE_TRUNC('day', created_at), SUM(revenue), COUNT(DISTINCT user_id)
FROM events
WHERE tenant_id = 42
  AND created_at BETWEEN '2024-01-01' AND '2024-02-01'
  AND revenue > 0
GROUP BY 1;
-- Should show: "Index Only Scan" on idx_events_revenue, partition pruned to 1 partition
```

---

### 1.3 Denormalization With Consistency Guarantees

```sql
-- PROBLEM: You denormalize for read speed but writes can make it inconsistent
-- SOLUTION: Trigger-maintained denormalization (write once, always consistent)

-- Normalized source (Layer 1):
CREATE TABLE products (
  id          BIGSERIAL PRIMARY KEY,
  name        TEXT        NOT NULL,
  category_id INT         NOT NULL REFERENCES categories(id),
  brand_id    INT         NOT NULL REFERENCES brands(id),
  base_price  NUMERIC(10,4) NOT NULL,
  is_active   BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE categories (id SERIAL PRIMARY KEY, name TEXT NOT NULL, path TEXT NOT NULL);
CREATE TABLE brands     (id SERIAL PRIMARY KEY, name TEXT NOT NULL, tier TEXT NOT NULL);

-- Denormalized read model (Layer 2) — no joins needed for product display:
CREATE TABLE products_denormalized (
  product_id      BIGINT    PRIMARY KEY REFERENCES products(id),
  product_name    TEXT      NOT NULL,
  base_price      NUMERIC(10,4) NOT NULL,
  is_active       BOOLEAN   NOT NULL,
  category_id     INT       NOT NULL,
  category_name   TEXT      NOT NULL,
  category_path   TEXT      NOT NULL,
  brand_id        INT       NOT NULL,
  brand_name      TEXT      NOT NULL,
  brand_tier      TEXT      NOT NULL,
  -- Computed fields (would require joins to compute at query time):
  search_text     TSVECTOR  GENERATED ALWAYS AS (
    TO_TSVECTOR('english', product_name || ' ' || category_name || ' ' || brand_name)
  ) STORED,
  last_synced_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TRIGGER: keep denormalized table in sync with all 3 source tables

-- When product changes:
CREATE OR REPLACE FUNCTION sync_product_denormalized() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO products_denormalized
    (product_id, product_name, base_price, is_active,
     category_id, category_name, category_path,
     brand_id, brand_name, brand_tier, last_synced_at)
  SELECT
    p.id, p.name, p.base_price, p.is_active,
    c.id, c.name, c.path,
    b.id, b.name, b.tier,
    NOW()
  FROM products p
  JOIN categories c ON c.id = p.category_id
  JOIN brands b     ON b.id = p.brand_id
  WHERE p.id = NEW.id
  ON CONFLICT (product_id) DO UPDATE SET
    product_name   = EXCLUDED.product_name,
    base_price     = EXCLUDED.base_price,
    is_active      = EXCLUDED.is_active,
    category_id    = EXCLUDED.category_id,
    category_name  = EXCLUDED.category_name,
    category_path  = EXCLUDED.category_path,
    brand_id       = EXCLUDED.brand_id,
    brand_name     = EXCLUDED.brand_name,
    brand_tier     = EXCLUDED.brand_tier,
    last_synced_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_product
AFTER INSERT OR UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION sync_product_denormalized();

-- When category changes (cascade to all products in that category):
CREATE OR REPLACE FUNCTION sync_category_denormalized() RETURNS TRIGGER AS $$
BEGIN
  UPDATE products_denormalized pd SET
    category_name  = NEW.name,
    category_path  = NEW.path,
    last_synced_at = NOW()
  WHERE pd.category_id = NEW.id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_category
AFTER UPDATE OF name, path ON categories
FOR EACH ROW EXECUTE FUNCTION sync_category_denormalized();

-- RESULT: products_denormalized is ALWAYS consistent with source tables
-- Read performance: single table scan, no joins, full-text search built in
-- Write overhead: ~2ms extra per product update (acceptable)
```

---

## 🔴 PART 2: COMPLEX RELATIONSHIP MODELING

---

### 2.1 Polymorphic Relationships — The Right Way

```sql
-- PROBLEM: Comments can belong to posts, videos, products, orders
-- WRONG approach (99% of developers do this):
CREATE TABLE comments_wrong (
  id               BIGSERIAL PRIMARY KEY,
  body             TEXT NOT NULL,
  commentable_type TEXT NOT NULL,  -- 'Post', 'Video', 'Product'
  commentable_id   BIGINT NOT NULL, -- the ID of the parent
  -- Problems:
  -- 1. Cannot have FK constraint (can't reference polymorphic ID)
  -- 2. Cannot index efficiently (type+id scan, but no referential integrity)
  -- 3. JOIN requires dynamic SQL or CASE WHEN
  -- 4. Orphaned comments are invisible (deleted parent, comment remains)
);

-- RIGHT approach A — Exclusive Arc (best for 2-5 parent types):
CREATE TABLE comments (
  id              BIGSERIAL PRIMARY KEY,
  body            TEXT      NOT NULL,
  author_id       BIGINT    NOT NULL REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Each FK is nullable — exactly ONE must be non-null:
  post_id         BIGINT    REFERENCES posts(id)    ON DELETE CASCADE,
  video_id        BIGINT    REFERENCES videos(id)   ON DELETE CASCADE,
  product_id      BIGINT    REFERENCES products(id) ON DELETE CASCADE,
  order_id        BIGINT    REFERENCES orders(id)   ON DELETE CASCADE,
  -- DB-enforced: exactly one parent (not zero, not two):
  CONSTRAINT exactly_one_parent CHECK (
    (post_id    IS NOT NULL)::INT +
    (video_id   IS NOT NULL)::INT +
    (product_id IS NOT NULL)::INT +
    (order_id   IS NOT NULL)::INT = 1
  )
);

-- Partial indexes (each index only covers relevant rows = small + fast):
CREATE INDEX idx_comments_post    ON comments (post_id,    created_at DESC) WHERE post_id    IS NOT NULL;
CREATE INDEX idx_comments_video   ON comments (video_id,   created_at DESC) WHERE video_id   IS NOT NULL;
CREATE INDEX idx_comments_product ON comments (product_id, created_at DESC) WHERE product_id IS NOT NULL;
CREATE INDEX idx_comments_order   ON comments (order_id,   created_at DESC) WHERE order_id   IS NOT NULL;

-- Query is simple and uses partial index:
SELECT * FROM comments WHERE post_id = 42 ORDER BY created_at DESC;

-- RIGHT approach B — Supertype table (best for 5+ parent types, extensible):
CREATE TABLE content_items (
  id           BIGSERIAL PRIMARY KEY,
  content_type TEXT NOT NULL CHECK (content_type IN ('post','video','product','order','course')),
  -- Add new types without schema change
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Each concrete type has its own table with FK to content_items:
CREATE TABLE posts    (id BIGINT PRIMARY KEY REFERENCES content_items(id) ON DELETE CASCADE, title TEXT, body TEXT, ...);
CREATE TABLE videos   (id BIGINT PRIMARY KEY REFERENCES content_items(id) ON DELETE CASCADE, url TEXT, duration_secs INT, ...);
CREATE TABLE products (id BIGINT PRIMARY KEY REFERENCES content_items(id) ON DELETE CASCADE, price NUMERIC, sku TEXT, ...);

-- Comments now FK to content_items (one real FK, no polymorphism):
CREATE TABLE comments_v2 (
  id              BIGSERIAL PRIMARY KEY,
  content_item_id BIGINT NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  body            TEXT   NOT NULL,
  author_id       BIGINT NOT NULL REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comments_v2_content ON comments_v2 (content_item_id, created_at DESC);

-- Query: get comments for a post:
SELECT c.* FROM comments_v2 c
JOIN content_items ci ON ci.id = c.content_item_id
WHERE ci.id = $post_id
  AND ci.content_type = 'post'
ORDER BY c.created_at DESC;
```

---

### 2.2 Hierarchical Data — Closure Table (The Correct Pattern)

```sql
-- PROBLEM: Trees (org charts, categories, comments, folders)
-- WRONG: Adjacency list (parent_id only) — recursive queries are slow at depth
-- WRONG: Nested sets — expensive writes, complex maintenance
-- RIGHT: Closure table — fast reads AND writes

-- Node table (stores just the nodes, no hierarchy):
CREATE TABLE category_nodes (
  id          BIGSERIAL PRIMARY KEY,
  name        TEXT      NOT NULL,
  description TEXT,
  is_active   BOOLEAN   NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Closure table (stores ALL ancestor-descendant relationships):
CREATE TABLE category_closure (
  ancestor_id   BIGINT NOT NULL REFERENCES category_nodes(id) ON DELETE CASCADE,
  descendant_id BIGINT NOT NULL REFERENCES category_nodes(id) ON DELETE CASCADE,
  depth         INT    NOT NULL DEFAULT 0 CHECK (depth >= 0),
  PRIMARY KEY (ancestor_id, descendant_id)
);

-- Indexes for both directions of traversal:
CREATE INDEX idx_closure_descendant ON category_closure (descendant_id, depth);
CREATE INDEX idx_closure_ancestor   ON category_closure (ancestor_id,   depth);

-- INSERT a new node (function handles closure table automatically):
CREATE OR REPLACE FUNCTION insert_category_node(
  p_name      TEXT,
  p_parent_id BIGINT DEFAULT NULL  -- NULL = root node
) RETURNS BIGINT AS $$
DECLARE
  v_new_id BIGINT;
BEGIN
  -- Insert the node:
  INSERT INTO category_nodes (name) VALUES (p_name) RETURNING id INTO v_new_id;

  -- Insert self-reference (depth 0):
  INSERT INTO category_closure (ancestor_id, descendant_id, depth)
  VALUES (v_new_id, v_new_id, 0);

  -- Insert all ancestor relationships:
  IF p_parent_id IS NOT NULL THEN
    INSERT INTO category_closure (ancestor_id, descendant_id, depth)
    SELECT ancestor_id, v_new_id, depth + 1
    FROM category_closure
    WHERE descendant_id = p_parent_id;
  END IF;

  RETURN v_new_id;
END;
$$ LANGUAGE plpgsql;

-- Usage:
SELECT insert_category_node('Electronics');                     -- returns 1
SELECT insert_category_node('Phones',    parent_id => 1);       -- returns 2
SELECT insert_category_node('Smartphones', parent_id => 2);     -- returns 3
SELECT insert_category_node('iPhones',   parent_id => 3);       -- returns 4

-- GET ALL DESCENDANTS of a node (any depth):
SELECT n.*, cc.depth
FROM category_closure cc
JOIN category_nodes n ON n.id = cc.descendant_id
WHERE cc.ancestor_id = 1        -- Electronics
  AND cc.depth > 0               -- exclude self
  AND n.is_active = TRUE
ORDER BY cc.depth, n.name;
-- Returns: Phones(1), Smartphones(2), iPhones(3) — ALL descendants instantly

-- GET ALL ANCESTORS of a node (breadcrumb):
SELECT n.name, cc.depth
FROM category_closure cc
JOIN category_nodes n ON n.id = cc.ancestor_id
WHERE cc.descendant_id = 4      -- iPhones
  AND cc.depth > 0               -- exclude self
ORDER BY cc.depth DESC;          -- top-level first
-- Returns: Electronics, Phones, Smartphones (breadcrumb)

-- GET IMMEDIATE CHILDREN ONLY (depth=1):
SELECT n.*
FROM category_closure cc
JOIN category_nodes n ON n.id = cc.descendant_id
WHERE cc.ancestor_id = 1 AND cc.depth = 1
ORDER BY n.name;

-- COUNT products in a category AND ALL its subcategories:
SELECT COUNT(DISTINCT p.id) AS total_products
FROM category_closure cc
JOIN products p ON p.category_id = cc.descendant_id
WHERE cc.ancestor_id = 1;   -- Electronics + all subcategories

-- MOVE a subtree (change parent):
CREATE OR REPLACE FUNCTION move_category(
  p_node_id      BIGINT,
  p_new_parent_id BIGINT
) RETURNS VOID AS $$
BEGIN
  -- Delete all paths going THROUGH p_node_id from ABOVE:
  DELETE FROM category_closure
  WHERE descendant_id IN (
    SELECT descendant_id FROM category_closure WHERE ancestor_id = p_node_id
  )
  AND ancestor_id NOT IN (
    SELECT descendant_id FROM category_closure WHERE ancestor_id = p_node_id
  );

  -- Reinsert with new parent's ancestors:
  INSERT INTO category_closure (ancestor_id, descendant_id, depth)
  SELECT p.ancestor_id, c.descendant_id, p.depth + c.depth + 1
  FROM category_closure p
  CROSS JOIN category_closure c
  WHERE p.descendant_id = p_new_parent_id
    AND c.ancestor_id   = p_node_id;
END;
$$ LANGUAGE plpgsql;
```
**Performance:** Get all descendants = O(log N) index scan. Adjacency list recursive CTE on same data = O(N) per level. At depth 10, closure table is 10x faster.

---

### 2.3 Many-to-Many — Beyond the Junction Table

```sql
-- MOST SCHEMAS stop here (too simple):
CREATE TABLE user_roles (
  user_id BIGINT REFERENCES users(id),
  role_id BIGINT REFERENCES roles(id),
  PRIMARY KEY (user_id, role_id)
);
-- This works for simple M2M but misses: when was it assigned? by whom?
-- can it be revoked? does it expire? is it conditional?

-- PRODUCTION M2M: self-documenting, auditable, temporal
CREATE TABLE user_role_assignments (
  id            BIGSERIAL PRIMARY KEY,
  user_id       BIGINT    NOT NULL REFERENCES users(id),
  role_id       BIGINT    NOT NULL REFERENCES roles(id),
  tenant_id     INT       NOT NULL,

  -- Temporal validity:
  granted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at    TIMESTAMPTZ,           -- NULL = never expires
  revoked_at    TIMESTAMPTZ,           -- NULL = still active

  -- Audit trail:
  granted_by    BIGINT    REFERENCES users(id),
  revoked_by    BIGINT    REFERENCES users(id),
  grant_reason  TEXT,
  revoke_reason TEXT,

  -- Conditions:
  conditions    JSONB,  -- e.g. {"ip_range": "10.0.0.0/8", "mfa_required": true}

  -- Derived: is this currently active?
  is_active     BOOLEAN GENERATED ALWAYS AS (
    revoked_at IS NULL AND
    (expires_at IS NULL OR expires_at > NOW())
  ) STORED,

  -- Prevent duplicate active assignments:
  CONSTRAINT uq_active_assignment
    UNIQUE NULLS NOT DISTINCT (user_id, role_id, tenant_id, revoked_at)
);

-- Indexes for every access pattern:
CREATE INDEX idx_ura_user_active
  ON user_role_assignments (user_id, tenant_id) WHERE is_active = TRUE;
CREATE INDEX idx_ura_role_active
  ON user_role_assignments (role_id, tenant_id) WHERE is_active = TRUE;
CREATE INDEX idx_ura_expiry
  ON user_role_assignments (expires_at) WHERE expires_at IS NOT NULL AND is_active = TRUE;

-- Query: what roles does this user have RIGHT NOW?
SELECT r.name, r.permissions
FROM user_role_assignments ura
JOIN roles r ON r.id = ura.role_id
WHERE ura.user_id   = $user_id
  AND ura.tenant_id = $tenant_id
  AND ura.is_active = TRUE;   -- uses partial index: instant

-- Query: who has this role? (for admin UI)
SELECT u.email, ura.granted_at, ura.expires_at, ura.grant_reason
FROM user_role_assignments ura
JOIN users u ON u.id = ura.user_id
WHERE ura.role_id   = $role_id
  AND ura.tenant_id = $tenant_id
  AND ura.is_active = TRUE;

-- Full history (including revoked):
SELECT ura.*, u.email, r.name AS role_name,
  g.email AS granted_by_email, rv.email AS revoked_by_email
FROM user_role_assignments ura
JOIN users u  ON u.id  = ura.user_id
JOIN roles r  ON r.id  = ura.role_id
LEFT JOIN users g  ON g.id  = ura.granted_by
LEFT JOIN users rv ON rv.id = ura.revoked_by
WHERE ura.user_id = $user_id
ORDER BY ura.granted_at DESC;
```

---

### 2.4 Temporal Data Modeling — Bitemporal Schema

```sql
-- TWO TIMELINES every business needs but most schemas ignore:
-- 1. Valid time  = when the fact was TRUE in the real world
-- 2. System time = when the database KNEW about it
--
-- Example: salary change backdated vs when it was entered
-- Real world: salary increased on Jan 1
-- Entered into DB: March 15 (payroll was slow)
-- These are DIFFERENT and both matter for audits

CREATE TABLE employee_salaries (
  id              BIGSERIAL PRIMARY KEY,
  employee_id     BIGINT    NOT NULL REFERENCES employees(id),

  -- THE ACTUAL SALARY:
  salary          NUMERIC(12,2) NOT NULL CHECK (salary > 0),
  currency        CHAR(3)   NOT NULL DEFAULT 'USD',

  -- VALID TIME: when this salary was true in reality
  valid_from      DATE      NOT NULL,
  valid_until     DATE      NOT NULL DEFAULT '9999-12-31',  -- open-ended = current

  -- SYSTEM TIME: when we knew about it (PostgreSQL 16+ handles this natively)
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  recorded_by     BIGINT    REFERENCES users(id),

  -- No overlapping valid periods for same employee:
  CONSTRAINT no_overlap EXCLUDE USING GIST (
    employee_id WITH =,
    DATERANGE(valid_from, valid_until, '[)') WITH &&
  ),

  -- valid_until must be after valid_from:
  CONSTRAINT valid_period CHECK (valid_until > valid_from)
);

CREATE INDEX idx_salaries_employee_valid
  ON employee_salaries (employee_id, valid_from, valid_until);

-- Query: what is salary for employee X TODAY?
SELECT salary, valid_from
FROM employee_salaries
WHERE employee_id = $emp_id
  AND valid_from  <= CURRENT_DATE
  AND valid_until >  CURRENT_DATE;

-- Query: what was salary for employee X on a specific DATE? (point-in-time)
SELECT salary, valid_from, valid_until
FROM employee_salaries
WHERE employee_id = $emp_id
  AND valid_from  <= $as_of_date::DATE
  AND valid_until >  $as_of_date::DATE;

-- Query: full salary history (all periods, all time):
SELECT
  salary,
  currency,
  valid_from,
  valid_until,
  valid_until - valid_from AS days_in_effect,
  recorded_at,
  LAG(salary) OVER (PARTITION BY employee_id ORDER BY valid_from) AS prev_salary,
  salary - LAG(salary) OVER (PARTITION BY employee_id ORDER BY valid_from) AS change_amount
FROM employee_salaries
WHERE employee_id = $emp_id
ORDER BY valid_from;

-- Update salary: NEVER update the row, INSERT a new period
-- Old period closes, new period opens:
CREATE OR REPLACE FUNCTION set_employee_salary(
  p_employee_id BIGINT,
  p_salary      NUMERIC,
  p_from_date   DATE,
  p_recorded_by BIGINT
) RETURNS VOID AS $$
BEGIN
  -- Close the current period (set valid_until to start of new period):
  UPDATE employee_salaries SET
    valid_until = p_from_date
  WHERE employee_id = p_employee_id
    AND valid_until = '9999-12-31'   -- currently open
    AND valid_from  < p_from_date;   -- and starts before new period

  -- Open new period:
  INSERT INTO employee_salaries
    (employee_id, salary, valid_from, recorded_by)
  VALUES
    (p_employee_id, p_salary, p_from_date, p_recorded_by);
END;
$$ LANGUAGE plpgsql;
```

---

## 🔴 PART 3: EVENT SOURCING, CQRS, OUTBOX PATTERNS

---

### 3.1 Event Sourcing Schema — Production-Grade

```sql
-- MISCONCEPTION: "Event sourcing means no relational DB"
-- REALITY: PostgreSQL handles event sourcing excellently at billions of events

-- EVENT STORE: append-only, immutable, the source of truth
CREATE TABLE event_store (
  -- Identity:
  id              BIGSERIAL PRIMARY KEY,
  aggregate_type  TEXT      NOT NULL,   -- 'Order', 'Account', 'User'
  aggregate_id    BIGINT    NOT NULL,   -- ID of the specific order/account/user

  -- Event data:
  event_type      TEXT      NOT NULL,   -- 'OrderPlaced', 'PaymentReceived'
  event_version   INT       NOT NULL,   -- version within this aggregate's stream
  payload         JSONB     NOT NULL,   -- the event data
  metadata        JSONB,                -- causation_id, correlation_id, user_agent

  -- Causality tracking (for distributed debugging):
  causation_id    BIGINT    REFERENCES event_store(id),  -- which event caused this
  correlation_id  UUID      NOT NULL DEFAULT gen_random_uuid(), -- trace across services

  -- Timing:
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- when it happened
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- when we recorded it

  -- Immutability enforcement:
  -- No UPDATE or DELETE allowed (enforced by trigger below)

  -- Optimistic concurrency: no two events can have same version for same aggregate
  CONSTRAINT uq_aggregate_version UNIQUE (aggregate_type, aggregate_id, event_version)
) PARTITION BY RANGE (recorded_at);

-- Monthly partitions (OLAP can query specific time ranges efficiently):
CREATE TABLE event_store_2024_01 PARTITION OF event_store
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Indexes:
-- Primary access pattern: replay all events for one aggregate (OLTP):
CREATE INDEX idx_event_store_aggregate
  ON event_store (aggregate_type, aggregate_id, event_version);

-- Secondary: find events of a type in a time range (OLAP):
CREATE INDEX idx_event_store_type_time
  ON event_store (event_type, recorded_at)
  INCLUDE (aggregate_id, payload);

-- Tertiary: causality tracing:
CREATE INDEX idx_event_store_correlation
  ON event_store (correlation_id)
  WHERE correlation_id IS NOT NULL;

-- Immutability trigger (prevent updates and deletes):
CREATE OR REPLACE FUNCTION prevent_event_mutation() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Events are immutable. Cannot % event store records.', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER no_event_updates BEFORE UPDATE ON event_store
FOR EACH ROW EXECUTE FUNCTION prevent_event_mutation();

CREATE TRIGGER no_event_deletes BEFORE DELETE ON event_store
FOR EACH ROW EXECUTE FUNCTION prevent_event_mutation();

-- APPEND event (with optimistic concurrency check):
CREATE OR REPLACE FUNCTION append_event(
  p_aggregate_type TEXT,
  p_aggregate_id   BIGINT,
  p_event_type     TEXT,
  p_payload        JSONB,
  p_expected_version INT DEFAULT NULL  -- NULL = don't check version
) RETURNS BIGINT AS $$
DECLARE
  v_current_version INT;
  v_new_version     INT;
  v_event_id        BIGINT;
BEGIN
  -- Get current version (lock the aggregate stream):
  SELECT COALESCE(MAX(event_version), 0) INTO v_current_version
  FROM event_store
  WHERE aggregate_type = p_aggregate_type
    AND aggregate_id   = p_aggregate_id
  FOR UPDATE;  -- row-level lock on this aggregate's stream

  -- Optimistic concurrency check:
  IF p_expected_version IS NOT NULL
   AND v_current_version != p_expected_version THEN
    RAISE EXCEPTION
      'Concurrency conflict: expected version %, got %',
      p_expected_version, v_current_version;
  END IF;

  v_new_version := v_current_version + 1;

  INSERT INTO event_store
    (aggregate_type, aggregate_id, event_type, event_version, payload)
  VALUES
    (p_aggregate_type, p_aggregate_id, p_event_type, v_new_version, p_payload)
  RETURNING id INTO v_event_id;

  RETURN v_event_id;
END;
$$ LANGUAGE plpgsql;

-- REPLAY: reconstruct current state from events
SELECT
  event_type,
  event_version,
  payload,
  occurred_at,
  -- Running state accumulation (application applies these in order):
  payload->>'status'                        AS status_at_this_event,
  (payload->>'amount')::NUMERIC             AS amount_delta,
  SUM((payload->>'amount')::NUMERIC)
    FILTER (WHERE payload->>'amount' IS NOT NULL)
    OVER (ORDER BY event_version)           AS running_total
FROM event_store
WHERE aggregate_type = 'Order'
  AND aggregate_id   = $order_id
ORDER BY event_version;
```

---

### 3.2 CQRS — Read Model Projections

```sql
-- CQRS: writes go to event store, reads go to projections
-- Projection = denormalized read model built from events
-- Critical for mixed OLTP+OLAP: OLTP writes events, OLAP reads projections

-- Order projection (built from Order events, optimized for UI queries):
CREATE TABLE order_projection (
  order_id        BIGINT    PRIMARY KEY,
  tenant_id       INT       NOT NULL,
  customer_id     BIGINT    NOT NULL,
  customer_email  TEXT      NOT NULL,   -- denormalized from customer aggregate

  -- Current state (derived from all events):
  status          TEXT      NOT NULL,
  total_amount    NUMERIC(15,4) NOT NULL DEFAULT 0,
  item_count      INT       NOT NULL DEFAULT 0,
  currency        CHAR(3)   NOT NULL DEFAULT 'USD',

  -- Timestamps derived from events:
  placed_at       TIMESTAMPTZ,
  confirmed_at    TIMESTAMPTZ,
  shipped_at      TIMESTAMPTZ,
  delivered_at    TIMESTAMPTZ,
  cancelled_at    TIMESTAMPTZ,

  -- Projection metadata:
  last_event_id        BIGINT NOT NULL,  -- which event was last applied
  last_event_version   INT    NOT NULL,
  projection_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- OLAP indexes (queries reports need, not OLTP):
CREATE INDEX idx_order_proj_tenant_status
  ON order_projection (tenant_id, status, placed_at DESC)
  INCLUDE (total_amount, customer_id);

CREATE INDEX idx_order_proj_customer
  ON order_projection (customer_id, placed_at DESC)
  INCLUDE (status, total_amount);

-- Projection updater (called by event handler / CDC consumer):
CREATE OR REPLACE FUNCTION apply_order_event(
  p_event_id      BIGINT,
  p_aggregate_id  BIGINT,
  p_event_type    TEXT,
  p_event_version INT,
  p_payload       JSONB
) RETURNS VOID AS $$
BEGIN
  CASE p_event_type

    WHEN 'OrderPlaced' THEN
      INSERT INTO order_projection
        (order_id, tenant_id, customer_id, customer_email,
         status, total_amount, currency, placed_at,
         last_event_id, last_event_version)
      VALUES (
        p_aggregate_id,
        (p_payload->>'tenant_id')::INT,
        (p_payload->>'customer_id')::BIGINT,
        p_payload->>'customer_email',
        'placed',
        (p_payload->>'total_amount')::NUMERIC,
        COALESCE(p_payload->>'currency', 'USD'),
        NOW(),
        p_event_id, p_event_version
      )
      ON CONFLICT (order_id) DO NOTHING;

    WHEN 'OrderConfirmed' THEN
      UPDATE order_projection SET
        status               = 'confirmed',
        confirmed_at         = NOW(),
        last_event_id        = p_event_id,
        last_event_version   = p_event_version,
        projection_updated_at = NOW()
      WHERE order_id = p_aggregate_id
        AND last_event_version < p_event_version;  -- idempotent

    WHEN 'OrderShipped' THEN
      UPDATE order_projection SET
        status               = 'shipped',
        shipped_at           = NOW(),
        last_event_id        = p_event_id,
        last_event_version   = p_event_version,
        projection_updated_at = NOW()
      WHERE order_id = p_aggregate_id
        AND last_event_version < p_event_version;

    WHEN 'OrderCancelled' THEN
      UPDATE order_projection SET
        status               = 'cancelled',
        cancelled_at         = NOW(),
        last_event_id        = p_event_id,
        last_event_version   = p_event_version,
        projection_updated_at = NOW()
      WHERE order_id = p_aggregate_id
        AND last_event_version < p_event_version;

    ELSE
      -- Unknown event type: log and skip (don't crash projection)
      INSERT INTO projection_errors (event_id, event_type, error_msg, occurred_at)
      VALUES (p_event_id, p_event_type, 'Unknown event type', NOW());

  END CASE;
END;
$$ LANGUAGE plpgsql;
```

---

### 3.3 Outbox Pattern — Guaranteed Event Delivery

```sql
-- PROBLEM: You update a table AND publish an event
-- If app crashes between the two: data updated but event never sent
-- SOLUTION: Write event in same transaction as data change (outbox)

-- OUTBOX TABLE (lives in same database as your domain tables):
CREATE TABLE outbox_messages (
  id              BIGSERIAL PRIMARY KEY,
  -- Routing:
  aggregate_type  TEXT      NOT NULL,   -- which service owns this event
  aggregate_id    BIGINT    NOT NULL,
  event_type      TEXT      NOT NULL,
  -- Payload:
  payload         JSONB     NOT NULL,
  headers         JSONB,               -- Kafka headers, trace IDs, etc.
  -- Delivery tracking:
  status          TEXT      NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'processing', 'published', 'failed', 'dead')),
  attempt_count   INT       NOT NULL DEFAULT 0,
  max_attempts    INT       NOT NULL DEFAULT 5,
  next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  published_at    TIMESTAMPTZ,
  last_error      TEXT,
  -- Ordering:
  sequence_num    BIGINT    NOT NULL GENERATED ALWAYS AS IDENTITY,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Partial index: only unpublished messages (stays small as messages are processed):
CREATE INDEX idx_outbox_pending
  ON outbox_messages (next_attempt_at, id)
  WHERE status IN ('pending', 'failed');

-- WRITE: order update + outbox message in ONE transaction:
BEGIN;

-- Domain write:
UPDATE orders SET
  status     = 'confirmed',
  updated_at = NOW()
WHERE id = $order_id;

-- Outbox write (same transaction = atomic):
INSERT INTO outbox_messages (aggregate_type, aggregate_id, event_type, payload)
VALUES (
  'order',
  $order_id,
  'OrderConfirmed',
  jsonb_build_object(
    'order_id',    $order_id,
    'customer_id', $customer_id,
    'amount',      $amount,
    'confirmed_at', NOW()
  )
);

COMMIT;
-- If commit fails: BOTH the order update and outbox message roll back
-- If commit succeeds: BOTH persist, relay will publish the message

-- RELAY (runs every 100ms, picks up pending messages):
WITH batch AS (
  SELECT id, aggregate_type, aggregate_id, event_type, payload, attempt_count
  FROM outbox_messages
  WHERE status IN ('pending', 'failed')
    AND next_attempt_at <= NOW()
    AND attempt_count < max_attempts
  ORDER BY id ASC
  LIMIT 100
  FOR UPDATE SKIP LOCKED  -- safe for multiple relay instances
),
-- Mark as processing:
claimed AS (
  UPDATE outbox_messages SET
    status        = 'processing',
    attempt_count = attempt_count + 1
  WHERE id IN (SELECT id FROM batch)
  RETURNING id, aggregate_type, aggregate_id, event_type, payload
)
SELECT * FROM claimed;
-- Application publishes to Kafka/SQS, then calls mark_published() below

-- After successful publish:
CREATE OR REPLACE FUNCTION mark_outbox_published(p_ids BIGINT[]) RETURNS VOID AS $$
BEGIN
  UPDATE outbox_messages SET
    status       = 'published',
    published_at = NOW()
  WHERE id = ANY(p_ids);
END;
$$ LANGUAGE plpgsql;

-- After failed publish (with exponential backoff):
CREATE OR REPLACE FUNCTION mark_outbox_failed(
  p_id    BIGINT,
  p_error TEXT
) RETURNS VOID AS $$
DECLARE v_attempts INT;
BEGIN
  SELECT attempt_count INTO v_attempts
  FROM outbox_messages WHERE id = p_id;

  UPDATE outbox_messages SET
    status          = CASE WHEN v_attempts >= max_attempts THEN 'dead' ELSE 'failed' END,
    last_error      = p_error,
    next_attempt_at = NOW() + (INTERVAL '1 second' * POWER(2, v_attempts))  -- 2,4,8,16,32s
  WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
```

---

## 🔴 PART 4: MULTI-TENANT ARCHITECTURE

---

### 4.1 Three Patterns — When to Use Each

```sql
-- PATTERN 1: ROW-LEVEL ISOLATION (tenant_id column on every table)
-- Best for: SaaS with thousands of tenants, similar usage patterns
-- Tradeoff: simplest to operate, hardest to guarantee isolation at DB level

-- Every table has tenant_id:
CREATE TABLE orders (
  id          BIGSERIAL PRIMARY KEY,
  tenant_id   INT NOT NULL,   -- ← always first in every index
  user_id     BIGINT NOT NULL,
  amount      NUMERIC(15,4),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ENFORCE at DB level with Row Level Security (not just application code):
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Policy: each connection can only see its own tenant's data:
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.current_tenant_id')::INT);

-- Set tenant at connection time (application does this after auth):
SET app.current_tenant_id = '42';
-- Now ALL queries on orders automatically filter to tenant 42
-- Even if developer forgets WHERE tenant_id = ?, RLS blocks it

-- Verify RLS is working:
SELECT * FROM orders;  -- automatically adds WHERE tenant_id = 42

-- Every index must have tenant_id FIRST:
CREATE INDEX idx_orders_tenant_user
  ON orders (tenant_id, user_id, created_at DESC);  -- tenant_id first
-- Without tenant_id first: index scan reads across all tenants

-- PATTERN 2: SCHEMA-PER-TENANT
-- Best for: enterprise SaaS, strict compliance, fewer large tenants (<100)
-- Tradeoff: full isolation, expensive to operate at scale

-- Create schema for each tenant:
CREATE SCHEMA tenant_42;
CREATE SCHEMA tenant_43;

-- Each schema has identical table structure:
CREATE TABLE tenant_42.orders (LIKE public.orders_template INCLUDING ALL);
CREATE TABLE tenant_43.orders (LIKE public.orders_template INCLUDING ALL);

-- Route connection to correct schema:
SET search_path = tenant_42;
SELECT * FROM orders;  -- hits tenant_42.orders only

-- Automated schema creation for new tenants:
CREATE OR REPLACE FUNCTION create_tenant_schema(p_tenant_id INT) RETURNS VOID AS $$
DECLARE
  v_schema TEXT := 'tenant_' || p_tenant_id;
  v_table  TEXT;
BEGIN
  -- Create schema:
  EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', v_schema);

  -- Clone all template tables:
  FOR v_table IN
    SELECT tablename FROM pg_tables WHERE schemaname = 'tenant_template'
  LOOP
    EXECUTE format(
      'CREATE TABLE %I.%I (LIKE tenant_template.%I INCLUDING ALL)',
      v_schema, v_table, v_table
    );
  END LOOP;

  RAISE NOTICE 'Created schema % with all tables', v_schema;
END;
$$ LANGUAGE plpgsql;

-- PATTERN 3: DATABASE-PER-TENANT
-- Best for: maximum isolation, different regions, regulatory requirements
-- Tradeoff: hardest to operate, impossible at thousands of tenants

-- Managed via connection routing (PgBouncer config or application layer):
-- Tenant 42 → connects to host: tenant-42.db.internal
-- Tenant 43 → connects to host: tenant-43.db.internal

-- Cross-tenant analytics still possible via FDW:
CREATE SERVER tenant_42_db FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'tenant-42.db.internal', dbname 'tenant_db');

CREATE FOREIGN TABLE tenant_42_orders (LIKE orders)
SERVER tenant_42_db;
```

---

### 4.2 Distributed Consistency Across Tenant Tables

```sql
-- THE CORE PROBLEM:
-- Mixed OLTP+OLAP on same DB
-- OLTP: tenant writes orders (needs immediate consistency)
-- OLAP: analytics reads across ALL tenants (needs eventual consistency)
-- Both hitting same PostgreSQL → contention

-- SOLUTION: Write isolation via partition + async projection

-- Step 1: Partition OLTP tables by tenant to isolate I/O:
CREATE TABLE orders (
  id          BIGSERIAL,
  tenant_id   INT         NOT NULL,
  user_id     BIGINT      NOT NULL,
  status      TEXT        NOT NULL,
  amount      NUMERIC(15,4),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (tenant_id, id)      -- tenant_id in PK = partition key
) PARTITION BY HASH (tenant_id);   -- hash partitioning = even distribution

-- 16 partitions = 16 independent page locks under concurrent write:
CREATE TABLE orders_p00 PARTITION OF orders FOR VALUES WITH (MODULUS 16, REMAINDER 0);
CREATE TABLE orders_p01 PARTITION OF orders FOR VALUES WITH (MODULUS 16, REMAINDER 1);
-- ... through p15

-- Step 2: Isolate OLAP from OLTP using parallel query on partitions:
-- OLTP query (single tenant, hits 1 partition):
SELECT * FROM orders WHERE tenant_id = 42 AND status = 'pending';

-- OLAP query (all tenants, hits all 16 partitions in PARALLEL):
SET max_parallel_workers_per_gather = 8;
SELECT tenant_id, DATE_TRUNC('month', created_at), SUM(amount)
FROM orders
WHERE created_at >= '2024-01-01'
GROUP BY 1, 2;
-- PostgreSQL runs 8 parallel workers, each scanning 2 partitions
-- OLAP query doesn't block OLTP on individual tenant partitions

-- Step 3: Track cross-tenant consistency state:
CREATE TABLE consistency_ledger (
  table_name    TEXT        NOT NULL,
  tenant_id     INT         NOT NULL,
  last_write_id BIGINT,                    -- last written row ID
  last_write_at TIMESTAMPTZ,               -- when last written
  olap_synced_id BIGINT,                   -- last ID reflected in analytics
  olap_synced_at TIMESTAMPTZ,
  lag_rows      BIGINT GENERATED ALWAYS AS  -- how many rows behind
    (COALESCE(last_write_id - olap_synced_id, 0)) STORED,
  PRIMARY KEY (table_name, tenant_id)
);

-- Update after every OLTP write (trigger):
CREATE OR REPLACE FUNCTION track_write_consistency() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO consistency_ledger (table_name, tenant_id, last_write_id, last_write_at)
  VALUES (TG_TABLE_NAME, NEW.tenant_id, NEW.id, NOW())
  ON CONFLICT (table_name, tenant_id) DO UPDATE SET
    last_write_id = GREATEST(consistency_ledger.last_write_id, NEW.id),
    last_write_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_track_consistency
AFTER INSERT OR UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION track_write_consistency();

-- Check consistency lag before running OLAP query:
SELECT
  tenant_id,
  lag_rows,
  last_write_at - olap_synced_at AS lag_duration,
  CASE
    WHEN lag_rows = 0            THEN 'CONSISTENT'
    WHEN lag_rows < 100          THEN 'EVENTUALLY CONSISTENT (<100 rows behind)'
    WHEN lag_rows < 10000        THEN 'LAGGING — OLAP data is stale'
    ELSE                              'CRITICAL LAG — OLAP unreliable'
  END AS consistency_status
FROM consistency_ledger
WHERE table_name = 'orders'
ORDER BY lag_rows DESC;
```

---

### 4.3 Cross-Tenant OLAP Without OLTP Interference

```sql
-- THE HARDEST PROBLEM in mixed OLTP+OLAP:
-- OLAP query takes 60 seconds scanning orders across all tenants
-- During those 60 seconds, OLTP orders are being written
-- → OLAP holds shared locks, OLTP waits → production degraded

-- SOLUTION: Materialized OLAP layer with scheduled refresh
-- OLTP writes to live tables, OLAP reads from snapshots

-- Snapshot table (OLAP reads from this, not live tables):
CREATE TABLE orders_olap_snapshot (
  -- Identical structure to orders:
  id          BIGINT,
  tenant_id   INT,
  user_id     BIGINT,
  status      TEXT,
  amount      NUMERIC(15,4),
  created_at  TIMESTAMPTZ,
  -- Snapshot metadata:
  snapshot_id     BIGINT      NOT NULL,  -- which snapshot run
  snapshotted_at  TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (created_at);  -- partition for OLAP time-range queries

CREATE TABLE orders_olap_2024_q1 PARTITION OF orders_olap_snapshot
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

-- Snapshot refresh (run every 15 minutes, NEVER during peak hours):
CREATE OR REPLACE FUNCTION refresh_olap_snapshot(
  p_snapshot_id BIGINT
) RETURNS INT AS $$
DECLARE
  v_rows INT;
  v_last_snapshot_at TIMESTAMPTZ;
BEGIN
  -- Find last snapshot time (only refresh incremental):
  SELECT MAX(snapshotted_at) INTO v_last_snapshot_at
  FROM orders_olap_snapshot;

  -- Insert only NEW rows since last snapshot:
  INSERT INTO orders_olap_snapshot
    (id, tenant_id, user_id, status, amount, created_at, snapshot_id, snapshotted_at)
  SELECT
    id, tenant_id, user_id, status, amount, created_at,
    p_snapshot_id, NOW()
  FROM orders
  WHERE created_at > COALESCE(v_last_snapshot_at, '-infinity'::TIMESTAMPTZ)
    AND created_at < NOW() - INTERVAL '1 minute';  -- safety buffer

  GET DIAGNOSTICS v_rows = ROW_COUNT;

  -- Update existing rows that changed status:
  UPDATE orders_olap_snapshot oas SET
    status       = o.status,
    snapshot_id  = p_snapshot_id,
    snapshotted_at = NOW()
  FROM orders o
  WHERE oas.id = o.id
    AND oas.status != o.status;     -- only update changed rows

  RETURN v_rows;
END;
$$ LANGUAGE plpgsql;

-- OLAP queries run against snapshot (no interference with OLTP):
SELECT
  tenant_id,
  DATE_TRUNC('week', created_at)          AS week,
  COUNT(*)                                AS orders,
  SUM(amount)                             AS revenue,
  COUNT(DISTINCT user_id)                 AS unique_buyers,
  AVG(amount)                             AS avg_order
FROM orders_olap_snapshot                  -- ← snapshot, not live table
WHERE created_at BETWEEN '2024-01-01' AND '2024-06-30'
GROUP BY tenant_id, DATE_TRUNC('week', created_at)
ORDER BY tenant_id, week;
-- No locks on live orders table. OLTP continues unaffected.
```

---

## 🔴 PART 5: CONSISTENCY PATTERNS ACROSS DISTRIBUTED TABLES

---

### 5.1 The Consistency Spectrum

```sql
-- FOUR LEVELS of consistency — choose per operation:
--
-- LEVEL 1: STRONG   — reads always see latest write (PostgreSQL default, single node)
-- LEVEL 2: CAUSAL   — reads see writes they causally depend on
-- LEVEL 3: EVENTUAL — reads will converge to latest write (given time)
-- LEVEL 4: WEAK     — no guarantees (analytics snapshots, caches)

-- STRONG consistency: use for financial data, inventory, user auth
BEGIN;
SELECT balance FROM accounts WHERE id = $id FOR UPDATE;  -- lock row
UPDATE accounts SET balance = balance - $amount WHERE id = $id;
COMMIT;
-- Anyone reading this account sees the deducted balance IMMEDIATELY

-- CAUSAL consistency: use for user-facing data (post, then read your post)
-- Capture write LSN, pass to reads:
-- After write:
SELECT pg_current_wal_lsn() AS causal_token;  -- e.g., "0/3A2F8C0"
-- Return causal_token to client. Client passes it on next read.

-- On read (replica):
SELECT pg_wal_replay_wait('0/3A2F8C0', timeout_ms => 2000);
SELECT * FROM posts WHERE id = $post_id;
-- Waits up to 2s for replica to catch up to your write, then reads

-- EVENTUAL consistency: use for analytics, counters, search indexes
-- Just write and let downstream catch up:
INSERT INTO events (user_id, event_type) VALUES ($user_id, 'page_view');
-- Analytics will see it when the next snapshot runs (minutes later, OK)

-- Track consistency level per table (documentation + enforcement):
CREATE TABLE table_consistency_contracts (
  table_name          TEXT PRIMARY KEY,
  consistency_level   TEXT NOT NULL CHECK (
    consistency_level IN ('strong','causal','eventual','weak')
  ),
  max_acceptable_lag  INTERVAL,  -- for eventual/weak
  notes               TEXT
);

INSERT INTO table_consistency_contracts VALUES
  ('accounts',          'strong',   NULL,          'Financial data — must be exact'),
  ('inventory',         'strong',   NULL,          'Stock levels — no oversell'),
  ('orders',            'causal',   NULL,          'User sees own orders immediately'),
  ('product_views',     'eventual', '5 minutes',   'View counts — approximate is fine'),
  ('orders_olap',       'weak',     '15 minutes',  'Analytics snapshots');
```

---

### 5.2 Referential Integrity Across Distributed Tables

```sql
-- PROBLEM: With multiple schemas/databases, FK constraints don't cross boundaries
-- SOLUTION: Application-level FK checks enforced consistently

-- Pattern: deferred FK check via trigger (works across schemas)
CREATE OR REPLACE FUNCTION check_cross_schema_fk(
  p_referencing_schema TEXT,
  p_referencing_table  TEXT,
  p_referencing_col    TEXT,
  p_referenced_schema  TEXT,
  p_referenced_table   TEXT,
  p_referenced_col     TEXT,
  p_value              TEXT
) RETURNS BOOLEAN AS $$
DECLARE v_exists BOOLEAN;
BEGIN
  EXECUTE format(
    'SELECT EXISTS(SELECT 1 FROM %I.%I WHERE %I = $1)',
    p_referenced_schema, p_referenced_table, p_referenced_col
  ) INTO v_exists USING p_value;

  RETURN v_exists;
END;
$$ LANGUAGE plpgsql STABLE;

-- Use in application validation before cross-schema inserts:
SELECT check_cross_schema_fk(
  'tenant_42', 'orders', 'customer_id',
  'public',    'customers', 'id',
  $customer_id::TEXT
);
-- Returns FALSE = customer doesn't exist = reject the insert

-- Consistency check query (find all cross-schema orphans):
DO $$
DECLARE
  v_tenant_schema TEXT;
  v_orphan_count  INT;
BEGIN
  FOR v_tenant_schema IN
    SELECT schema_name FROM information_schema.schemata
    WHERE schema_name LIKE 'tenant_%'
  LOOP
    EXECUTE format($q$
      SELECT COUNT(*) FROM %I.orders o
      WHERE NOT EXISTS (
        SELECT 1 FROM public.customers c WHERE c.id = o.customer_id
      )
    $q$, v_tenant_schema) INTO v_orphan_count;

    IF v_orphan_count > 0 THEN
      RAISE WARNING 'Schema % has % orphaned orders (no matching customer)',
        v_tenant_schema, v_orphan_count;
    END IF;
  END LOOP;
END $$;
```

---

### 5.3 Complete Data Model Health Check

```sql
-- Run this weekly on your entire database
-- Catches: missing FKs, no indexes on FK cols, tables without PKs,
--          nullable FK cols, missing updated_at, tables with 0 rows

WITH
-- Tables missing primary keys:
missing_pk AS (
  SELECT t.table_name, 'NO PRIMARY KEY' AS issue
  FROM information_schema.tables t
  WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    AND t.table_name NOT IN (
      SELECT tc.table_name
      FROM information_schema.table_constraints tc
      WHERE tc.constraint_type = 'PRIMARY KEY'
        AND tc.table_schema = 'public'
    )
),
-- FK columns without indexes:
fk_no_index AS (
  SELECT
    kcu.table_name,
    kcu.column_name,
    'FK COLUMN WITHOUT INDEX: ' || kcu.column_name AS issue
  FROM information_schema.key_column_usage kcu
  JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = kcu.constraint_name
  WHERE kcu.table_schema = 'public'
    AND NOT EXISTS (
      SELECT 1 FROM pg_indexes ix
      WHERE ix.tablename = kcu.table_name
        AND ix.indexdef LIKE '%' || kcu.column_name || '%'
    )
),
-- Large tables without updated_at (can't do incremental ETL):
no_updated_at AS (
  SELECT c.relname AS table_name,
    'LARGE TABLE WITHOUT updated_at: ' || c.relname AS issue
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public'
    AND c.relkind = 'r'
    AND c.reltuples > 100000
    AND NOT EXISTS (
      SELECT 1 FROM information_schema.columns col
      WHERE col.table_name = c.relname
        AND col.column_name IN ('updated_at', 'modified_at', 'changed_at')
    )
),
-- Tables with no rows (dead weight):
empty_tables AS (
  SELECT relname AS table_name,
    'EMPTY TABLE — consider dropping' AS issue
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public'
    AND c.relkind = 'r'
    AND c.reltuples = 0
    AND c.relname NOT LIKE '%_template%'
    AND c.relname NOT LIKE '%_history%'
)
-- Combined report:
SELECT table_name, issue FROM missing_pk
UNION ALL
SELECT table_name, issue FROM fk_no_index
UNION ALL
SELECT table_name, issue FROM no_updated_at
UNION ALL
SELECT table_name, issue FROM empty_tables
ORDER BY table_name, issue;
```

---

## Reference Map — Which Pattern Solves Which Problem

```
PROBLEM                              → PATTERN
─────────────────────────────────────────────────────────────────────
OLTP + OLAP on same table            → Partition by time + parallel query
Reads slow as data grows             → Covering index + partial index
Writes slow (too many indexes)       → Drop unused indexes, partial indexes
Polymorphic relationships            → Exclusive arc OR supertype table
Tree/hierarchy queries slow          → Closure table
M2M with business rules              → Junction table with temporal columns
Point-in-time historical queries     → Bitemporal schema (valid_time + system_time)
Event history / audit trail          → Event store (append-only + immutable)
OLAP queries blocking OLTP           → OLAP snapshot + scheduled refresh
Eventual vs strong consistency       → Consistency contract per table
Event loss on crash                  → Outbox pattern (same transaction)
Multi-tenant data bleeding           → RLS policy + tenant_id first in every index
Cross-schema FK integrity            → Application-level FK check function
Stale planner statistics             → ANALYZE + SET STATISTICS 500+
Schema evolution without downtime    → Add column nullable → backfill → add NOT NULL
Deduplication on growing table       → Partial unique index on active rows only
```