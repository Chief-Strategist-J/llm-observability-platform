import logging
import requests
from typing import Dict, Any, Optional
from config.config import CLOUDFLARE_AI_URL, CLOUDFLARE_API_TOKEN

logger = logging.getLogger(__name__)

def call_cloudflare(endpoint: Optional[str], token: Optional[str], prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ep = endpoint or CLOUDFLARE_AI_URL
    tk = token or CLOUDFLARE_API_TOKEN

    logger.info("cloudflare call start endpoint=%s prompt_len=%d", ep, len(prompt) if prompt else 0)

    if not ep or not tk:
        logger.error("cloudflare call missing endpoint or token")
        return {"error": "missing endpoint or token"}

    headers = {"Authorization": f"Bearer {tk}", "Content-Type": "application/json"}
    payload = {"input": prompt}

    if params:
        payload["parameters"] = params
    try:
        resp = requests.post(ep, json=payload, headers=headers, timeout=30)
        logger.info("cloudflare response status=%s", resp.status_code)

        try:
            return resp.json()
        except Exception:
            logger.exception("cloudflare response json parse failed")
            return {"status_code": resp.status_code, "text": resp.text}

    except Exception:
        logger.exception("cloudflare request failed")
        return {"error": "request failed"}
