import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
CLOUDFLARE_AI_URL = os.getenv("CLOUDFLARE_AI_URL")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
DEFAULT_IMAGE_TAG = os.getenv("DEFAULT_IMAGE_TAG", "llm_chat_app:latest")
DEFAULT_CONTAINER_NAME = os.getenv("DEFAULT_CONTAINER_NAME", "llm-chat-app")
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "chat-service-queue")
