# core/client/cloudflare_client.py
import logging
import requests
import urllib.parse
from typing import Optional, Dict, Any

from core.config.config import CLOUDFLARE_AI_BASE, CLOUDFLARE_API_TOKEN, get_model_entry

logger = logging.getLogger(__name__)


def _auth_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }


def _make_endpoint_for_identifier(model_identifier: str) -> str:
    mid = urllib.parse.quote(model_identifier, safe="")
    return f"{CLOUDFLARE_AI_BASE}/{mid}"


def run_model_by_identifier(
    model_identifier: str,
    prompt: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    if not model_identifier:
        raise ValueError("model_identifier is required")
    url = _make_endpoint_for_identifier(model_identifier)
    payload: Dict[str, Any] = {"prompt": prompt}
    if params:
        payload.update(params)
    headers = _auth_headers()
    logger.info(
        "cloudflare.run_model identifier=%s url=%s payload_keys=%s",
        model_identifier, url, list(payload.keys())
    )
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        try:
            body = resp.json()
        except Exception:
            body = {"raw_text": resp.text}
        logger.info(
            "cloudflare.run_model status=%s identifier=%s",
            resp.status_code, model_identifier
        )
        return {"status_code": resp.status_code, "body": body}
    except Exception as e:
        logger.exception(
            "cloudflare.run_model failed identifier=%s error=%s",
            model_identifier, e
        )
        raise


def run_registered_model(
    model_name: str,
    prompt: str,
    model_identifier: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    entry = get_model_entry(model_name)
    if not entry:
        raise ValueError(f"model '{model_name}' not found in registry")
    endpoint = entry.get("endpoint", "") or model_identifier
    if not endpoint:
        raise ValueError(
            f"no endpoint configured for registered model '{model_name}'. "
            f"provide model_identifier or set endpoint in registry"
        )
    params = {}
    params.update(entry.get("defaults", {}) or {})
    if overrides:
        params.update(overrides)
    return run_model_by_identifier(endpoint, prompt, params, timeout)
