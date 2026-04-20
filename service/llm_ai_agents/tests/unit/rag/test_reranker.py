import pytest
from langchain_core.documents import Document
from services.rag.retrieval.reranker import CrossEncoderReranker


@pytest.fixture
def reranker(monkeypatch):
    from services.rag.retrieval import reranker as mod

    class _FakeCrossEncoder:
        def predict(self, pairs):
            return [len(p[1]) for p in pairs]

    monkeypatch.setattr(mod, "CrossEncoder", lambda *a, **kw: _FakeCrossEncoder())
    return CrossEncoderReranker()


def _doc(text: str) -> Document:
    return Document(page_content=text, metadata={"id": text[:5]})


def test_rerank_returns_top_k_documents(reranker):
    docs = [_doc("short"), _doc("medium length text"), _doc("the longest text of all docs")]
    result = reranker.rerank("query", docs, top_k=2)
    assert len(result) == 2


def test_rerank_orders_by_descending_score(reranker):
    docs = [_doc("a"), _doc("ab"), _doc("abc")]
    result = reranker.rerank("q", docs, top_k=3)
    lengths = [len(d.page_content) for d in result]
    assert lengths == sorted(lengths, reverse=True)


def test_rerank_empty_input_returns_empty(reranker):
    result = reranker.rerank("query", [], top_k=3)
    assert result == []


def test_rerank_top_k_greater_than_docs_returns_all(reranker):
    docs = [_doc("one"), _doc("two")]
    result = reranker.rerank("query", docs, top_k=10)
    assert len(result) == 2


def test_rerank_single_document(reranker):
    docs = [_doc("only document")]
    result = reranker.rerank("q", docs, top_k=1)
    assert len(result) == 1
    assert result[0].page_content == "only document"
