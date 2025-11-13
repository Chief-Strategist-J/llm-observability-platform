import logging
import requests
from core.config.config import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN

logger = logging.getLogger(__name__)

def get_ai_response(prompt: str, model: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"prompt": prompt}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
    except Exception as e:
        logger.error("cloudflare_request_failed model=%s error=%s", model, e)
        return {"text": "Cloudflare request failed", "raw": {}}
    try:
        data = r.json() if r.content else {}
    except Exception:
        data = {"raw_text": r.text}
    if not r.ok:
        logger.error("cloudflare_response_not_ok status=%s body=%s", r.status_code, data)
        return {"text": "Cloudflare API error", "raw": data}
    result = (data or {}).get("result") or {}
    out = ""
    if isinstance(result, dict):
        out = result.get("response") or ""
    if not out and isinstance(data, dict):
        out = data.get("response") or ""
    return {"text": out or "", "raw": data}
