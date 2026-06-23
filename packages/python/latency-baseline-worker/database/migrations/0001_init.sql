CREATE TABLE IF NOT EXISTS latency_checkpoints (
    model String,
    endpoint String,
    checkpoint_date Date,
    hour_of_day UInt8,
    p50_ttft_ms Float64,
    p95_ttft_ms Float64,
    p99_ttft_ms Float64,
    p50_total_ms Float64,
    p95_total_ms Float64,
    p99_total_ms Float64,
    sample_count UInt64,
    slo_violation_count UInt64,
    timestamp DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(timestamp)
ORDER BY (model, endpoint, checkpoint_date, hour_of_day);
