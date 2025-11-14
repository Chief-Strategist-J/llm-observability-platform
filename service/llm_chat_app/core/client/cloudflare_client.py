import logging
import requests
from typing import Dict, Any, List, Optional
from core.config.config import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.cloudflare.com/client/v4"
_MODELS_CACHE: Optional[List[Dict[str, Any]]] = None

def _get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }

def fetch_models_from_api(force_refresh: bool = False) -> List[Dict[str, Any]]:
    global _MODELS_CACHE
    
    if _MODELS_CACHE is not None and not force_refresh:
        logger.info("event=models_cache_hit count=%s", len(_MODELS_CACHE))
        return _MODELS_CACHE
    
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        logger.error("event=models_fetch_no_credentials")
        return []
    
    url = f"{_BASE_URL}/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/models/search"
    
    logger.info("event=models_fetch_start url=%s", url)
    
    try:
        resp = requests.get(url, headers=_get_headers(), timeout=15)
        
        if not resp.ok:
            logger.error("event=models_fetch_failed status=%s body=%s", resp.status_code, resp.text[:200])
            return []
        
        data = resp.json()
        result = data.get("result", [])
        
        if not isinstance(result, list):
            logger.error("event=models_fetch_invalid_format type=%s", type(result))
            return []
        
        models = []
        for item in result:
            if not isinstance(item, dict):
                continue
            
            model_name = item.get("name") or item.get("id")
            task = item.get("task", {})
            task_name = task.get("name") if isinstance(task, dict) else str(task)
            
            if model_name:
                models.append({
                    "name": model_name,
                    "id": item.get("id"),
                    "task": task_name or "Unknown",
                    "description": item.get("description", ""),
                    "properties": item.get("properties", [])
                })
        
        _MODELS_CACHE = models
        logger.info("event=models_fetch_success count=%s", len(models))
        return models
        
    except requests.exceptions.Timeout:
        logger.error("event=models_fetch_timeout")
        return []
    except Exception as e:
        logger.exception("event=models_fetch_exception error=%s", str(e))
        return []

def run_model(model_name: str, prompt: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        logger.error("event=run_model_no_credentials model=%s", model_name)
        return {"success": False, "error": "Missing Cloudflare credentials"}
    
    url = f"{_BASE_URL}/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{model_name}"
    
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    if params:
        payload.update(params)
    
    logger.info("event=run_model_start model=%s url=%s", model_name, url)
    
    try:
        resp = requests.post(url, json=payload, headers=_get_headers(), timeout=timeout)
        
        try:
            body = resp.json()
        except Exception:
            body = {"raw_text": resp.text}
        
        if not resp.ok:
            logger.error("event=run_model_failed model=%s status=%s body=%s", model_name, resp.status_code, body)
            return {
                "success": False,
                "status_code": resp.status_code,
                "error": body.get("errors", [{}])[0].get("message", "Unknown error") if isinstance(body, dict) else "API error",
                "body": body
            }
        
        logger.info("event=run_model_success model=%s status=%s", model_name, resp.status_code)
        
        return {
            "success": True,
            "status_code": resp.status_code,
            "body": body
        }
        
    except requests.exceptions.Timeout:
        logger.error("event=run_model_timeout model=%s", model_name)
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        logger.exception("event=run_model_exception model=%s error=%s", model_name, str(e))
        return {"success": False, "error": str(e)}