# Contracts Changelog

## [1.0.0] — 2026-06-04
### Added
- `contracts/events/llm_spans_sampled.yaml` — AsyncAPI v2.6 schema for consumed topic `llm.spans.sampled` and produced topics:
  - `llm.quality.scores`
  - `llm.toxicity.flagged`
  - `alerts.quality.degradation`
- Consumer group: `quality-engine-group` (pinned in `src/worker/config.py`)
## [1.1.0] — 2026-06-09
### Added
- Added database schema support for `weights_used` JSONB column inside `quality_scores`.
- Integrated `LOW_COHERENCE` and `HALLUCINATION_RISK` flags back to ingestion metrics quality flags.
- Configured dynamic weight renormalization excluding perplexity by default.

## [1.2.0] — 2026-06-15
### Added
- `contracts/events/llm_spans_sampled.yaml` — Add `perplexity_score` field to `QualityScoreEvent`.
- `contracts/events/llm_spans_sampled.yaml` — Add `is_cold_start` field to `DegradationAlertEvent`.

