import logging
from typing import Dict, Any
from core.client.cloudflare_client import run_model

logger = logging.getLogger(__name__)

def get_ai_response(prompt: str, model: str, timeout: int = 30) -> Dict[str, Any]:
    if not prompt or not prompt.strip():
        logger.error("event=ai_response_empty_prompt model=%s", model)
        return {
            "text": "Please provide a prompt",
            "model_used": model,
            "success": False
        }
    
    if not model or not model.strip():
        logger.error("event=ai_response_empty_model")
        return {
            "text": "No model selected",
            "model_used": "",
            "success": False
        }
    
    logger.info("event=ai_response_start model=%s prompt_len=%s", model, len(prompt))
    
    result = run_model(model, prompt, timeout=timeout)
    
    if not result.get("success"):
        error_msg = result.get("error", "Unknown error")
        logger.error("event=ai_response_failed model=%s error=%s", model, error_msg)
        return {
            "text": f"Error: {error_msg}",
            "model_used": model,
            "success": False,
            "raw": result
        }
    
    body = result.get("body", {})
    
    response_text = ""
    if isinstance(body, dict):
        result_data = body.get("result", {})
        if isinstance(result_data, dict):
            response_text = (
                result_data.get("response") or 
                result_data.get("content") or 
                result_data.get("output") or 
                result_data.get("text") or
                ""
            )
        elif isinstance(result_data, str):
            response_text = result_data
    
    if not response_text:
        logger.warning("event=ai_response_empty model=%s body=%s", model, str(body)[:200])
        response_text = "No response generated"
    
    logger.info("event=ai_response_success model=%s response_len=%s", model, len(response_text))
    
    return {
        "text": response_text,
        "model_used": model,
        "success": True,
        "raw": body
    }