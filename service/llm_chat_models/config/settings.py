import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()
MODEL_STORAGE_PATH = os.path.join(BASE_DIR, "storage", "models")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
API_HOST = "0.0.0.0"
API_PORT = 8100
LOG_LEVEL = "INFO"
KEEP_ALIVE_DURATION = 300
