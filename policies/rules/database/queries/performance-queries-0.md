# Advanced SQL Performance Queries — Top 50

---

## 🔴 CATEGORY 1: INDEX ISSUES

---

**1. Missing Index on JOIN column**

```sql
-- ❌ WRONG
SELECT o.order_id, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;
-- No index on orders.customer_id → full table scan on every join

-- ✅ RIGHT
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
SELECT o.order_id, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;
```
**Impact:** Full table scan on millions of rows vs index seek in microseconds. Can be 1000x slower without index.

---

**2. Leading Wildcard kills index**

```sql
-- ❌ WRONG
SELECT * FROM customers WHERE name LIKE '%john%';
-- Scans every row, index is useless

-- ✅ RIGHT
SELECT * FROM customers WHERE name LIKE 'john%';
-- OR use Full-Text Search
SELECT * FROM customers WHERE MATCH(name) AGAINST('john' IN BOOLEAN MODE);
```
**Impact:** `%john%` = full scan always. `john%` = index range scan.

---

**3. Function on indexed column breaks index**

```sql
-- ❌ WRONG
SELECT * FROM orders WHERE YEAR(created_at) = 2024;
-- Function prevents index usage

-- ✅ RIGHT
SELECT * FROM orders 
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01';
```
**Impact:** Wrapping a column in ANY function (UPPER, LOWER, DATE, CAST) disables the index entirely.

---

**4. Implicit type conversion disables index**

```sql
-- ❌ WRONG
SELECT * FROM users WHERE phone = 9876543210;
-- phone is VARCHAR, comparing to INT → implicit cast, no index

-- ✅ RIGHT
SELECT * FROM users WHERE phone = '9876543210';
```
**Impact:** Type mismatch silently causes full scan. Common bug that's hard to spot.

---

**5. Composite index column order wrong**

```sql
-- Index: CREATE INDEX idx ON orders(status, created_at)

-- ❌ WRONG
SELECT * FROM orders WHERE created_at > '2024-01-01';
-- Skips leading column 'status' → index unused

-- ✅ RIGHT
SELECT * FROM orders WHERE status = 'active' AND created_at > '2024-01-01';
-- OR redesign index to match your query pattern
CREATE INDEX idx ON orders(created_at, status);
```
**Impact:** Composite index is only used when leading column is in WHERE clause.

---

**6. OR condition breaks index**

```sql
-- ❌ WRONG
SELECT * FROM users WHERE email = 'a@b.com' OR phone = '999';
-- Often causes full scan even with both indexed

-- ✅ RIGHT
SELECT * FROM users WHERE email = 'a@b.com'
UNION ALL
SELECT * FROM users WHERE phone = '999' AND email != 'a@b.com';
```
**Impact:** OR forces optimizer to choose between indexes or abandon both. UNION is faster.

---

**7. Over-indexing slows writes**

```sql
-- ❌ WRONG
CREATE INDEX idx1 ON orders(status);
CREATE INDEX idx2 ON orders(status, created_at);
CREATE INDEX idx3 ON orders(status, user_id);
CREATE INDEX idx4 ON orders(status, created_at, user_id);
-- idx1 and idx2 are now redundant

-- ✅ RIGHT
-- Keep only the most selective composite index
CREATE INDEX idx_orders_main ON orders(status, created_at, user_id);
-- Drop redundant indexes
DROP INDEX idx1 ON orders;
DROP INDEX idx2 ON orders;
```
**Impact:** Every INSERT/UPDATE/DELETE must update all indexes. 10 indexes = 10x write overhead.

---

**8. Index not used due to NULL comparison**

```sql
-- ❌ WRONG
SELECT * FROM users WHERE deleted_at != NULL;
-- Always returns 0 rows. NULL comparisons don't work with !=

-- ✅ RIGHT
SELECT * FROM users WHERE deleted_at IS NULL;
SELECT * FROM users WHERE deleted_at IS NOT NULL;
```
**Impact:** Logic bug + index not used. Always use IS NULL / IS NOT NULL.

---

## 🔴 CATEGORY 2: SELECT & QUERY STRUCTURE

---

**9. SELECT * is a performance killer**

```sql
-- ❌ WRONG
SELECT * FROM orders JOIN customers ON orders.customer_id = customers.id;
-- Fetches all columns from both tables, bloats network + memory

-- ✅ RIGHT
SELECT o.order_id, o.total, c.name, c.email
FROM orders o JOIN customers c ON o.customer_id = c.id;
```
**Impact:** SELECT * prevents covering indexes, increases I/O, and sends unused data over network.

---

**10. COUNT(*) vs COUNT(column)**

```sql
-- ❌ WRONG (when you want total rows)
SELECT COUNT(deleted_at) FROM users;
-- Counts only non-NULL values, likely wrong result

-- ✅ RIGHT
SELECT COUNT(*) FROM users;           -- total rows
SELECT COUNT(deleted_at) FROM users;  -- only when you explicitly want non-NULL count
SELECT COUNT(DISTINCT user_id) FROM orders; -- distinct count
```
**Impact:** COUNT(*) is optimized by engine. COUNT(col) checks each value. Know which you need.

---

**11. DISTINCT masking a JOIN problem**

```sql
-- ❌ WRONG
SELECT DISTINCT o.order_id, c.name
FROM orders o JOIN customers c ON o.customer_id = c.id;
-- DISTINCT is hiding a bad join producing duplicates

-- ✅ RIGHT
-- Fix the join. Ask: why are duplicates produced?
-- Usually a missing GROUP BY or wrong join type
SELECT o.order_id, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
GROUP BY o.order_id, c.name;
```
**Impact:** DISTINCT sorts/deduplicates the entire result set. Very expensive on large data.

---

**12. Correlated subquery in SELECT**

```sql
-- ❌ WRONG
SELECT 
  u.name,
  (SELECT COUNT(*) FROM orders WHERE user_id = u.id) AS order_count
FROM users u;
-- Executes subquery once per row in users

-- ✅ RIGHT
SELECT u.name, COALESCE(o.order_count, 0) AS order_count
FROM users u
LEFT JOIN (
  SELECT user_id, COUNT(*) AS order_count
  FROM orders GROUP BY user_id
) o ON o.user_id = u.id;
```
**Impact:** Correlated subquery = N queries for N rows. JOIN aggregation = 2 queries total.

---

**13. NOT IN with NULLs returns nothing**

```sql
-- ❌ WRONG
SELECT * FROM orders WHERE user_id NOT IN (SELECT id FROM deleted_users);
-- If deleted_users has even one NULL id, result is always empty

-- ✅ RIGHT
SELECT * FROM orders o
WHERE NOT EXISTS (
  SELECT 1 FROM deleted_users d WHERE d.id = o.user_id
);
```
**Impact:** NOT IN short-circuits to empty result when subquery contains NULL. Silent data loss.

---

**14. IN vs EXISTS for large subqueries**

```sql
-- ❌ WRONG (large subquery)
SELECT * FROM orders 
WHERE user_id IN (SELECT id FROM users WHERE country = 'IN');
-- Materializes entire subquery result first

-- ✅ RIGHT
SELECT * FROM orders o
WHERE EXISTS (
  SELECT 1 FROM users u WHERE u.id = o.user_id AND u.country = 'IN'
);
```
**Impact:** EXISTS stops at first match. IN loads and checks all values. On large sets, EXISTS wins.

---

**15. HAVING vs WHERE confusion**

```sql
-- ❌ WRONG
SELECT user_id, COUNT(*) AS cnt
FROM orders
GROUP BY user_id
HAVING user_id > 100;
-- Aggregates ALL rows then filters. WHERE would filter before grouping.

-- ✅ RIGHT
SELECT user_id, COUNT(*) AS cnt
FROM orders
WHERE user_id > 100
GROUP BY user_id;
```
**Impact:** HAVING filters after aggregation. WHERE filters before. Always push filters to WHERE.

---

**16. Pagination with OFFSET at scale**

```sql
-- ❌ WRONG
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 100000;
-- Reads 100,020 rows, discards 100,000

-- ✅ RIGHT (Keyset / Cursor pagination)
SELECT * FROM orders 
WHERE created_at < '2024-03-15 10:00:00'  -- last seen value
ORDER BY created_at DESC 
LIMIT 20;
```
**Impact:** OFFSET 1M = scan 1M rows. Keyset pagination is O(1) regardless of page depth.

---

**17. Unnecessary subquery instead of JOIN**

```sql
-- ❌ WRONG
SELECT * FROM orders
WHERE user_id IN (SELECT id FROM users WHERE status = 'active');

-- ✅ RIGHT
SELECT o.* FROM orders o
JOIN users u ON u.id = o.user_id
WHERE u.status = 'active';
```
**Impact:** JOIN lets optimizer choose best strategy. Subquery forces sequential evaluation.

---

## 🔴 CATEGORY 3: JOINS

---

**18. Joining without filtering first (large tables)**

```sql
-- ❌ WRONG
SELECT * FROM orders o
JOIN order_items oi ON o.id = oi.order_id
WHERE o.status = 'pending' AND o.created_at > '2024-01-01';
-- Joins everything, then filters

-- ✅ RIGHT
SELECT * FROM (
  SELECT id FROM orders 
  WHERE status = 'pending' AND created_at > '2024-01-01'
) filtered_orders
JOIN order_items oi ON filtered_orders.id = oi.order_id;
```
**Impact:** Filter early, join less. Smaller intermediate result = faster join.

---

**19. CROSS JOIN without condition**

```sql
-- ❌ WRONG
SELECT * FROM products, categories;
-- Implicit CROSS JOIN: 1000 products × 50 categories = 50,000 rows

-- ✅ RIGHT
SELECT p.*, c.name AS category_name
FROM products p
JOIN categories c ON p.category_id = c.id;
```
**Impact:** Accidental cartesian product can crash servers. Always verify join conditions exist.

---

**20. LEFT JOIN with WHERE filtering right table (converts to INNER JOIN)**

```sql
-- ❌ WRONG
SELECT u.*, o.total FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.status = 'completed';
-- WHERE on right table NULLifies LEFT JOIN → becomes INNER JOIN

-- ✅ RIGHT
SELECT u.*, o.total FROM users u
LEFT JOIN orders o ON o.user_id = u.id AND o.status = 'completed';
-- Filter moved into JOIN condition
```
**Impact:** Logic bug — users with no completed orders are excluded silently.

---

**21. Too many JOINs in one query**

```sql
-- ❌ WRONG
SELECT * FROM a JOIN b ON ... JOIN c ON ... JOIN d ON ... 
JOIN e ON ... JOIN f ON ... JOIN g ON ...
-- Optimizer has exponential join-order combinations to evaluate

-- ✅ RIGHT
-- Break into CTEs or temp tables
WITH ab AS (SELECT ... FROM a JOIN b ON ...),
     abc AS (SELECT ... FROM ab JOIN c ON ...)
SELECT ... FROM abc JOIN d ON ...;
```
**Impact:** 8+ join optimizer complexity explodes. CTEs let you control order and reuse results.

---

## 🔴 CATEGORY 4: AGGREGATIONS & GROUPING

---

**22. GROUP BY on non-indexed column**

```sql
-- ❌ WRONG
SELECT department, COUNT(*) FROM employees GROUP BY department;
-- No index on department → full scan + sort

-- ✅ RIGHT
CREATE INDEX idx_dept ON employees(department);
SELECT department, COUNT(*) FROM employees GROUP BY department;
```
**Impact:** Without index, GROUP BY requires full scan + filesort. Index makes it a range scan.

---

**23. Aggregating before filtering**

```sql
-- ❌ WRONG
SELECT user_id, SUM(amount) FROM transactions
GROUP BY user_id
HAVING SUM(amount) > 1000 AND user_id IN (SELECT id FROM active_users);

-- ✅ RIGHT
SELECT t.user_id, SUM(t.amount) 
FROM transactions t
JOIN active_users au ON au.id = t.user_id
GROUP BY t.user_id
HAVING SUM(t.amount) > 1000;
```
**Impact:** Filter rows before aggregating, not after. Fewer rows to GROUP = faster.

---

**24. Recomputing aggregation multiple times**

```sql
-- ❌ WRONG
SELECT user_id
FROM orders
WHERE amount > (SELECT AVG(amount) FROM orders)
AND amount < (SELECT AVG(amount) FROM orders) * 2;
-- AVG computed twice

-- ✅ RIGHT
WITH avg_amount AS (SELECT AVG(amount) AS avg FROM orders)
SELECT user_id FROM orders, avg_amount
WHERE amount > avg AND amount < avg * 2;
```
**Impact:** Each subquery is a full scan. CTE computes it once.

---

## 🔴 CATEGORY 5: CTEs & WINDOW FUNCTIONS

---

**25. Recursive CTE without depth limit**

```sql
-- ❌ WRONG
WITH RECURSIVE tree AS (
  SELECT id, parent_id FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.parent_id FROM categories c JOIN tree ON c.parent_id = tree.id
)
SELECT * FROM tree;
-- Infinite loop if circular reference exists

-- ✅ RIGHT
WITH RECURSIVE tree AS (
  SELECT id, parent_id, 1 AS depth FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.parent_id, t.depth + 1
  FROM categories c JOIN tree t ON c.parent_id = t.id
  WHERE t.depth < 10  -- guard
)
SELECT * FROM tree;
```
**Impact:** Without depth guard, circular data kills the query. Always add depth limiter.

---

**26. ROW_NUMBER vs RANK vs DENSE_RANK confusion**

```sql
-- ❌ WRONG: Using ROW_NUMBER when you need rank with ties
SELECT name, salary,
  ROW_NUMBER() OVER (ORDER BY salary DESC) AS rank
FROM employees;
-- Two employees with same salary get different "ranks"

-- ✅ RIGHT
SELECT name, salary,
  RANK() OVER (ORDER BY salary DESC) AS rank,        -- skips numbers on ties
  DENSE_RANK() OVER (ORDER BY salary DESC) AS d_rank -- no gaps
FROM employees;
```
**Impact:** Wrong function = wrong business logic. Know the difference.

---

**27. Window function in WHERE clause**

```sql
-- ❌ WRONG
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS rn
  FROM employees
)
WHERE rn = 1;
-- Works but subquery materializes all rows first

-- ✅ RIGHT (PostgreSQL/SQL Server)
SELECT DISTINCT ON (dept) * 
FROM employees 
ORDER BY dept, salary DESC;
-- OR use CTE for clarity and optimizer hints
```
**Impact:** Window functions cannot be in WHERE directly. Subquery is required but can be expensive.

---

**28. LAG/LEAD without proper partitioning**

```sql
-- ❌ WRONG
SELECT order_id, amount,
  LAG(amount) OVER (ORDER BY created_at) AS prev_amount
FROM orders;
-- Crosses user boundaries — compares one user's order to another's

-- ✅ RIGHT
SELECT order_id, user_id, amount,
  LAG(amount) OVER (PARTITION BY user_id ORDER BY created_at) AS prev_amount
FROM orders;
```
**Impact:** Missing PARTITION BY gives meaningless cross-entity comparisons.

---

## 🔴 CATEGORY 6: TRANSACTIONS & LOCKING

---

**29. Long-running transactions holding locks**

```sql
-- ❌ WRONG
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
-- ... application does some processing for 30 seconds ...
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;

-- ✅ RIGHT
-- Do ALL application logic first, then:
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```
**Impact:** Long transactions hold row locks, block other queries, and cause deadlocks.

---

**30. Deadlock from inconsistent lock order**

```sql
-- ❌ WRONG
-- Session 1: locks row A then row B
-- Session 2: locks row B then row A → DEADLOCK

-- ✅ RIGHT
-- Always lock in same order (e.g., by primary key ascending)
BEGIN;
SELECT * FROM accounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE;
-- Now update in same order
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```
**Impact:** Consistent lock ordering prevents deadlocks entirely.

---

**31. SELECT FOR UPDATE without index**

```sql
-- ❌ WRONG
SELECT * FROM orders WHERE status = 'pending' FOR UPDATE;
-- No index on status → table-level lock

-- ✅ RIGHT
CREATE INDEX idx_status ON orders(status);
SELECT * FROM orders WHERE status = 'pending' FOR UPDATE;
-- Row-level locks only
```
**Impact:** Table lock blocks all concurrent writes. Row lock only blocks affected rows.

---

**32. UPDATE without WHERE (full table update)**

```sql
-- ❌ WRONG
UPDATE users SET is_verified = 1;
-- Updates ALL rows, full table lock

-- ✅ RIGHT
UPDATE users SET is_verified = 1 WHERE is_verified = 0;
-- OR batch it:
UPDATE users SET is_verified = 1 
WHERE id BETWEEN 1 AND 10000 AND is_verified = 0;
```
**Impact:** Updating millions of rows at once = long lock + huge undo log + replication lag.

---

**33. Batch deletes instead of single delete**

```sql
-- ❌ WRONG
DELETE FROM logs WHERE created_at < '2023-01-01';
-- Deletes millions of rows in one transaction, huge lock

-- ✅ RIGHT
-- Loop in application:
DELETE FROM logs WHERE created_at < '2023-01-01' LIMIT 1000;
-- Repeat until 0 rows affected
```
**Impact:** Batch deletes keep transactions short, prevent lock escalation and replication lag.

---

## 🔴 CATEGORY 7: SCHEMA & DATA TYPES

---

**34. Using VARCHAR for dates**

```sql
-- ❌ WRONG
CREATE TABLE events (event_date VARCHAR(20));
SELECT * FROM events WHERE event_date > '2024-01-01';
-- String comparison, no date math, no index range scan

-- ✅ RIGHT
CREATE TABLE events (event_date DATE);
SELECT * FROM events WHERE event_date > '2024-01-01';
```
**Impact:** Wrong type = wrong sort order, no date functions, wasted storage.

---

**35. Using TEXT/BLOB for everything**

```sql
-- ❌ WRONG
CREATE TABLE users (
  id INT, name TEXT, age TEXT, is_active TEXT
);

-- ✅ RIGHT
CREATE TABLE users (
  id INT UNSIGNED NOT NULL,
  name VARCHAR(100) NOT NULL,
  age TINYINT UNSIGNED,
  is_active BOOLEAN DEFAULT TRUE
);
```
**Impact:** TEXT forces off-page storage, no inline indexing, wastes memory and I/O.

---

**36. Missing NOT NULL constraints**

```sql
-- ❌ WRONG
CREATE TABLE orders (
  id INT, user_id INT, total DECIMAL(10,2)
);
-- NULLs in join columns cause missed rows, NULL propagation bugs

-- ✅ RIGHT
CREATE TABLE orders (
  id INT NOT NULL,
  user_id INT NOT NULL,
  total DECIMAL(10,2) NOT NULL DEFAULT 0.00
);
```
**Impact:** NULLs in critical columns corrupt aggregation, JOIN results, and comparisons.

---

**37. DECIMAL vs FLOAT for money**

```sql
-- ❌ WRONG
CREATE TABLE transactions (amount FLOAT);
INSERT INTO transactions VALUES (0.1 + 0.2);
SELECT amount FROM transactions; -- 0.30000000000000004

-- ✅ RIGHT
CREATE TABLE transactions (amount DECIMAL(15, 2));
```
**Impact:** FLOAT has binary precision errors. NEVER use for currency. DECIMAL is exact.

---

## 🔴 CATEGORY 8: QUERY PLANNING & ANALYSIS

---

**38. Not using EXPLAIN / EXPLAIN ANALYZE**

```sql
-- ❌ WRONG: Running slow query blind
SELECT * FROM orders WHERE status = 'pending' AND created_at > '2024-01-01';

-- ✅ RIGHT: Analyze first
EXPLAIN SELECT * FROM orders WHERE status = 'pending' AND created_at > '2024-01-01';
-- MySQL
EXPLAIN FORMAT=JSON SELECT ...;
-- PostgreSQL
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;
```
**Impact:** EXPLAIN shows: full scan vs index scan, join strategy, rows estimated, actual cost.

---

**39. Ignoring query cost in EXPLAIN**

```sql
-- Key things to look for in EXPLAIN output:

-- ❌ BAD signs:
-- type: ALL             → full table scan
-- Extra: Using filesort → no index for ORDER BY
-- Extra: Using temporary → temp table created
-- rows: 5000000         → scanning 5M rows for 10 results

-- ✅ GOOD signs:
-- type: ref, range, index, eq_ref, const
-- Extra: Using index    → covering index (no table lookup)
-- rows: 10              → precise
```
**Impact:** Learning to read EXPLAIN is the single most important performance skill.

---

**40. Statistics not updated (stale query plans)**

```sql
-- ❌ WRONG: Optimizer uses stale row counts
-- After bulk insert of millions of rows, optimizer still thinks table is small

-- ✅ RIGHT
-- MySQL
ANALYZE TABLE orders;
-- PostgreSQL
ANALYZE orders;
VACUUM ANALYZE orders;
-- SQL Server
UPDATE STATISTICS orders;
```
**Impact:** Outdated stats = wrong execution plan = 100x slower queries.

---

## 🔴 CATEGORY 9: COMMON ANTI-PATTERNS

---

**41. Polling with repeated COUNT queries**

```sql
-- ❌ WRONG (app polls every second)
SELECT COUNT(*) FROM jobs WHERE status = 'pending';

-- ✅ RIGHT
-- Use message queues (Redis, RabbitMQ, SQS) for job tracking
-- Or use LISTEN/NOTIFY (PostgreSQL)
LISTEN job_queue;
NOTIFY job_queue, '{"job_id": 123}';
```
**Impact:** COUNT on large table is expensive. Polling every second = constant load.

---

**42. Storing comma-separated values in a column**

```sql
-- ❌ WRONG
CREATE TABLE posts (tags VARCHAR(500));
INSERT INTO posts VALUES ('sql,performance,database');
SELECT * FROM posts WHERE tags LIKE '%performance%';
-- Can't index, can't join, can't aggregate

-- ✅ RIGHT
CREATE TABLE post_tags (post_id INT, tag VARCHAR(50));
INSERT INTO post_tags VALUES (1, 'sql'), (1, 'performance'), (1, 'database');
SELECT p.* FROM posts p JOIN post_tags pt ON pt.post_id = p.id WHERE pt.tag = 'performance';
```
**Impact:** CSV in column = no index, no referential integrity, no proper queries. Classic violation of 1NF.

---

**43. Using ORM-generated queries blindly**

```sql
-- ❌ WRONG (typical ORM N+1 problem)
-- For each user, ORM fires: SELECT * FROM orders WHERE user_id = ?
-- 1000 users = 1001 queries

-- ✅ RIGHT (eager load in ORM, or raw SQL)
SELECT u.*, o.id, o.total 
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;
-- 1 query for everything
```
**Impact:** N+1 is the most common ORM performance killer. Always check query logs.

---

**44. No query timeout set**

```sql
-- ❌ WRONG: Runaway query blocks server for hours

-- ✅ RIGHT
-- MySQL
SET SESSION MAX_EXECUTION_TIME = 5000; -- 5 seconds
-- PostgreSQL
SET statement_timeout = '5s';
-- SQL Server
-- Set in connection string: Connection Timeout=5
```
**Impact:** One bad query without timeout can OOM or lock the entire database server.

---

**45. Using RAND() in ORDER BY**

```sql
-- ❌ WRONG
SELECT * FROM products ORDER BY RAND() LIMIT 10;
-- Assigns random value to EVERY row, sorts all of them

-- ✅ RIGHT (MySQL)
SELECT * FROM products
WHERE id >= (SELECT FLOOR(MAX(id) * RAND()) FROM products)
LIMIT 10;
-- PostgreSQL
SELECT * FROM products ORDER BY RANDOM() LIMIT 10; -- acceptable for small tables
-- For large: use tablesample
SELECT * FROM products TABLESAMPLE SYSTEM(1) LIMIT 10;
```
**Impact:** ORDER BY RAND() is O(N log N) on entire table. Never use on large datasets.

---

## 🔴 CATEGORY 10: ADVANCED PATTERNS

---

**46. UNION vs UNION ALL**

```sql
-- ❌ WRONG
SELECT id FROM table_a UNION SELECT id FROM table_b;
-- Sorts and deduplicates entire result — expensive

-- ✅ RIGHT (when duplicates are acceptable or impossible)
SELECT id FROM table_a UNION ALL SELECT id FROM table_b;
-- No sort, no dedup — just concatenates
```
**Impact:** UNION = sort + dedup = O(N log N). UNION ALL = O(N). Use UNION only when dedup needed.

---

**47. Upsert done wrong**

```sql
-- ❌ WRONG (race condition)
IF NOT EXISTS (SELECT 1 FROM users WHERE email = 'x@y.com')
  INSERT INTO users (email) VALUES ('x@y.com');
-- Concurrent requests can both pass the check and double-insert

-- ✅ RIGHT
-- MySQL
INSERT INTO users (email) VALUES ('x@y.com')
ON DUPLICATE KEY UPDATE email = VALUES(email);
-- PostgreSQL
INSERT INTO users (email) VALUES ('x@y.com')
ON CONFLICT (email) DO UPDATE SET updated_at = NOW();
```
**Impact:** Check-then-insert is never atomic. ON CONFLICT / ON DUPLICATE KEY is atomic.

---

**48. Sorting in application instead of database**

```sql
-- ❌ WRONG
SELECT * FROM orders; 
-- Sort 1M rows in application memory

-- ✅ RIGHT
SELECT * FROM orders ORDER BY created_at DESC LIMIT 100;
-- Database uses index, returns only what's needed
```
**Impact:** Transferring millions of rows to sort in app is wasteful. Database is built for this.

---

**49. Unparameterized queries (SQL injection + no plan cache)**

```sql
-- ❌ WRONG
query = "SELECT * FROM users WHERE id = " + userId;
-- SQL injection vulnerability + optimizer can't cache plan

-- ✅ RIGHT
SELECT * FROM users WHERE id = ?;  -- prepared statement
-- Or named param: WHERE id = :user_id
```
**Impact:** Without parameterization: SQL injection risk + query plan recompiled every time = double penalty.

---

**50. Not archiving old data (fat tables)**

```sql
-- ❌ WRONG
-- orders table: 500M rows going back 10 years
SELECT * FROM orders WHERE user_id = 5 AND created_at > '2024-01-01';
-- Index scan still slow because table is massive

-- ✅ RIGHT
-- Partition by date
CREATE TABLE orders_2024 PARTITION OF orders 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- OR archive old data
INSERT INTO orders_archive SELECT * FROM orders WHERE created_at < '2022-01-01';
DELETE FROM orders WHERE created_at < '2022-01-01';
```
**Impact:** Table size directly affects index depth (B-tree height), buffer pool efficiency, and vacuum/autovacuum time.

---

## Quick Reference Cheat Sheet

| Anti-Pattern | Fix | Impact |
|---|---|---|
| LIKE '%value%' | Full-text search | Index killed |
| Function on column | Sargable rewrite | Index killed |
| SELECT * | Name columns | I/O + memory waste |
| OFFSET pagination | Keyset cursor | O(N) → O(1) |
| OR in WHERE | UNION ALL | Index abandoned |
| NOT IN with NULLs | NOT EXISTS | Silent empty result |
| FLOAT for money | DECIMAL | Precision errors |
| N+1 queries | JOIN / eager load | 1000x query reduction |
| ORDER BY RAND() | TABLESAMPLE | O(N log N) → O(1) |
| No EXPLAIN | Always EXPLAIN first | Blind optimization |