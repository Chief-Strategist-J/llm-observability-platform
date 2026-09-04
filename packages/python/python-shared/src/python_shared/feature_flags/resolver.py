import os
from typing import Dict, Any

def evaluate_flag(flag_name: str, context: Dict[str, Any], default: bool = False) -> bool:
    env_flag = os.getenv(f"FEATURE_FLAG_{flag_name.upper()}")
    if env_flag is not None:
        return env_flag.lower() in ("true", "1", "yes")
    return default
