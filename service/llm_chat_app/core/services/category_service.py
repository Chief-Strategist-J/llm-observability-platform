import logging
from typing import Dict, List
from core.client.cloudflare_client import fetch_models_from_api

logger = logging.getLogger(__name__)

_TASK_MAPPING = {
    "Text Generation": ["Text Generation", "text-generation", "chat"],
    "Text Embeddings": ["Text Embeddings", "text-embeddings", "embedding"],
    "Image Generation": ["Image Generation", "image-generation", "text-to-image"],
    "Speech Recognition": ["Speech Recognition", "speech-recognition", "automatic-speech-recognition"],
    "Text-to-Speech": ["Text to Speech", "text-to-speech", "tts"],
    "Translation": ["Translation", "translation"],
    "Summarization": ["Summarization", "summarization"],
    "Image Classification": ["Image Classification", "image-classification", "vision"],
    "Object Detection": ["Object Detection", "object-detection"],
    "Other": []
}

def _normalize_task(task: str) -> str:
    task_lower = task.lower().strip()
    
    for normalized, variants in _TASK_MAPPING.items():
        if normalized == "Other":
            continue
        for variant in variants:
            if variant.lower() in task_lower or task_lower in variant.lower():
                return normalized
    
    return "Other"

def get_categories_and_models(force_refresh: bool = False) -> Dict[str, List[Dict[str, str]]]:
    models = fetch_models_from_api(force_refresh=force_refresh)
    
    if not models:
        logger.warning("event=categories_no_models")
        return {}
    
    categories: Dict[str, List[Dict[str, str]]] = {}
    
    for model in models:
        task = model.get("task", "Unknown")
        normalized_task = _normalize_task(task)
        
        if normalized_task not in categories:
            categories[normalized_task] = []
        
        categories[normalized_task].append({
            "name": model.get("name", ""),
            "id": model.get("id", ""),
            "description": model.get("description", "")
        })
    
    for cat in categories:
        categories[cat] = sorted(categories[cat], key=lambda x: x["name"])
    
    sorted_categories = {}
    priority = ["Text Generation", "Text Embeddings", "Image Generation", "Speech Recognition", "Text-to-Speech"]
    
    for cat in priority:
        if cat in categories:
            sorted_categories[cat] = categories[cat]
    
    for cat in sorted(categories.keys()):
        if cat not in sorted_categories:
            sorted_categories[cat] = categories[cat]
    
    logger.info("event=categories_built count=%s models=%s", len(sorted_categories), sum(len(v) for v in sorted_categories.values()))
    
    return sorted_categories

def get_models_for_category(category: str, force_refresh: bool = False) -> List[str]:
    categories = get_categories_and_models(force_refresh=force_refresh)
    
    if category not in categories:
        logger.warning("event=category_not_found category=%s", category)
        return []
    
    model_names = [m["name"] for m in categories[category]]
    logger.info("event=category_models category=%s count=%s", category, len(model_names))
    
    return model_names

def get_default_model_for_category(category: str, force_refresh: bool = False) -> str:
    models = get_models_for_category(category, force_refresh=force_refresh)
    
    if not models:
        logger.warning("event=default_model_empty category=%s", category)
        return ""
    
    default = models[0]
    logger.info("event=default_model_selected category=%s model=%s", category, default)
    
    return default