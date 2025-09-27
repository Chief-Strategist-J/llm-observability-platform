import os
import yaml
from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path

# Get project root directory
ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "configs" / "model.yaml"

@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment and config files"""
    cf_account_id: str
    cf_api_token: str
    model_id: str
    inference_params: Dict[str, Any]
    host: str
    port: int
    http_timeout_seconds: float
    environment: str

def load_model_config() -> Dict[str, Any]:
    """Load model configuration from YAML file"""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"Warning: Config file {CONFIG_PATH} not found, using defaults")
        return {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def load_settings() -> Settings:
    """Load all application settings"""
    config = load_model_config()
    
    # Required Cloudflare credentials
    cf_account_id = os.getenv("CF_ACCOUNT_ID", "").strip()
    cf_api_token = os.getenv("CF_API_TOKEN", "").strip()
    
    if not cf_account_id:
        raise ValueError("CF_ACCOUNT_ID environment variable is required")
    if not cf_api_token:
        raise ValueError("CF_API_TOKEN environment variable is required")
    
    # Model configuration (ENV can override YAML)
    model_id = os.getenv("MODEL_ID") or config.get("model_id", "@cf/meta/llama-3.2-1b-instruct")
    inference_params = config.get("inference", {})
    
    return Settings(
        cf_account_id=cf_account_id,
        cf_api_token=cf_api_token,
        model_id=model_id,
        inference_params=inference_params,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
        environment=os.getenv("ENV", "production")
    )

# Global settings instance
settings = load_settings()
