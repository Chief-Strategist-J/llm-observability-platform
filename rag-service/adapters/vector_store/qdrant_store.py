from typing import List
import asyncio
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from core.ports.vector_store import VectorStorePort
from core.domain.models import Chunk, SearchResult

class QdrantStore(VectorStorePort):
    def __init__(self, url: str, collection: str, dimension: int):
        self.client = self._connect(url)
        self.collection = collection
        self.dimension = dimension
        self._ensure_collection()

    def _connect(self, url: str) -> QdrantClient:
        for attempt in range(30):
            try:
                client = QdrantClient(url=url, timeout=10)
                client.get_collections()
                return client
            except Exception as e:
                if attempt < 29:
                    time.sleep(2)
                else:
                    raise Exception(f"Qdrant connection failed: {e}")

    def _ensure_collection(self):
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE)
            )

    async def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        loop = asyncio.get_event_loop()
        points = [
            PointStruct(
                id=chunk.id,
                vector=embedding,
                payload={"text": chunk.text, "metadata": chunk.metadata}
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        await loop.run_in_executor(
            None,
            lambda: self.client.upsert(collection_name=self.collection, points=points, wait=True)
        )

    async def search(self, embedding: List[float], limit: int) -> List[SearchResult]:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                collection_name=self.collection,
                query_vector=embedding,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
        )
        return [
            SearchResult(
                chunk=Chunk(
                    id=str(r.id),
                    text=r.payload["text"],
                    metadata=r.payload["metadata"]
                ),
                score=r.score
            )
            for r in results
        ]
