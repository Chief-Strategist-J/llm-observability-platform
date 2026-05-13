-- migration:      0001
-- description:    initialize llm_spans table in ClickHouse
-- author:         antigravity
-- date:           2026-05-13
-- depends_on:     NONE
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         initial schema setup for high-throughput OLAP span storage

CREATE TABLE IF NOT EXISTS llm_spans (
    span_id UUID,
    trace_id Nullable(UUID),
    parent_span_id Nullable(UUID),
    schema_version UInt8,
    model LowCardinality(String),
    provider LowCardinality(String),
    service_name LowCardinality(String),
    endpoint String,
    environment Enum8('production' = 1, 'staging' = 2, 'dev' = 3),
    user_id Nullable(String),
    session_id Nullable(String),
    prompt_tokens UInt32,
    completion_tokens UInt32,
    latency_ms_ttft Nullable(UInt32),
    latency_ms_total UInt32,
    finish_reason Enum8(
        'stop' = 1, 
        'length' = 2, 
        'content_filter' = 3, 
        'timeout' = 4, 
        'tool_calls' = 5, 
        'cache_hit' = 6, 
        'client_disconnect' = 7
    ),
    cost_usd_micro UInt64,
    price_version String,
    token_count_method Enum8('tiktoken' = 1, 'estimated' = 2),
    is_sampled UInt8,
    retry_count UInt8,
    attempted_models Array(String),
    pii_detected UInt8,
    injection_attempt UInt8,
    timestamp_utc DateTime64(3, 'UTC'),
    prompt_hash Nullable(FixedString(64)),
    prompt_embedding Array(Float32),
    response_embedding Array(Float32),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp_utc)
ORDER BY (service_name, model, timestamp_utc, span_id)
SETTINGS index_granularity = 8192;
