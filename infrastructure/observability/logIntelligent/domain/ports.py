from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Protocol, Sequence, Tuple


class ParserPort(Protocol):
    def parse(self, message: str) -> Tuple[str, str]:
        ...


class StructuralEnricherPort(Protocol):
    def enrich(self, message: str) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, int]]:
        ...


class EmbeddingPort(Protocol):
    def get_or_compute(self, template_id: str, template_text: str) -> Tuple[float, ...]:
        ...


class FrequencyPort(Protocol):
    def add(self, key: str, count: int = 1) -> None:
        ...

    def estimate(self, key: str) -> int:
        ...


class DriftPort(Protocol):
    def update(self, template_id: str, count: int) -> bool:
        ...


class AnomalyPort(Protocol):
    def score(self, template_count: int, unseen_fields: int, drift_detected: bool) -> float:
        ...


class SemanticIndexPort(Protocol):
    def upsert(self, template_id: str, vector: Tuple[float, ...]) -> None:
        ...

    def query(self, vector: Sequence[float], k: int = 5) -> List[str]:
        ...


class TraceIndexPort(Protocol):
    def add(self, trace_id: Optional[str], line_id: str) -> None:
        ...

    def lookup(self, trace_id: str) -> List[str]:
        ...


class StorageRouterPort(Protocol):
    def route(self, event_time: datetime):
        ...


class TemplateStorePort(Protocol):
    def get(self, template_id: str) -> Optional[str]:
        ...
