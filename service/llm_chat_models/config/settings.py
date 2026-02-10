import os
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.absolute()
MODEL_STORAGE_PATH = os.path.join(BASE_DIR, 'storage', 'models')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
API_HOST = '0.0.0.0'
API_PORT = 8100
LOG_LEVEL = 'INFO'
KEEP_ALIVE_DURATION = 300
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:MongoPassword123!@172.29.0.20:27017/')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'ai_agents')
POSTGRES_DSN = os.getenv('POSTGRES_DSN', 'postgresql://admin:PostgresPassword123!@172.29.0.10:5432/default')
CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5'))
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = float(os.getenv('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', '30.0'))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '100'))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv('RATE_LIMIT_WINDOW_SECONDS', '60'))
AUTH_ENABLED = os.getenv('AUTH_ENABLED', 'true').lower() == 'true'
AUTH_SKIP_PATHS = ['/health', '/ready', '/docs', '/openapi.json']
GRACEFUL_SHUTDOWN_TIMEOUT = float(os.getenv('GRACEFUL_SHUTDOWN_TIMEOUT', '10.0'))
EVENT_POLL_INTERVAL = float(os.getenv('EVENT_POLL_INTERVAL', '0.5'))