import pytest

from shared.di.providers import resolve_embedding_provider
from shared.ports.embedding_provider import EmbeddingRequest


@pytest.mark.parametrize("name", ["cloudflare", "openai", "mock", "CLOUDFLARE", " openai "])
def test_resolve_provider_supported(name):
    provider = resolve_embedding_provider(name)
    out = provider.create_embedding(EmbeddingRequest("hello", "m", "t", "s"), dimensions=8)
    assert out.dimensions == 8
    assert out.provider in {"cloudflare", "openai", "mock"}


def test_resolve_provider_unknown_fails():
    with pytest.raises(ValueError):
        resolve_embedding_provider("anthropic")
