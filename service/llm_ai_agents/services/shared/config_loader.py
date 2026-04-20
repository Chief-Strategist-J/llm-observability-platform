import os
import yaml
from typing import Any, Dict
from services.shared.exceptions import ConfigNotFoundError


def _project_root() -> str:
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def load_yaml_config(relative_path: str) -> Dict[str, Any]:
    full_path = os.path.join(_project_root(), relative_path)
    if not os.path.exists(full_path):
        raise ConfigNotFoundError(f"Config not found: {full_path}")
    with open(full_path, "r") as f:
        return yaml.safe_load(f) or {}
