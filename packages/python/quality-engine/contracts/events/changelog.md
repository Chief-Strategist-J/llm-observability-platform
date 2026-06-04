# Contracts Changelog

## [1.0.0] — 2026-06-04
### Added
- `contracts/events/llm_spans_sampled.yaml` — AsyncAPI v2.6 schema for consumed topic `llm.spans.sampled` and produced topics:
  - `llm.quality.scores`
  - `llm.toxicity.flagged`
  - `alerts.quality.degradation`
- Consumer group: `quality-engine-group` (pinned in `src/worker/config.py`)
- Event schema version v1.0.0 pinned in `.contract-lock`
