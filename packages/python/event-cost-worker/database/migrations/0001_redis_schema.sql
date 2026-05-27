-- migration:      0001
-- description:    Redis key schema for cost-engine Fenwick Trees, Token Buckets, and Dedup Set
-- author:         event-cost-worker
-- date:           2026-05-27
-- depends_on:     none
-- reversible:     YES (FLUSHDB on isolated Redis instance)
-- lock_risk:      LOW
-- rows_affected:  schema only (no SQL — Redis key patterns)
-- reason:         Define Redis key naming conventions and data structures

--- KEY PATTERNS ---

-- Fenwick Tree (Hash per dimension/window/entity)
--   Key:    fenwick:{dimension}:{window}:{entity_key}
--   Type:   HASH (field = tree index, value = cumulative cost)
--   Dims:   org, project, service, model, user
--   Windows: 1h, 24h, 7d, 30d
--   Example: fenwick:model:1h:gpt-4
--   TTL:    none (managed by window rotation cron)

-- Token Bucket (String per org/project)
--   Key:    budget:tb:{org_id}:{project_id}
--   Type:   STRING (integer, can go negative)
--   Example: budget:tb:org-1:proj-1
--   TTL:    none (managed by SDK refill)

-- EWMA Baseline (String per service/model/hour — READ ONLY by cost-engine)
--   Key:    ewma:cost:{service}:{model}:{hour_of_week}
--   Type:   STRING (float)
--   Owner:  temporal-ewma-worker (cost-engine reads only)

-- Dedup Set (Set for idempotency guard)
--   Key:    dedup:cost_engine
--   Type:   SET (members = span_id strings)
--   TTL:    3600 seconds (auto-expire)
--   Example: dedup:cost_engine -> {"span-aaa", "span-bbb"}

--- ROLLBACK ---
-- FLUSHDB on isolated cost-engine Redis instance
-- Or DEL all keys matching fenwick:*, budget:tb:*, dedup:cost_engine
