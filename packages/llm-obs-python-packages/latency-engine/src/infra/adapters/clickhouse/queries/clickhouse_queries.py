from __future__ import annotations

class ClickHouseQueryRegistry:
    BASELINE_QUERY = """
SELECT
    checkpoint_date,
    p99_ttft_ms,
    p99_total_ms
FROM latency_checkpoints
WHERE model = %(model)s
  AND hour_of_day = %(hour_of_day)s
  AND checkpoint_date >= today() - %(days)s
ORDER BY checkpoint_date DESC
LIMIT %(days)s
"""

    P99_TTFT_HISTORY_QUERY = """
SELECT p99_ttft_ms
FROM latency_checkpoints
WHERE model = %(model)s
  AND endpoint = %(endpoint)s
  AND hour_of_day = %(hour_of_day)s
  AND timestamp >= now() - INTERVAL 7 DAY
ORDER BY timestamp DESC
"""
