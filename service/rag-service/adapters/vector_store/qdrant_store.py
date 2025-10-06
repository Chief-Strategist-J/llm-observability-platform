"""Qdrant vector store implementation for RAG service.

This module provides vector storage and retrieval capabilities using Qdrant.

"""

import asyncio
import time

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ...core.domain.models import Chunk, SearchResult
from ...core.ports.vector_store import VectorStorePort


class QdrantStore(VectorStorePort):
    """
    Qdrant vector store implementation with connection retry logic.
    """

    def __init__(self, url: str, collection: str, dimension: int):
        """Initialize Qdrant vector store.

        Args:
            url: Qdrant server URL
            collection: Collection name for vector storage
            dimension: Dimensionality of embedding vectors

        """
        self.client = self._connect(url)
        self.collection = collection
        self.dimension = dimension
        self._ensure_collection()

    def _connect(self, url: str) -> QdrantClient:
        """Connect to Qdrant with retry logic.

        Args:

        Returns:
            Connected QdrantClient instance

        Raises:
            ConnectionError: If connection fails after all retries

        """
        for attempt in range(30):
            try:
                client = QdrantClient(url=url, timeout=10)
                client.get_collections()
                return client
            except Exception as e:
                if attempt < 29:
                    time.sleep(2)
                else:
                    raise ConnectionError(f"Qdrant connection failed: {e}") from e

    def _ensure_collection(self):
        """
        Ensure the collection exists, creating it if necessary.
        """
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.dimension, distance=Distance.COSINE
                ),
            )

    async def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Upsert chunks with their embeddings into the vector store.

        Args:
            chunks: List of document chunks
            embeddings: Corresponding embedding vectors

        """
        loop = asyncio.get_event_loop()
        points = [
            PointStruct(
                id=chunk.id,
                vector=embedding,
                payload={"text": chunk.text, "metadata": chunk.metadata},
            )
            for chunk, embedding in zip(chunks, embeddings, strict=False)
        ]
        await loop.run_in_executor(
            None,
            lambda: self.client.upsert(
                collection_name=self.collection, points=points, wait=True
            ),
        )

    async def search(self, embedding: list[float], limit: int) -> list[SearchResult]:
        """Search for similar vectors in the store.

        Args:
            embedding: Query embedding vector
            limit: Maximum number of results to return

        Returns:
            List of search results with chunks and scores

        """
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                collection_name=self.collection,
                query_vector=embedding,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            ),
        )
        return [
            SearchResult(
                chunk=Chunk(
                    id=str(r.id), text=r.payload["text"], metadata=r.payload["metadata"]
                ),
                score=r.score,
            )
            for r in results
        ]
