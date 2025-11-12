import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from config.config import DEFAULT_IMAGE_TAG

logger = logging.getLogger(__name__)
REG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "registry.yaml")

class ModelStore:
    def __init__(self, path: Optional[str] = None):
        self.path = path or REG_PATH
        self._models = self._load()
    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
                return raw.get("models", [])
        except Exception:
            logger.exception("model_store load failed")
            return []
    def list_models(self) -> List[str]:
        return [f"{m.get('name')}@{m.get('version')}" for m in self._models]
    def get_model(self, model_choice: Optional[str]) -> Dict[str, Any]:
        if not model_choice and self._models:
            return self._models[0]
        if "@" in (model_choice or ""):
            name, _, ver = model_choice.partition("@")
        else:
            name, ver = model_choice, None
        for m in self._models:
            if m.get("name") == name and (ver is None or m.get("version") == ver):
                return m
        raise KeyError("model not found")
    def default_model(self) -> Dict[str, Any]:
        if self._models:
            return self._models[0]
        return {"endpoint": os.getenv("CLOUDFLARE_AI_URL"), "token": os.getenv("CLOUDFLARE_API_TOKEN"), "defaults": {}}
