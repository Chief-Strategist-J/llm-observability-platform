# Hypothesis: Quality Baseline Worker Implementation and Rollup Verification

## Objective
Verify the correctness of rolling baseline averages, Temporal scheduled workflow registration, and multi-database connectivity (PostgreSQL, ClickHouse, Redis) for the `quality-baseline-worker`.

## Hypotheses
1. **Rolling Baseline Calculation Accuracy (F-Q-09)**: PostgreSQL queries correctly aggregate quality scores over the 7-day trailing window and project them onto Redis keys without hot-path overhead.
2. **Daily Rollup Aggregation correctness (F-Q-10)**: Yesterday's prompt/quality score summaries are computed exactly and written cleanly to ClickHouse without row duplication or data gaps.
3. **Alerting Threshold Accuracy**: Significant quality score drops trigger message publication to the Kafka degradation topic.
4. **Hexagonal isolation behaves reliably**: Mocking ports allows running full workflow simulations locally without spinning up physical databases.
