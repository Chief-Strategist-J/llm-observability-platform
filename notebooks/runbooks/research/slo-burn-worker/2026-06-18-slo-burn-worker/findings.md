# Findings — SLO Burn Rate Verification

## Summary of Results
Validation of the SLO Burn Rate calculations, Alert Routing thresholds, and Deduplication layers yielded the following key findings:

### 1. Burn Rate Mathematical Integrity (H-1)
* Verified that when the observed error rate is exactly equal to the target budget (e.g., $5\%$ error rate on a $95\%$ compliance target), the calculated burn rate is precisely $1.0$.
* Confirmed that a burn rate of $14.4$ represents consumption of the entire monthly budget in 50 hours, and $6.0$ consumes the budget in 120 hours.

### 2. Deduplication Lock Behavior (H-2)
* Tested the Redis TTL locks using mock adapters. Once an alert is fired for `(page, gpt-4o, /v1/chat/completions)`, a lock is successfully placed with a 3600-second TTL.
* Subsequent attempts to fire an alert within this window are correctly ignored by the deduplication logic.

### 3. ClickHouse Fallbacks (H-3)
* Simulating clickhouse connection timeouts demonstrated that the worker falls back gracefully to the standard $95\%$ threshold, maintaining continuity of operations.
