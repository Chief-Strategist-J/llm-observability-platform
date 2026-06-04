from __future__ import annotations
from typing import Protocol
from handlers.span_quality.types import QualityScoreRow


class QualityScoreRepositoryPort(Protocol):
    """Port for persisting quality score rows to PostgreSQL."""

    def insert_score(self, row: QualityScoreRow) -> None: ...

    def get_window_avg(self, model: str, endpoint: str, window_seconds: int = 3600) -> float | None: ...
