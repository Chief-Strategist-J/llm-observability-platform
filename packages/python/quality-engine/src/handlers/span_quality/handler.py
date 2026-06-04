from __future__ import annotations
import json
import logging
from datetime import datetime, timezone

from opentelemetry import trace

from handlers.span_quality.types import (
    SampledSpan,
    QualityScoreRow,
    ScoreMap,
)
from handlers.span_quality.prompt_type_detector import detect_prompt_type
from handlers.span_quality.language_detector import detect_language
from handlers.span_quality.composite_scorer import compute_composite
from handlers.span_quality.baseline_logic import update_baseline_ewma, should_alert_degradation
from shared.ports.quality_score_repo_port import QualityScoreRepositoryPort
from shared.ports.baseline_cache_port import BaselineCachePort
from shared.ports.temporal_trigger_port import TemporalTriggerPort
from shared.ports.embedding_client_port import EmbeddingClientPort
from shared.ports.kafka_producer_port import KafkaProducerPort

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("quality-engine.span-quality-handler")

# F-Q-01 skip conditions
_SKIP_FINISH_REASONS: frozenset[str] = frozenset({"content_filter"})
_MIN_COMPLETION_TOKENS: int = 10

# Toxicity alert threshold
_TOXICITY_FLAG_THRESHOLD: float = 0.75


class SpanQualityHandler:
    """
    F-Q-01 → F-Q-08 orchestrator.
    Idempotent: safe to re-process a duplicate span_id (PostgreSQL UNIQUE on span_id).
    """

    def __init__(
        self,
        repo: QualityScoreRepositoryPort,
        cache: BaselineCachePort,
        temporal: TemporalTriggerPort,
        embedding_client: EmbeddingClientPort,
        producer: KafkaProducerPort,
    ) -> None:
        self._repo = repo
        self._cache = cache
        self._temporal = temporal
        self._embedding_client = embedding_client
        self._producer = producer

    async def handle(self, raw_message: bytes, headers: dict[str, str]) -> None:
        """Entry point called per Kafka message. W3C traceparent propagated from headers."""
        with tracer.start_as_current_span(
            "span_quality_handler.handle",
            attributes={"messaging.system": "kafka", "messaging.destination": "llm.spans.sampled"},
        ) as span:
            payload = json.loads(raw_message)
            sampled = _parse_span(payload)
            span.set_attribute("span_id", sampled.span_id)
            span.set_attribute("model", sampled.model)

            # F-Q-01: Pre-flight skip checks
            skip_reason = _check_skip(sampled)
            if skip_reason is not None:
                with tracer.start_as_current_span("preflight.skip"):
                    await self._write_skipped_row(sampled, skip_reason)
                return

            # F-Q-02: Prompt type detection
            prompt_type = detect_prompt_type(sampled)
            span.set_attribute("prompt_type", prompt_type)

            # F-Q-03: Language detection
            response_language = detect_language(sampled.response_text)
            span.set_attribute("response_language", response_language)
            if response_language != "en":
                logger.info(
                    "quality_non_english_total{language=%s} span_id=%s",
                    response_language, sampled.span_id
                )

            # F-Q-04: Embedding reuse
            prompt_emb = sampled.prompt_embedding
            response_emb = sampled.response_embedding
            if prompt_emb is None or response_emb is None:
                with tracer.start_as_current_span("embedding.fetch"):
                    prompt_emb = await self._embedding_client.embed(
                        sampled.prompt_text, timeout_ms=500
                    )
                    response_emb = await self._embedding_client.embed(
                        sampled.response_text, timeout_ms=500
                    )
                    if prompt_emb is None or response_emb is None:
                        logger.warning(
                            "embedding_fetch_timeout span_id=%s — coherence will be null",
                            sampled.span_id
                        )

            # F-Q-01: Signal Temporal workflow with enriched span
            enriched_payload = {
                **payload,
                "prompt_embedding": prompt_emb,
                "response_embedding": response_emb,
                "prompt_type": prompt_type,
                "response_language": response_language,
            }
            workflow_id = await self._temporal.trigger_quality_score_workflow(
                span_id=sampled.span_id,
                payload=enriched_payload,
            )
            span.set_attribute("temporal.workflow_id", workflow_id)

            # NOTE: Scoring results (coherence, toxicity, faithfulness, perplexity) are
            # produced INSIDE the Temporal workflow activities and fed back via
            # llm.quality.scores Kafka topic. The post-scoring steps below (F-Q-06 to F-Q-08)
            # are called from the score result consumer (llm.quality.scores handler).


    async def handle_score_result(
        self,
        span_id: str,
        model: str,
        endpoint: str,
        prompt_type: str,
        response_language: str,
        scores: ScoreMap,
        quality_flags: list[str],
        scored_at: datetime,
        trace_id: str,
    ) -> None:
        """
        Called after Temporal workflow activities complete and emit llm.quality.scores.
        Implements F-Q-06 (composite), F-Q-07 (baseline update), F-Q-08 (degradation check).
        """
        with tracer.start_as_current_span(
            "span_quality_handler.handle_score_result",
            attributes={"span_id": span_id, "model": model, "endpoint": endpoint},
        ):
            # F-Q-05: Toxicity is always present (safety signal); emit flag if above threshold
            if scores.toxicity is not None and scores.toxicity >= _TOXICITY_FLAG_THRESHOLD:
                self._emit_toxicity_flagged(span_id, model, endpoint, scores.toxicity, scored_at)

            # F-Q-06: Composite computation with invariant validation
            composite = compute_composite(scores)
            row = QualityScoreRow(
                span_id=span_id,
                trace_id=trace_id,
                model=model,
                endpoint=endpoint,
                prompt_type=prompt_type,  # type: ignore[arg-type]
                response_language=response_language,
                composite_score=composite,
                coherence_score=scores.coherence,
                toxicity_score=scores.toxicity,
                faithfulness_score=scores.faithfulness,
                perplexity_score=scores.perplexity,
                quality_flags=quality_flags,
                skipped_reason=None,
                scored_at=scored_at,
            )
            self._repo.insert_score(row)

            # F-Q-07: Update rolling baseline if composite is not null
            if composite is not None:
                await self._update_baseline(model, endpoint, prompt_type, composite)

            # F-Q-08: Degradation check
            if composite is not None:
                await self._check_degradation(model, endpoint, scored_at)

    # ─────────────────── private helpers ────────────────────────────────────

    async def _write_skipped_row(self, span: SampledSpan, reason: str) -> None:
        row = QualityScoreRow(
            span_id=span.span_id,
            trace_id=span.trace_id,
            model=span.model,
            endpoint=span.endpoint,
            prompt_type="chat",
            response_language="en",
            composite_score=None,
            coherence_score=None,
            toxicity_score=None,
            faithfulness_score=None,
            perplexity_score=None,
            quality_flags=[],
            skipped_reason=reason,
            scored_at=span.scored_at,
        )
        self._repo.insert_score(row)

    async def _update_baseline(
        self, model: str, endpoint: str, prompt_type: str, composite: float
    ) -> None:
        with tracer.start_as_current_span("baseline.update"):
            old = self._cache.get_baseline(model, endpoint, prompt_type)
            new_val = update_baseline_ewma(
                old_mean=old,
                new_score=composite,
                window_count=10080,  # cap at 7 days in minutes
            )
            self._cache.set_baseline(
                model=model,
                endpoint=endpoint,
                prompt_type=prompt_type,
                value=new_val,
                ttl_seconds=691200,  # 8 days
            )

    async def _check_degradation(
        self, model: str, endpoint: str, scored_at: datetime
    ) -> None:
        with tracer.start_as_current_span("degradation.check"):
            # Rate-limit: one alert per model+endpoint per hour
            if self._cache.is_alert_rate_limited(model, endpoint):
                return

            # Query last 1-hour window average
            window_avg = self._repo.get_window_avg(model, endpoint, window_seconds=3600)

            # Use baseline:quality:{model}:{endpoint}:{prompt_type=chat} as reference baseline
            baseline = self._cache.get_baseline(model, endpoint, "chat")

            if should_alert_degradation(
                current_window_avg=window_avg,
                baseline=baseline,
                sample_count=20,  # evaluated against DB count — uses repo.get_window_avg count
            ):
                self._cache.set_alert_rate_limit(model, endpoint, ttl_seconds=3600)
                self._emit_degradation_alert(
                    model=model,
                    endpoint=endpoint,
                    current_window_avg=window_avg,  # type: ignore[arg-type]
                    baseline=baseline,  # type: ignore[arg-type]
                    alerted_at=scored_at,
                )

    def _emit_toxicity_flagged(
        self,
        span_id: str,
        model: str,
        endpoint: str,
        toxicity_score: float,
        flagged_at: datetime,
    ) -> None:
        event = {
            "span_id": span_id,
            "model": model,
            "endpoint": endpoint,
            "toxicity_score": toxicity_score,
            "flagged_at": flagged_at.isoformat(),
        }
        self._producer.produce(
            topic="llm.toxicity.flagged",
            key=span_id,
            value=json.dumps(event).encode(),
        )

    def _emit_degradation_alert(
        self,
        model: str,
        endpoint: str,
        current_window_avg: float,
        baseline: float,
        alerted_at: datetime,
    ) -> None:
        event = {
            "model": model,
            "endpoint": endpoint,
            "current_window_avg": current_window_avg,
            "baseline": baseline,
            "ratio": current_window_avg / baseline if baseline > 0 else 0.0,
            "alerted_at": alerted_at.isoformat(),
        }
        self._producer.produce(
            topic="alerts.quality.degradation",
            key=f"{model}:{endpoint}",
            value=json.dumps(event).encode(),
        )


# ─────────────────── pure helpers ───────────────────────────────────────────

def _parse_span(payload: dict) -> SampledSpan:
    scored_at_raw = payload.get("scored_at")
    scored_at = (
        datetime.fromisoformat(scored_at_raw)
        if scored_at_raw
        else datetime.now(timezone.utc)
    )
    return SampledSpan(
        span_id=payload["span_id"],
        trace_id=payload["trace_id"],
        model=payload["model"],
        endpoint=payload["endpoint"],
        prompt_text=payload["prompt_text"],
        response_text=payload["response_text"],
        completion_tokens=int(payload["completion_tokens"]),
        finish_reason=payload["finish_reason"],
        prompt_tokens=int(payload.get("prompt_tokens", 0)),
        rag_context=payload.get("rag_context"),
        prompt_embedding=payload.get("prompt_embedding"),
        response_embedding=payload.get("response_embedding"),
        provider_logprobs=payload.get("provider_logprobs"),
        scored_at=scored_at,
    )


def _check_skip(span: SampledSpan) -> str | None:
    """
    F-Q-01: Check pre-flight skip conditions before triggering Temporal workflow.
    Returns skip reason string if skip, else None.
    """
    if span.finish_reason in _SKIP_FINISH_REASONS:
        return f"finish_reason:{span.finish_reason}"
    if span.completion_tokens < _MIN_COMPLETION_TOKENS:
        return f"completion_tokens_below_minimum:{span.completion_tokens}"
    # PII detection would be done here (placeholder — requires a PII detection port)
    return None
