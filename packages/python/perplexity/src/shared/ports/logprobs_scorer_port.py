from __future__ import annotations

from typing import Protocol


class LogprobsScorerPort(Protocol):
    def compute(
        self,
        token_logprobs: list[float] | None,
        response_text: str,
    ) -> float | None: ...
