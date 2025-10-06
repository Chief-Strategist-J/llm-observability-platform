import logging
from uuid import uuid4

from ..domain.models import Chunk
from ..ports.document_parser import DocumentParserPort
from ..ports.embedding_model import EmbeddingModelPort
from ..ports.vector_store import VectorStorePort

logger = logging.getLogger(__name__)


async def ingest_document(
    file_bytes: bytes,
    filename: str,
    parser: DocumentParserPort,
    embedder: EmbeddingModelPort,
    vector_store: VectorStorePort,
) -> dict:
    logger.info(f"Ingesting: {filename}")

    text = await parser.parse(file_bytes)
    logger.info(f"Extracted {len(text)} chars")

    chunks: list[Chunk] = []
    texts: list[str] = []

    async for chunk_text in parser.chunk(text):
        idx = len(chunks)
        chunks.append(
            Chunk(
                id=str(uuid4()),
                text=chunk_text,
                metadata={"filename": filename, "chunk_index": idx},
            )
        )
        texts.append(chunk_text)

    logger.info(f"Created {len(chunks)} chunks")

    embeddings = await embedder.embed_batch(texts)
    await vector_store.upsert(chunks, embeddings)

    logger.info(f"Stored {len(chunks)} chunks")
    return {"chunks": len(chunks), "filename": filename}
