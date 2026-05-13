-- migration:      0001
-- description:    initialize llm_spans table in PostgreSQL with partitioning
-- author:         antigravity
-- date:           2026-05-13
-- depends_on:     NONE
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         initial schema setup for OLTP span storage and vector search

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS llm_spans (
    id BIGSERIAL NOT NULL,
    span_id UUID NOT NULL,
    trace_id UUID,
    parent_span_id UUID,
    schema_version SMALLINT NOT NULL DEFAULT 1,
    model VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    endpoint TEXT NOT NULL,
    environment VARCHAR(50) NOT NULL CHECK (environment IN ('production', 'staging', 'dev')),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    latency_ms_ttft INTEGER,
    latency_ms_total INTEGER NOT NULL,
    finish_reason VARCHAR(50) NOT NULL CHECK (finish_reason IN ('stop', 'length', 'content_filter', 'timeout', 'tool_calls', 'cache_hit', 'client_disconnect')),
    cost_usd_micro BIGINT NOT NULL,
    price_version VARCHAR(100) NOT NULL,
    token_count_method VARCHAR(50) NOT NULL CHECK (token_count_method IN ('tiktoken', 'estimated')),
    is_sampled BOOLEAN NOT NULL DEFAULT FALSE,
    retry_count SMALLINT NOT NULL DEFAULT 0,
    attempted_models TEXT[],
    pii_detected BOOLEAN NOT NULL DEFAULT FALSE,
    injection_attempt BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    prompt_hash CHAR(64),
    prompt_embedding vector(384),
    response_embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (span_id, timestamp_utc)
) PARTITION BY RANGE (timestamp_utc);

-- Initial partitions (e.g., for May and June 2026)
CREATE TABLE llm_spans_2026_05 PARTITION OF llm_spans
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE llm_spans_2026_06 PARTITION OF llm_spans
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- Indexes
CREATE INDEX idx_llm_spans_trace_id ON llm_spans (trace_id);
CREATE INDEX idx_llm_spans_service_model ON llm_spans (service_name, model);
CREATE INDEX idx_llm_spans_timestamp ON llm_spans (timestamp_utc DESC);
