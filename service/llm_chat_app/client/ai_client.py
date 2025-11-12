import logging
from typing import Optional, Dict, Any
from client.cloudflare_client import call_cloudflare
from models.model_store import ModelStore
logger = logging.getLogger(__name__)

_store = ModelStore()

def get_ai_response(prompt: str, model_choice: Optional[str] = None) -> Dict[str, Any]:
    logger.info("ai_client.get_ai_response model_choice=%s prompt_len=%d", model_choice, len(prompt) if prompt else 0)
    
    try:
        model = _store.get_model(model_choice) if model_choice else _store.default_model()
    except Exception:
        model = {}

    endpoint = model.get("endpoint")
    token = model.get("token")
    params = model.get("defaults", {})
    resp = call_cloudflare(endpoint, token, prompt, params)

    return {"text": resp.get("result") or resp.get("output") or resp.get("text") or str(resp), "raw": resp}
