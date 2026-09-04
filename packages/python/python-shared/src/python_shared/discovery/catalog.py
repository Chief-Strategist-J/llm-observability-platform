import os
from typing import Dict

DEFAULT_SERVICE_CATALOG: Dict[str, str] = {
    "alert-engine": "http://alert-engine.internal:8004",
    "budget-provisioner": "http://budget-provisioner.internal:8002",
    "event-cost": "http://event-cost.internal:8005",
    "faithfulness": "http://faithfulness.internal:8010",
    "forecast-worker": "http://forecast-worker.internal:8006",
    "latency-engine": "http://latency-engine.internal:8001",
    "nli-worker": "http://nli-worker.internal:8008",
    "perplexity": "http://perplexity.internal:8011",
    "quality-engine": "http://quality-engine.internal:8003",
    "semantic-coherence": "http://semantic-coherence.internal:8009",
    "slo-burn-worker": "http://slo-burn-worker.internal:8007",
    "toxicity": "http://toxicity.internal:8012",
}

def resolve_service_endpoint(service_name: str) -> str:
    env_key = f"{service_name.upper().replace('-', '_')}_SERVICE_URL"
    return os.getenv(env_key, DEFAULT_SERVICE_CATALOG.get(service_name, f"http://{service_name}:8000"))
