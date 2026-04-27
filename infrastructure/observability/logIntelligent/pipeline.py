from __future__ import annotations

from typing import Dict, List

from infrastructure.observability.logIntelligent.dependencies import PipelineDependencies, build_default_dependencies
from infrastructure.observability.logIntelligent.models import ParsedLogRecord, RawLogRecord


class LogIntelligencePipeline:
    def __init__(self, dependencies: PipelineDependencies | None = None) -> None:
        resolved = dependencies or build_default_dependencies()
        self.template_store = resolved.template_store
        self.parser = resolved.parser
        self.structural_enricher = resolved.structural_enricher
        self.embedding_cache = resolved.embedding_cache
        self.frequency = resolved.frequency
        self.drift = resolved.drift
        self.anomaly = resolved.anomaly
        self.semantic_index = resolved.semantic_index
        self.trace_index = resolved.trace_index
        self.storage_router = resolved.storage_router
        self._parsed_by_line: Dict[str, ParsedLogRecord] = {}

    def ingest(self, log: RawLogRecord) -> ParsedLogRecord:
        template_id, template_text = self.parser.parse(log.message)
        self.frequency.add(template_id)
        template_count = self.frequency.estimate(template_id)

        extracted, normalized, cardinality = self.structural_enricher.enrich(log.message)
        drift_detected = self.drift.update(template_id, template_count)
        unseen_field_count = sum(1 for count in cardinality.values() if count == 1)
        anomaly_score = self.anomaly.score(template_count, unseen_field_count, drift_detected)

        embedding = self.embedding_cache.get_or_compute(template_id, template_text)
        self.semantic_index.upsert(template_id, embedding)
        self.trace_index.add(normalized.get("trace_id"), log.line_id)

        tier = self.storage_router.route(log.received_at).tier
        parsed = ParsedLogRecord(
            raw=log,
            template_id=template_id,
            template_text=template_text,
            extracted_fields=extracted,
            normalized_fields=normalized,
            embedding=embedding,
            anomaly_score=anomaly_score,
            storage_tier=tier,
        )
        self._parsed_by_line[log.line_id] = parsed
        return parsed

    def similar_templates(self, template_id: str, k: int = 5) -> List[str]:
        template_text = self.template_store.get(template_id)
        if not template_text:
            return []
        vector = self.embedding_cache.get_or_compute(template_id, template_text)
        return self.semantic_index.query(vector, k=k)

    def get_log(self, line_id: str) -> ParsedLogRecord | None:
        return self._parsed_by_line.get(line_id)
