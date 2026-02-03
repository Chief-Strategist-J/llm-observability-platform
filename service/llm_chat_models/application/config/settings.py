from pathlib import Path
from .credentials import (
    ServiceConfig,
    OllamaConfig,
    MongoDBConfig,
    ApicurioConfig,
    ObservabilityConfig
)

BASE_DIR = Path(__file__).parent.absolute()

OLLAMA_HOST = OllamaConfig.HOST
API_HOST = ServiceConfig.HOST
API_PORT = ServiceConfig.PORT
LOG_LEVEL = ServiceConfig.LOG_LEVEL
KEEP_ALIVE_DURATION = ServiceConfig.KEEP_ALIVE_DURATION

MONGODB_URI = MongoDBConfig.URI
MONGODB_DATABASE = MongoDBConfig.DATABASE
MONGODB_MODELS_COLLECTION = MongoDBConfig.MODELS_COLLECTION
MONGODB_ENDPOINTS_COLLECTION = MongoDBConfig.ENDPOINTS_COLLECTION

APICURIO_BASE_URL = ApicurioConfig.BASE_URL
APICURIO_API_VERSION = ApicurioConfig.API_VERSION
APICURIO_GROUP_ID = ApicurioConfig.GROUP_ID

OTLP_ENDPOINT = ObservabilityConfig.OTLP_ENDPOINT
SERVICE_NAME = ObservabilityConfig.SERVICE_NAME
