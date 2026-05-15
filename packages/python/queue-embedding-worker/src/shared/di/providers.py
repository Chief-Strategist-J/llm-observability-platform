from infra.clients.cloudflare_embeddings import CloudflareEmbeddingClient
from infra.clients.mock_embeddings import MockEmbeddingClient
from infra.clients.openai_embeddings import OpenAIEmbeddingClient
from shared.ports.embedding_provider import EmbeddingProviderPort


_PROVIDER_MAP = {
    "cloudflare": CloudflareEmbeddingClient,
    "openai": OpenAIEmbeddingClient,
    "mock": MockEmbeddingClient,
}


def resolve_embedding_provider(name: str, account_id: str = "", api_token: str = "") -> EmbeddingProviderPort:
    key = (name or "cloudflare").strip().lower()
    provider_cls = _PROVIDER_MAP.get(key)
    if provider_cls is None:
        raise ValueError(f"Unknown embedding provider '{name}'")
    
    if key == "cloudflare":
        return provider_cls(account_id=account_id, api_token=api_token)
    return provider_cls()
