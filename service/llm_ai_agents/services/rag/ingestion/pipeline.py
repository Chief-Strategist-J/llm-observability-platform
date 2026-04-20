from typing import List
from langchain_core.documents import Document
from services.rag.ingestion.loader import DocumentLoader
from services.rag.ingestion.chunker import TextChunker
from services.rag.ports.document_store import DocumentStorePort
from services.shared.exceptions import RAGIngestionError


class IngestionPipeline:
    def __init__(self, store: DocumentStorePort, chunk_size: int = 1000, chunk_overlap: int = 200):
        self._store = store
        self._loader = DocumentLoader()
        self._chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def ingest_url(self, url: str, collection: str) -> int:
        try:
            docs = self._loader.from_url(url)
            chunks = self._chunker.split(docs)
            self._store.add_documents(chunks, collection)
            return len(chunks)
        except Exception as exc:
            raise RAGIngestionError(str(exc)) from exc

    def ingest_file(self, file_path: str, collection: str) -> int:
        try:
            docs = self._loader.from_file(file_path)
            chunks = self._chunker.split(docs)
            self._store.add_documents(chunks, collection)
            return len(chunks)
        except Exception as exc:
            raise RAGIngestionError(str(exc)) from exc

    def ingest_text(self, text: str, collection: str, metadata: dict = None) -> int:
        try:
            docs = self._loader.from_text(text, metadata=metadata)
            chunks = self._chunker.split(docs)
            self._store.add_documents(chunks, collection)
            return len(chunks)
        except Exception as exc:
            raise RAGIngestionError(str(exc)) from exc
