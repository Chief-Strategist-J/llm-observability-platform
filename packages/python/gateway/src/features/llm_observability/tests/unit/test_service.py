from features.llm_observability.service import build_span_record, prompt_hash
from python_shared.types.llm_observability import PriceCard


def test_prompt_hash_is_sha256_hex() -> None:
    value = prompt_hash("hello")
    assert len(value) == 64
    assert value.isalnum()


def test_build_span_record_computes_cost() -> None:
    record = build_span_record(
        model="gpt-4",
        prompt="hi",
        prompt_tokens=100,
        completion_tokens=50,
        finish_reason="stop",
        ttft_ms=110.0,
        total_ms=700.0,
        price_card=PriceCard(
            model="gpt-4", input_price_per_token=0.00001, output_price_per_token=0.00002
        ),
        sample_rate=0.0,
    )
    assert record["cost_usd"] == 0.002
    assert record["sampled"] is False
