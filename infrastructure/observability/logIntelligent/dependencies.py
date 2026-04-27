from __future__ import annotations

from dataclasses import dataclass

from infrastructure.observability.logIntelligent.domain.ports import (
    AnomalyPort,
    DriftPort,
    EmbeddingPort,
    FrequencyPort,
    ParserPort,
    SemanticIndexPort,
    StorageRouterPort,
    StructuralEnricherPort,
    TemplateStorePort,
    TraceIndexPort,
)
from infrastructure.observability.logIntelligent.enrichment.anomaly import IsolationForestLikeScorer
from infrastructure.observability.logIntelligent.enrichment.semantic import TemplateEmbeddingCache
from infrastructure.observability.logIntelligent.enrichment.structural import StructuralEnricher
from infrastructure.observability.logIntelligent.ingestion.drain3_parser import Drain3LikeParser
from infrastructure.observability.logIntelligent.ingestion.template_store import TemplateStore
from infrastructure.observability.logIntelligent.intelligence.drift import ADWINLikeDriftDetector
from infrastructure.observability.logIntelligent.intelligence.frequency import CountMinSketch
from infrastructure.observability.logIntelligent.intelligence.semantic_index import HNSWLikeIndex
from infrastructure.observability.logIntelligent.intelligence.trace_index import TraceInvertedIndex
from infrastructure.observability.logIntelligent.storage.router import StorageRouter


@dataclass
class PipelineDependencies:
    template_store: TemplateStorePort
    parser: ParserPort
    structural_enricher: StructuralEnricherPort
    embedding_cache: EmbeddingPort
    frequency: FrequencyPort
    drift: DriftPort
    anomaly: AnomalyPort
    semantic_index: SemanticIndexPort
    trace_index: TraceIndexPort
    storage_router: StorageRouterPort


def build_default_dependencies() -> PipelineDependencies:
    template_store = TemplateStore()
    return PipelineDependencies(
        template_store=template_store,
        parser=Drain3LikeParser(template_store),
        structural_enricher=StructuralEnricher(),
        embedding_cache=TemplateEmbeddingCache(dim=384),
        frequency=CountMinSketch(width=2000, depth=7),
        drift=ADWINLikeDriftDetector(max_window=50),
        anomaly=IsolationForestLikeScorer(),
        semantic_index=HNSWLikeIndex(),
        trace_index=TraceInvertedIndex(),
        storage_router=StorageRouter(),
    )
