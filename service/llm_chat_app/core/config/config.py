import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_env_path = Path(__file__).resolve().parents[2] / ".env.llm_chat_app"
load_dotenv(_env_path, override=True)
logger.info("event=config_loaded path=%s exists=%s", str(_env_path), _env_path.exists())

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

DEFAULT_IMAGE_TAG = os.getenv("DEFAULT_IMAGE_TAG")
DEFAULT_CONTAINER_NAME = os.getenv("DEFAULT_CONTAINER_NAME")

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE")

if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
    logger.error("event=config_missing_cloudflare account_id=%s token=%s", bool(CLOUDFLARE_ACCOUNT_ID), bool(CLOUDFLARE_API_TOKEN))
else:
    logger.info("event=config_cloudflare_ok account_id_len=%s", len(CLOUDFLARE_ACCOUNT_ID))