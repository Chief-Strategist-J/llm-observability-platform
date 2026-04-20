from typing import List
from langchain_core.documents import Document
from services.rag.ports.retriever import RetrieverPort
from services.rag.ports.document_store import DocumentStorePort
from services.rag.ingestion.pipeline import IngestionPipeline
from services.rag.retrieval.reranker import CrossEncoderReranker
from services.llm.base.llm import BaseLLM


_CONTEXT_TEMPLATE = (
    "Use the following context to answer the question.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Answer:"
)


class RAGService:
    def __init__(
        self,
        retriever: RetrieverPort,
        store: DocumentStorePort,
        ingestion: IngestionPipeline,
        reranker: CrossEncoderReranker,
    ):
        self._retriever = retriever
        self._store = store
        self._ingestion = ingestion
        self._reranker = reranker

    def ingest(self, source: str, source_type: str, collection: str = "default") -> int:
        if source_type == "url":
            return self._ingestion.ingest_url(source, collection)
        if source_type == "file":
            return self._ingestion.ingest_file(source, collection)
        return self._ingestion.ingest_text(source, collection)

    def query(
        self,
        question: str,
        llm: BaseLLM,
        collection: str = "default",
        k: int = 4,
        rerank_top_k: int = 3,
    ) -> dict:
        docs = self._retriever.retrieve(question, collection, k=k)
        ranked = self._reranker.rerank(question, docs, top_k=rerank_top_k)
        context = "\n\n".join(doc.page_content for doc in ranked)
        prompt = _CONTEXT_TEMPLATE.format(context=context, question=question)
        answer = llm.generate(prompt)
        return {
            "answer": answer,
            "sources": [doc.metadata for doc in ranked],
            "chunks_retrieved": len(docs),
        }

    def delete_collection(self, collection: str) -> None:
        self._store.delete_collection(collection)

    def list_collections(self) -> List[str]:
        return self._store.list_collections()
