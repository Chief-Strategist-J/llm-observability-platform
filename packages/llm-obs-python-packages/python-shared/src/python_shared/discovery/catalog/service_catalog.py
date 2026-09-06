import os
from typing import Dict, Any, Optional

SERVICE_CATALOG_META: Dict[str, Dict[str, Any]] = {
    "latency-engine": {"defaultPort": 8001, "protocol": "http", "healthPath": "/health"},
    "budget-provisioner": {"defaultPort": 8002, "protocol": "http", "healthPath": "/health"},
    "quality-engine": {"defaultPort": 8003, "protocol": "http", "healthPath": "/health"},
    "alert-engine": {"defaultPort": 8004, "protocol": "http", "healthPath": "/health"},
    "event-cost": {"defaultPort": 8005, "protocol": "http", "healthPath": "/health"},
    "forecast-worker": {"defaultPort": 8006, "protocol": "http", "healthPath": "/health"},
    "slo-burn-worker": {"defaultPort": 8007, "protocol": "http", "healthPath": "/health"},
    "nli-worker": {"defaultPort": 8008, "protocol": "http", "healthPath": "/health"},
    "semantic-coherence": {"defaultPort": 8009, "protocol": "http", "healthPath": "/health"},
    "faithfulness": {"defaultPort": 8010, "protocol": "http", "healthPath": "/health"},
    "perplexity": {"defaultPort": 8011, "protocol": "http", "healthPath": "/health"},
    "toxicity": {"defaultPort": 8012, "protocol": "http", "healthPath": "/health"},
    "queue-embedding-worker": {"defaultPort": 8013, "protocol": "http", "healthPath": "/health"},
    "temporal-ewma-worker": {"defaultPort": 8014, "protocol": "http", "healthPath": "/health"},
    "web-app": {"defaultPort": 3000, "protocol": "http", "healthPath": "/"},
}

DEFAULT_SERVICE_CATALOG: Dict[str, str] = {
    name: f"{meta.get('protocol', 'http')}://{name}.internal:{meta.get('defaultPort', 8000)}"
    for name, meta in SERVICE_CATALOG_META.items()
}

def resolve_service_endpoint(service_name: str, fallback_url: Optional[str] = None) -> str:
    env_key = f"{service_name.upper().replace('-', '_')}_SERVICE_URL"
    env_val = os.getenv(env_key)
    if env_val:
        return env_val
    if fallback_url:
        return fallback_url
    return DEFAULT_SERVICE_CATALOG.get(service_name, f"http://{service_name}:8000")
