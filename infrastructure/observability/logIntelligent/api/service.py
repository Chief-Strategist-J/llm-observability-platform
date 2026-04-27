from __future__ import annotations

from infrastructure.observability.logIntelligent.api.schemas import (
    CapabilityMetricsResponse,
    IngestLogRequest,
    IngestLogResponse,
    LogLookupResponse,
    SimilarTemplatesResponse,
    TraceLookupResponse,
)
from infrastructure.observability.logIntelligent.models import RawLogRecord
from infrastructure.observability.logIntelligent.pipeline import LogIntelligencePipeline


class LogIntelligenceService:
    def __init__(self, pipeline: LogIntelligencePipeline) -> None:
        self.pipeline = pipeline

    def ingest(self, payload: IngestLogRequest) -> IngestLogResponse:
        parsed = self.pipeline.ingest(RawLogRecord(line_id=payload.line_id, message=payload.message))
        return self._to_response(parsed)

    def ingest_batch(self, payloads: list[IngestLogRequest]) -> list[IngestLogResponse]:
        return [self.ingest(item) for item in payloads]

    def similar_templates(self, template_id: str, k: int = 5) -> SimilarTemplatesResponse:
        neighbors = self.pipeline.similar_templates(template_id, k=k)
        return SimilarTemplatesResponse(template_id=template_id, neighbors=neighbors)

    def trace_lookup(self, trace_id: str) -> TraceLookupResponse:
        line_ids = self.pipeline.trace_index.lookup(trace_id)
        return TraceLookupResponse(trace_id=trace_id, line_ids=line_ids)

    def log_lookup(self, line_id: str) -> LogLookupResponse:
        item = self.pipeline.get_log(line_id)
        if item is None:
            return LogLookupResponse(found=False, item=None)
        return LogLookupResponse(found=True, item=self._to_response(item))

    def capability_metrics(self) -> CapabilityMetricsResponse:
        implemented = [
            "trie_template_store",
            "structural_enrichment",
            "count_min_frequency",
            "trace_inverted_index",
            "tier_routing_logic",
        ]
        partial = [
            "drain3_online_parsing",
            "minilm_embeddings",
            "isolation_forest_scoring",
            "adwin_drift_detection",
            "semantic_nn_search",
        ]
        pending = [
            "loki_clickhouse_s3_writers",
            "federated_query_router",
            "compression_pipeline",
            "accuracy_benchmark_suite",
        ]
        total = len(implemented) + len(partial) + len(pending)
        readiness_score = (len(implemented) + 0.5 * len(partial)) / total
        return CapabilityMetricsResponse(
            implemented=implemented,
            partial=partial,
            pending=pending,
            readiness_score=round(readiness_score, 4),
        )

    def _to_response(self, parsed) -> IngestLogResponse:
        return IngestLogResponse(
            line_id=parsed.raw.line_id,
            template_id=parsed.template_id,
            template_text=parsed.template_text,
            normalized_fields=parsed.normalized_fields,
            anomaly_score=parsed.anomaly_score,
            storage_tier=parsed.storage_tier,
        )
