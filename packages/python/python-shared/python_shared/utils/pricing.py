"""Pure pricing helpers (no IO)."""

from python_shared.types.llm_observability import PriceCard, TokenUsage


def compute_cost_usd(usage: TokenUsage, price: PriceCard) -> float:
    """Compute per-call cost in O(1)."""
    return (usage.prompt_tokens * price.input_price_per_token) + (
        usage.completion_tokens * price.output_price_per_token
    )
