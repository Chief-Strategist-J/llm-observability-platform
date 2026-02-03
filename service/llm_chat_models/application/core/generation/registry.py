from typing import Dict, Any

SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
    "llama2": {
        "name": "llama2",
        "description": "Meta's Llama 2 model",
        "parameters": "7b",
        "size": "3.8GB",
        "family": "llama"
    },
    "llama3": {
        "name": "llama3",
        "description": "Meta's Llama 3 model",
        "parameters": "8b",
        "size": "4.7GB",
        "family": "llama"
    },
    "mistral": {
        "name": "mistral",
        "description": "Mistral AI 7B model",
        "parameters": "7b",
        "size": "4.1GB",
        "family": "mistral"
    },
    "qwen": {
        "name": "qwen",
        "description": "Alibaba Cloud's Qwen model",
        "parameters": "7b",
        "size": "4.5GB",
        "family": "qwen"
    },
    "tinyllama": {
        "name": "tinyllama",
        "description": "TinyLlama 1.1B model",
        "parameters": "1.1b",
        "size": "637MB",
        "family": "llama"
    }
}

def get_model_info(model_name: str) -> Dict[str, Any]:
    return SUPPORTED_MODELS.get(model_name, None)
