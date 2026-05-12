"""Repository contract for persisting span records."""

from typing import Protocol


class SpanRepository(Protocol):
    def save(self, record: dict[str, object]) -> None: ...
