from python_shared.types.llm_observability import PriceCard, TokenUsage
from python_shared.utils.pricing import compute_cost_usd


def test_compute_cost_usd() -> None:
    usage = TokenUsage(prompt_tokens=200, completion_tokens=100)
    card = PriceCard(model="gpt-4", input_price_per_token=0.00001, output_price_per_token=0.00002)
    assert compute_cost_usd(usage, card) == 0.004
