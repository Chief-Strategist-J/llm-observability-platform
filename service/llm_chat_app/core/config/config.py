# core/config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

CLOUDFLARE_ACCOUNT_ID = os.getenv(
    "CLOUDFLARE_ACCOUNT_ID",
    "718e73ec2e4dc0f92912bdeba7977bf2"
)

CLOUDFLARE_API_TOKEN = os.getenv(
    "CLOUDFLARE_API_TOKEN",
    "1R_3h3AQpV_DGQihx8p7HkGQELLHja6AQD77oqZe"
)

CLOUDFLARE_AI_BASE = os.getenv(
    "CLOUDFLARE_AI_BASE",
    f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run"
)

DEFAULT_IMAGE_TAG = os.getenv("DEFAULT_IMAGE_TAG", "llm_chat_app:latest")
DEFAULT_CONTAINER_NAME = os.getenv("DEFAULT_CONTAINER_NAME", "llm-chat-app")

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "chat-service-queue")

MODEL_REGISTRY = [
    {
        "name": "cloudflare-gpt",
        "version": "1.0",
        "backend": "cloudflare",
        "endpoint": "",
        "defaults": {
            "temperature": 0.2,
            "max_tokens": 512
        }
    }
]


def get_model_entry(name: str):
    for m in MODEL_REGISTRY:
        if m.get("name") == name:
            return m
    return None
