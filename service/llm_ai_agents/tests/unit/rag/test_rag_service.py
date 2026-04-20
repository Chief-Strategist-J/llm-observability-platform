import pytest
from langchain_core.documents import Document
from services.rag.api.rag_service import RAGService
from services.rag.ingestion.pipeline import IngestionPipeline
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_retriever import FakeRetriever
from tests.fakes.fake_document_store import FakeDocumentStore


@pytest.fixture
def docs():
    return [
        Document(page_content="Python uses indentation", metadata={"source": "py-docs"}),
        Document(page_content="Python is interpreted", metadata={"source": "py-docs"}),
        Document(page_content="Python has dynamic typing", metadata={"source": "py-docs"}),
    ]


@pytest.fixture
def fake_retriever(docs):
    return FakeRetriever(documents=docs)


@pytest.fixture
def fake_store():
    return FakeDocumentStore()


@pytest.fixture
def fake_reranker(monkeypatch):
    from services.rag.retrieval import reranker as mod

    class _FakeEncoder:
        def predict(self, pairs):
            return list(range(len(pairs), 0, -1))

    monkeypatch.setattr(mod, "CrossEncoder", lambda *a, **kw: _FakeEncoder())
    from services.rag.retrieval.reranker import CrossEncoderReranker
    return CrossEncoderReranker()


@pytest.fixture
def service(fake_retriever, fake_store, fake_reranker):
    pipeline = IngestionPipeline(store=fake_store, chunk_size=100, chunk_overlap=0)
    return RAGService(
        retriever=fake_retriever,
        store=fake_store,
        ingestion=pipeline,
        reranker=fake_reranker,
    )


def test_query_calls_retriever_with_correct_args(service, fake_retriever):
    llm = FakeLLM(response="answer")
    service.query("What is Python?", llm=llm, collection="py", k=2)
    assert len(fake_retriever.retrieve_calls) == 1
    query, collection, k = fake_retriever.retrieve_calls[0]
    assert query == "What is Python?"
    assert collection == "py"
    assert k == 2


def test_query_passes_retrieved_context_to_llm(service):
    llm = FakeLLM(response="42")
    service.query("question", llm=llm)
    assert len(llm.generate_calls) == 1
    prompt = llm.generate_calls[0]
    assert "Context:" in prompt
    assert "question" in prompt


def test_query_returns_correct_answer(service):
    llm = FakeLLM(response="Python uses indentation")
    result = service.query("What does Python use?", llm=llm)
    assert result["answer"] == "Python uses indentation"


def test_query_returns_sources(service):
    llm = FakeLLM(response="something")
    result = service.query("q", llm=llm)
    assert "sources" in result
    assert isinstance(result["sources"], list)


def test_query_returns_chunks_retrieved_count(service):
    llm = FakeLLM(response="x")
    result = service.query("q", llm=llm, k=3)
    assert result["chunks_retrieved"] == 3


def test_ingest_text_delegates_to_pipeline(service, fake_store):
    count = service.ingest("hello world " * 50, source_type="text", collection="demo")
    assert count > 0
    assert len(fake_store.add_calls) > 0


def test_delete_collection_delegates_to_store(service, fake_store):
    service.ingest("some text", source_type="text", collection="to-delete")
    service.delete_collection("to-delete")
    assert "to-delete" in fake_store.delete_calls


def test_list_collections_returns_known_collections(service, fake_store):
    service.ingest("text", source_type="text", collection="col-a")
    service.ingest("text", source_type="text", collection="col-b")
    collections = service.list_collections()
    assert "col-a" in collections
    assert "col-b" in collections
