import uuid

from core.domain.models import Chunk
from core.ports.chunking import ChunkingPort
import tiktoken


class SemanticChunker(ChunkingPort):
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

    async def chunk_text(self, text: str, metadata: dict) -> list[Chunk]:
        tokens = self.encoding.encode(text)
        chunks = []

        start = 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)

            chunk = Chunk(
                text=chunk_text,
                chunk_id=f"chunk_{uuid.uuid4().hex[:12]}",
                metadata={
                    **metadata,
                    "start_token": start,
                    "end_token": end,
                    "token_count": len(chunk_tokens),
                },
            )
            chunks.append(chunk)

            start = end - self.overlap

        return chunks
