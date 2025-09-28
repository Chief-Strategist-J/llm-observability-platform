"""Application settings with validation."""
import os
from typing import Optional

class Settings:
    # Qdrant Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # Vector Configuration
    VECTOR_DIM: int = int(os.getenv("VECTOR_DIM", "384"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "embeddings")
    DISTANCE_METRIC: str = os.getenv("DISTANCE_METRIC", "Cosine")
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "demo")
    
    # API Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    def validate(self):
        """Validate configuration."""
        assert self.VECTOR_DIM > 0, "VECTOR_DIM must be positive"
        assert self.DISTANCE_METRIC in ["Cosine", "Dot", "Euclid"], "Invalid distance metric"
        assert self.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"], "Invalid log level"

settings = Settings()
settings.validate()
