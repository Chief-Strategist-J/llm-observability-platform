import logging
from typing import Dict, Any, List, Optional
from core.client.cloudflare_client import run_model
from core.services.deep_psychological_engine import analyze_deep_psychology

logger = logging.getLogger(__name__)

def get_ai_response(
    prompt: str, 
    model: str, 
    conversation_history: Optional[List[Dict[str, str]]] = None, 
    timeout: int = 30,
    enable_deep_analysis: bool = True
) -> Dict[str, Any]:
    
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
    
    logger.info("event=ai_response_start model=%s prompt_len=%s history_len=%s deep_analysis=%s", 
                model, len(prompt), len(conversation_history) if conversation_history else 0, enable_deep_analysis)
    
    params = None
    if conversation_history and len(conversation_history) > 0:
        messages = conversation_history + [{"role": "user", "content": prompt}]
        params = {"messages": messages}
    
    result = run_model(model, prompt, params=params, timeout=timeout)
    
    if not result.get("success"):
        error_msg = result.get("error", "Unknown error")
        logger.error("event=ai_response_failed model=%s error=%s", model, error_msg)
        return {
            "text": f"Error: {error_msg}",
            "model_used": model,
            "success": False,
            "deep_analysis": None
        }
    
    body = result.get("body", {})
    
    response_text = ""
    if isinstance(body, dict):
        result_data = body.get("result", {})
        if isinstance(result_data, dict):
            choices = result_data.get("choices", [])
            if isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get("message", {})
                    if isinstance(message, dict):
                        response_text = message.get("content", "")
            
            if not response_text:
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
    
    deep_analysis = None
    if enable_deep_analysis:
        logger.info("event=ai_response_deep_analysis_start model=%s", model)
        try:
            deep_analysis = analyze_deep_psychology(
                prompt=prompt,
                response=response_text,
                conversation_history=conversation_history
            )
            logger.info("event=ai_response_deep_analysis_success emotion=%s meta_core=%s", 
                       deep_analysis.get("layer_2_emotional_state", {}).get("core_emotion"),
                       deep_analysis.get("layer_5_meta_questions", {}).get("meta_5"))
        except Exception as e:
            logger.error("event=ai_response_deep_analysis_failed error=%s", str(e))
            deep_analysis = None
    
    return {
        "text": response_text,
        "model_used": model,
        "success": True,
        "raw": body,
        "deep_analysis": deep_analysis
    }