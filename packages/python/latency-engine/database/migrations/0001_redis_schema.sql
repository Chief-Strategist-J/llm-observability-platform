-- migration:      0001
-- description:    Redis key schema for latency-engine DDSketches, TPOT lists, and SLO error counters
-- author:         latency-engine
-- date:           2026-06-17
-- depends_on:     none
-- reversible:     YES (FLUSHDB on isolated Redis instance)
-- lock_risk:      LOW
-- rows_affected:  schema only (no SQL — Redis key patterns)
-- reason:         Define Redis key naming conventions and data structures for latency metrics

--- KEY PATTERNS ---

-- TTFT DDSketch (String containing Base64 Proto-serialized DDSketch)
--   Key:    sketch:ttft:{model}:{hour_of_day}
--   Type:   STRING (Base64 protobuf string)
--   Example: sketch:ttft:gpt-4:14
--   TTL:    none

-- Total Latency DDSketch (String containing Base64 Proto-serialized DDSketch)
--   Key:    sketch:total:{model}:{endpoint}:{hour_of_day}
--   Type:   STRING (Base64 protobuf string)
--   Example: sketch:total:gpt-4:/v1/chat/completions:14
--   TTL:    none

-- Retry Total Latency DDSketch (String containing Base64 Proto-serialized DDSketch)
--   Key:    sketch:total:retry:{model}
--   Type:   STRING (Base64 protobuf string)
--   Example: sketch:total:retry:gpt-4
--   TTL:    none

-- TPOT Rolling List (List of floats representing TPOT latency values)
--   Key:    tpot:latest:{model}
--   Type:   LIST (elements: floats, max length: 1000)
--   Example: tpot:latest:gpt-4
--   TTL:    none

-- SLO Total Counter (String representing integer incremented on every span)
--   Key:    slo:total:{model}:{endpoint}:{minute_bucket}
--   Type:   STRING (integer)
--   Example: slo:total:gpt-4:/v1/chat/completions:29704200
--   TTL:    21600 seconds (6 hours auto-expire)

-- SLO Error Counter (String representing integer incremented on spans exceeding threshold)
--   Key:    slo:errors:{model}:{endpoint}:{minute_bucket}
--   Type:   STRING (integer)
--   Example: slo:errors:gpt-4:/v1/chat/completions:29704200
--   TTL:    21600 seconds (6 hours auto-expire)

-- Latency Attribution Span Details (Hash storing dns, tcp, queue, inference latencies)
--   Key:    attribution:{span_id}
--   Type:   HASH (fields: dns, tcp, queue, inference; values: float string)
--   Example: attribution:span-123
--   TTL:    300 seconds (5 minutes auto-expire)

-- Latency Attribution Hourly Average Aggregation (Hash summing attribution times per model/hour)
--   Key:    attr:avg:{model}:{hour_string}
--   Type:   HASH (fields: dns, tcp, queue, inference; values: float sums)
--   Example: attr:avg:gpt-4:2026061714
--   TTL:    604800 seconds (7 days auto-expire)

--- ROLLBACK ---
-- FLUSHDB on isolated latency-engine Redis instance
-- Or DEL all keys matching sketch:*, tpot:*, slo:*, attribution:*, attr:*
