from __future__ import annotations
import json
import logging
import math
from typing import List
from datetime import datetime, timezone
from dataclasses import dataclass
from temporalio import activity
from opentelemetry import trace
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.redis_port import RedisPort
from shared.ports.postgres_port import PostgresPort
from shared.ports.metrics_port import MetricsPort
from shared.ports.scorer_client_port import ScorerClientPort
from shared.ports.kafka_producer_port import KafkaProducerPort
from features.quality_baseline.types import BaselineRecomputeResult
from features.quality_baseline.service import QualityBaselineService

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer("quality-baseline-worker")

@dataclass
class AggregateCompositeInput:
    payload: dict
    coherence: float | None
    toxicity: float | None
    faithfulness: float | None
    perplexity: float | None
    prompt_type: str
    response_language: str

class QualityBaselineActivities:
    def __init__(
        self,
        clickhouse: ClickHousePort,
        redis: RedisPort,
        postgres: PostgresPort,
        metrics: MetricsPort,
        scorer_client: ScorerClientPort,
        kafka_producer: KafkaProducerPort,
    ):
        self.clickhouse = clickhouse
        self.redis = redis
        self.postgres = postgres
        self.metrics = metrics
        self.scorer_client = scorer_client
        self.kafka_producer = kafka_producer

    @activity.defn(name="recompute_baseline_scores")
    async def recompute_baseline_scores(self) -> List[BaselineRecomputeResult]:
        return self.postgres.get_rolling_baselines()

    @activity.defn(name="write_redis_baselines")
    async def write_redis_baselines(self, baselines: List[BaselineRecomputeResult]) -> int:
        for b in baselines:
            self.redis.set_baseline_quality(
                model=b.model,
                endpoint=b.endpoint,
                prompt_type=b.prompt_type,
                score=b.avg_score
            )
        self.metrics.record_baseline_updates(len(baselines))
        return len(baselines)

    @activity.defn(name="rollup_quality_trend")
    async def rollup_quality_trend(self) -> int:
        return QualityBaselineService.rollup_yesterday_scores(
            postgres=self.postgres,
            clickhouse=self.clickhouse,
            metrics=self.metrics
        )

    @activity.defn(name="detect_language")
    async def detect_language(self, response_text: str | None) -> str:
        with _tracer.start_as_current_span("detect_language") as span:
            span.set_attribute("activity.name", "detect_language")
            if not response_text:
                return "en"
            try:
                from langdetect import detect
                return detect(response_text)
            except Exception:
                return "en"

    @activity.defn(name="detect_prompt_type")
    async def detect_prompt_type(self, prompt_text: str, response_text: str, rag_context: str | None) -> str:
        with _tracer.start_as_current_span("detect_prompt_type") as span:
            span.set_attribute("activity.name", "detect_prompt_type")
            if rag_context is not None:
                return "rag"
            if "```" in prompt_text:
                return "code"
            words = response_text.strip().split()
            if len(words) <= 3:
                return "classification"
            return "chat"

    @activity.defn(name="compute_coherence")
    async def compute_coherence(self, payload: dict, prompt_type: str | None) -> float | None:
        with _tracer.start_as_current_span("compute_coherence") as span:
            span.set_attribute("activity.name", "compute_coherence")
            span.set_attribute("span_id", payload.get("span_id", ""))
            span.set_attribute("trace_id", payload.get("trace_id", ""))
            coh = payload.get("coherence_score")
            if coh is not None:
                return coh
            return self.scorer_client.get_coherence_score(
                trace_id=payload["trace_id"],
                span_id=payload["span_id"],
                prompt_type=prompt_type or payload.get("prompt_type"),
                pii_detected=payload.get("pii_detected"),
                prompt_embedding=payload.get("prompt_embedding"),
                response_embedding=payload.get("response_embedding"),
            )

    @activity.defn(name="compute_toxicity")
    async def compute_toxicity(self, payload: dict) -> float | None:
        with _tracer.start_as_current_span("compute_toxicity") as span:
            span.set_attribute("activity.name", "compute_toxicity")
            span.set_attribute("span_id", payload.get("span_id", ""))
            span.set_attribute("trace_id", payload.get("trace_id", ""))
            tox = payload.get("toxicity_score")
            if tox is not None:
                return tox
            return self.scorer_client.get_toxicity_score(
                trace_id=payload["trace_id"],
                span_id=payload["span_id"],
                response_text=payload.get("response_text"),
            )

    @activity.defn(name="compute_faithfulness")
    async def compute_faithfulness(self, payload: dict) -> float | None:
        with _tracer.start_as_current_span("compute_faithfulness") as span:
            span.set_attribute("activity.name", "compute_faithfulness")
            span.set_attribute("span_id", payload.get("span_id", ""))
            span.set_attribute("trace_id", payload.get("trace_id", ""))
            faith = payload.get("faithfulness_score")
            if faith is not None:
                return faith
            return self.scorer_client.get_faithfulness_score(
                trace_id=payload["trace_id"],
                span_id=payload["span_id"],
                response_text=payload.get("response_text"),
                completion_tokens=payload.get("completion_tokens"),
                rag_context=payload.get("rag_context"),
                finish_reason=payload.get("finish_reason"),
            )

    @activity.defn(name="compute_perplexity")
    async def compute_perplexity(self, payload: dict, prompt_type: str | None) -> float | None:
        with _tracer.start_as_current_span("compute_perplexity") as span:
            span.set_attribute("activity.name", "compute_perplexity")
            span.set_attribute("span_id", payload.get("span_id", ""))
            span.set_attribute("trace_id", payload.get("trace_id", ""))
            perp = payload.get("perplexity_score") or payload.get("perplexity")
            if perp is not None:
                return perp
            return self.scorer_client.get_perplexity_value(
                trace_id=payload["trace_id"],
                span_id=payload["span_id"],
                response_text=payload.get("response_text"),
                completion_tokens=payload.get("completion_tokens"),
                prompt_type=prompt_type or payload.get("prompt_type"),
                token_logprobs=payload.get("token_logprobs"),
                finish_reason=payload.get("finish_reason"),
            )

    @activity.defn(name="aggregate_composite")
    async def aggregate_composite(self, inp: AggregateCompositeInput) -> dict:
        with _tracer.start_as_current_span("aggregate_composite") as span:
            span.set_attribute("activity.name", "aggregate_composite")
            payload = inp.payload
            coherence = inp.coherence
            toxicity = inp.toxicity
            faithfulness = inp.faithfulness
            perplexity = inp.perplexity
            prompt_type = inp.prompt_type
            response_language = inp.response_language

            span.set_attribute("span_id", payload.get("span_id", ""))
            span.set_attribute("trace_id", payload.get("trace_id", ""))

            # 1. Calculate composite score
            # Using Phase 3 composite formula
            BASE_WEIGHTS = {
                "coherence": 0.30,
                "faithfulness": 0.40,
                "toxicity": 0.20,
                "perplexity": 0.0,
            }
            S = []
            raw_contributions = {}

            if coherence is not None:
                S.append("coherence")
                raw_contributions["coherence"] = coherence

            if faithfulness is not None:
                S.append("faithfulness")
                raw_contributions["faithfulness"] = faithfulness

            if toxicity is not None:
                S.append("toxicity")
                raw_contributions["toxicity"] = 1.0 - toxicity

            if perplexity is not None:
                S.append("perplexity")
                perplexity_baseline = payload.get("perplexity_baseline", 2.0)
                use_literal_formula = payload.get("use_literal_formula", False)
                if perplexity <= 0.0 or perplexity_baseline <= 0.0:
                    c_perp = 0.0
                elif use_literal_formula:
                    denom = math.log(perplexity_baseline * 3.0)
                    if denom != 0.0:
                        c_perp = max(0.0, min(1.0, 1.0 - (math.log(perplexity) / denom)))
                    else:
                        c_perp = 0.0
                else:
                    c_perp = max(0.0, min(1.0, 1.0 - (math.log(perplexity / perplexity_baseline) / math.log(3.0))))
                raw_contributions["perplexity"] = c_perp

            if not S:
                composite = None
            else:
                active_weights = {k: BASE_WEIGHTS[k] for k in S if BASE_WEIGHTS[k] > 0.0}
                total_weight = sum(active_weights.values())
                normalized_weights = {}
                if total_weight > 0.0:
                    normalized_weights = {k: v / total_weight for k, v in active_weights.items()}
                composite = sum(normalized_weights[k] * raw_contributions[k] for k in active_weights) if active_weights else None

            # 2. Validate Invariants (INV-Q-01 through INV-Q-07)
            scores_map = {
                "coherence": coherence,
                "toxicity": toxicity,
                "faithfulness": faithfulness,
                "perplexity": perplexity,
            }
            self._validate_invariants(scores_map, composite)

            # 3. Publish to llm.quality.scores Kafka topic
            scored_at = payload.get("scored_at")
            if not scored_at:
                scored_at = datetime.now(timezone.utc).isoformat()
            
            event = {
                "span_id": payload["span_id"],
                "trace_id": payload["trace_id"],
                "model": payload["model"],
                "endpoint": payload["endpoint"],
                "prompt_type": prompt_type,
                "response_language": response_language,
                "scores": {
                    "coherence": coherence,
                    "toxicity": toxicity,
                    "faithfulness": faithfulness,
                    "perplexity": perplexity,
                },
                "quality_flags": payload.get("quality_flags", []),
                "scored_at": scored_at,
                "user_id": payload.get("user_id"),
            }

            self.kafka_producer.produce(
                topic="llm.quality.scores",
                key=payload["span_id"],
                value=json.dumps(event).encode(),
            )
            self.kafka_producer.flush()

            return event

    def _validate_invariants(self, scores: dict, composite: float | None) -> None:
        # INV-Q-01: composite score in [0, 1] (or null)
        if composite is not None and not (0.0 <= composite <= 1.0):
            logger.warning("invariant_violation_total{invariant_id=INV-Q-01} composite=%s", composite)
            self.metrics.record_invariant_violation("INV-Q-01")

        # INV-Q-02: coherence in [0, 1] if present
        coherence = scores.get("coherence")
        if coherence is not None and not (0.0 <= coherence <= 1.0):
            logger.warning("invariant_violation_total{invariant_id=INV-Q-02} coherence=%s", coherence)
            self.metrics.record_invariant_violation("INV-Q-02")

        # INV-Q-03: toxicity in [0, 1] if present
        toxicity = scores.get("toxicity")
        if toxicity is not None and not (0.0 <= toxicity <= 1.0):
            logger.warning("invariant_violation_total{invariant_id=INV-Q-03} toxicity=%s", toxicity)
            self.metrics.record_invariant_violation("INV-Q-03")

        # INV-Q-04: faithfulness in [0, 1] if present
        faithfulness = scores.get("faithfulness")
        if faithfulness is not None and not (0.0 <= faithfulness <= 1.0):
            logger.warning("invariant_violation_total{invariant_id=INV-Q-04} faithfulness=%s", faithfulness)
            self.metrics.record_invariant_violation("INV-Q-04")

        # INV-Q-05: perplexity_score non-negative if present
        perplexity = scores.get("perplexity")
        if perplexity is not None and perplexity < 0.0:
            logger.warning("invariant_violation_total{invariant_id=INV-Q-05} perplexity=%s", perplexity)
            self.metrics.record_invariant_violation("INV-Q-05")

        # INV-Q-06: at least one score present if composite is not null
        if composite is not None:
            has_any = any([coherence is not None, toxicity is not None, faithfulness is not None, perplexity is not None])
            if not has_any:
                logger.warning("invariant_violation_total{invariant_id=INV-Q-06} no_scores_for_non_null_composite")
                self.metrics.record_invariant_violation("INV-Q-06")

        # INV-Q-07: toxicity always present (unless model unavailable)
        if toxicity is None:
            logger.warning("invariant_violation_total{invariant_id=INV-Q-07} toxicity_is_null")
            self.metrics.record_invariant_violation("INV-Q-07")
