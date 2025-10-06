"""Sentence transformer embedding model for RAG service.

This module provides sentence embedding capabilities using the sentence- transformers
library.

"""

import asyncio

from sentence_transformers import SentenceTransformer

from ...core.ports.embedding_model import EmbeddingModelPort


class SentenceTransformerModel(EmbeddingModelPort):
    """
    Sentence transformer embedding model implementation with singleton pattern.
    """

    _instance = None
    _model = None

    def __new__(cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Create or return singleton instance of SentenceTransformerModel.

        Args:
            model_name: Name of the sentence transformer model to load

        Returns:
            Singleton instance of the model

        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._model = SentenceTransformer(model_name)
        return cls._instance

    @property
    def dimension(self) -> int:
        """
        Get the dimensionality of the embedding vectors.
        """
        return self._model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        """
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                text, show_progress_bar=False, normalize_embeddings=True
            ),
        )
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        """
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                texts, show_progress_bar=False, batch_size=8, normalize_embeddings=True
            ),
        )
        return [emb.tolist() for emb in embeddings]
