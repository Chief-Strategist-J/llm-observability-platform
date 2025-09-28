import os

class Settings:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    VECTOR_SIZE: int = 384
    COLLECTION_NAME: str = "documents"
    MODEL_NAME: str = "all-MiniLM-L6-v2"

settings: Settings = Settings()
