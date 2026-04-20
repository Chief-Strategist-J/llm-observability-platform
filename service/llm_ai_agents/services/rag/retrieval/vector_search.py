import os
from typing import List
from langchain_core.documents import Document
from langchain_chroma import Chroma
from services.rag.ports.document_store import DocumentStorePort
from services.rag.ports.retriever import RetrieverPort


_CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")


class ChromaRetriever(RetrieverPort, DocumentStorePort):
    def __init__(self, embeddings):
        self._embeddings = embeddings
        self._persist_dir = _CHROMA_PERSIST_DIR

    def _get_store(self, collection: str) -> Chroma:
        return Chroma(
            collection_name=collection,
            embedding_function=self._embeddings,
            persist_directory=self._persist_dir,
        )

    def add_documents(self, documents: List[Document], collection: str) -> None:
        store = self._get_store(collection)
        store.add_documents(documents)

    def delete_collection(self, collection: str) -> None:
        store = self._get_store(collection)
        store.delete_collection()

    def list_collections(self) -> List[str]:
        import chromadb
        client = chromadb.PersistentClient(path=self._persist_dir)
        return [c.name for c in client.list_collections()]

    def retrieve(self, query: str, collection: str, k: int = 4) -> List[Document]:
        store = self._get_store(collection)
        return store.similarity_search(query, k=k)
