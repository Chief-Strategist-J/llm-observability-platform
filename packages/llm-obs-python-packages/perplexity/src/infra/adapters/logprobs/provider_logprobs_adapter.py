from __future__ import annotations

import math


class ProviderLogprobsAdapter:
    def compute(
        self,
        token_logprobs: list[float] | None,
        response_text: str,
    ) -> float | None:
        if not token_logprobs:
            return None
        n = len(token_logprobs)
        if n == 0:
            return None
        return math.exp(-sum(token_logprobs) / n)
