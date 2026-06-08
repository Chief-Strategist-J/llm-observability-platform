from prometheus_client import Counter, Histogram

SPANS_PROCESSED = Counter(
    "quality_spans_processed_total",
    "Total LLM spans processed for quality",
    ["model", "endpoint"]
)

TOXICITY_SCORE = Histogram(
    "quality_toxicity_score",
    "Distribution of toxicity scores",
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

TOXIC_FLAGGED = Counter(
    "quality_toxic_flagged_total",
    "Total spans flagged for high toxicity",
    ["model", "endpoint"]
)

PIPELINE_LATENCY = Histogram(
    "quality_pipeline_latency_ms",
    "Pipeline latency in milliseconds"
)

SCORE_NULL = Counter(
    "quality_score_null_total",
    "Total null scores with reasons",
    ["reason"]
)
