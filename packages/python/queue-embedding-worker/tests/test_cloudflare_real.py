import os
import pytest
from features.enrich_span.service import enrich_span

def test_cloudflare_real_call():
    # Credentials should be set in environment variables
    env = {
        "CF_ACCOUNT_ID": os.getenv("CF_ACCOUNT_ID"),
        "CF_API_TOKEN": os.getenv("CF_API_TOKEN"),
        "EMBEDDING_PROVIDER": "cloudflare"
    }
    
    if not env["CF_ACCOUNT_ID"] or not env["CF_API_TOKEN"]:
        pytest.skip("Skipping real Cloudflare test: Credentials not set in environment.")
    
    payload = {
        "trace_id": "test-trace-123",
        "span_id": "test-span-456",
        "text": "Hello Cloudflare Workers AI!",
        "model": "@cf/baai/bge-small-en-v1.5"
    }
    
    try:
        result = enrich_span(payload, dimensions=384, provider_name="cloudflare", env=env)
        print("\nCloudflare API Result:", result)
        assert result["provider"] == "cloudflare"
        assert "embedding_key" in result
        print("Real Cloudflare call successful!")
    except Exception as e:
        pytest.fail(f"Real Cloudflare call failed: {e}")

if __name__ == "__main__":
    test_cloudflare_real_call()
