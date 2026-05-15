import pytest

from features.enrich_span.index import enrich_span


def test_feature_enrich_span_success():
    out = enrich_span(
        {
            "trace_id": "t1",
            "span_id": "s1",
            "text": "hello",
            "model": "text-embedding-3-small",
        },
        dimensions=64,
    )
    assert out["dimensions"] == 64
    assert out["embedding_key"].startswith("emb_")


@pytest.mark.parametrize("provider", ["cloudflare", "openai", "mock"])
def test_feature_enrich_span_provider_switch(provider):
    out = enrich_span(
        {
            "trace_id": "t1",
            "span_id": "s1",
            "text": "hello",
            "model": "text-embedding-3-small",
        },
        dimensions=64,
        provider_name=provider,
    )
    assert out["provider"] == provider
