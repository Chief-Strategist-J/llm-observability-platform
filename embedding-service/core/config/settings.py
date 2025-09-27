"""Application settings."""
import os

class Settings:
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    VECTOR_DIM: int = int(os.getenv("VECTOR_DIM", "384"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "embeddings")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

settings = Settings()
