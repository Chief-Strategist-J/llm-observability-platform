import httpx
from shared.ports.embedding_provider import EmbeddingProviderPort, EmbeddingRequest, EmbeddingResponse
from shared.utils.hash import stable_embedding_key


class CloudflareEmbeddingClient(EmbeddingProviderPort):
    def __init__(self, account_id: str, api_token: str):
        self.account_id = account_id
        self.api_token = api_token

    def create_embedding(self, request: EmbeddingRequest, *, dimensions: int) -> EmbeddingResponse:
        # If no credentials, fallback to placeholder logic
        if not self.account_id or not self.api_token or self.account_id == "local-account":
             return EmbeddingResponse(
                embedding_key=stable_embedding_key(request.trace_id, request.span_id, request.text, prefix="emb_"),
                dimensions=dimensions,
                provider="cloudflare-mock",
            )

        model = request.model or "@cf/baai/bge-small-en-v1.5"
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{model}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        with httpx.Client() as client:
            resp = client.post(url, headers=headers, json={"text": request.text})
            resp.raise_for_status()
            # We don't store the actual embedding values here as per current architecture, 
            # we just confirm the call works and return the stable key.
            # In a real scenario, we might save the embedding to a database.
            
        return EmbeddingResponse(
            embedding_key=stable_embedding_key(request.trace_id, request.span_id, request.text, prefix="emb_"),
            dimensions=dimensions,
            provider="cloudflare",
        )
