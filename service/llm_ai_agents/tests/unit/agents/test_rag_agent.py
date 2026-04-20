import pytest
from langchain_core.documents import Document
from services.agents.implementations.rag_agent import RAGAgent
from services.agents.base.agent import AgentInput, AgentOutput
from services.rag.api.rag_service import RAGService
from services.rag.ingestion.pipeline import IngestionPipeline
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_retriever import FakeRetriever
from tests.fakes.fake_document_store import FakeDocumentStore


@pytest.fixture
def docs():
    return [
        Document(page_content="Generators use yield", metadata={"source": "x"}),
        Document(page_content="They are lazy evaluated", metadata={"source": "x"}),
    ]


@pytest.fixture
def fake_retriever(docs):
    return FakeRetriever(documents=docs)


@pytest.fixture
def fake_reranker(monkeypatch):
    from services.rag.retrieval import reranker as mod

    class _FakeCrossEncoder:
        def predict(self, pairs):
            return list(range(len(pairs), 0, -1))

    monkeypatch.setattr(mod, "CrossEncoder", lambda *a, **kw: _FakeCrossEncoder())
    from services.rag.retrieval.reranker import CrossEncoderReranker
    return CrossEncoderReranker()


@pytest.fixture
def rag_service(fake_retriever, fake_reranker):
    store = FakeDocumentStore()
    pipeline = IngestionPipeline(store=store)
    return RAGService(
        retriever=fake_retriever,
        store=store,
        ingestion=pipeline,
        reranker=fake_reranker,
    )


@pytest.fixture
def llm():
    return FakeLLM(response="Generators are lazy.")


@pytest.fixture
def agent(llm, rag_service):
    return RAGAgent(llm=llm, rag_service=rag_service)


def test_run_returns_agent_output(agent):
    result = agent.run(AgentInput(text="What are generators?"))
    assert isinstance(result, AgentOutput)


def test_run_answer_comes_from_llm(agent, llm):
    result = agent.run(AgentInput(text="q"))
    assert result.text == llm._response


def test_run_sources_populated_from_retriever(agent):
    result = agent.run(AgentInput(text="q"))
    assert isinstance(result.sources, list)
    assert len(result.sources) > 0


def test_run_uses_collection_from_input(agent, fake_retriever):
    agent.run(AgentInput(text="q", collection="my-collection"))
    _, collection, _ = fake_retriever.retrieve_calls[0]
    assert collection == "my-collection"


def test_run_metadata_includes_chunks_retrieved(agent):
    result = agent.run(AgentInput(text="q"))
    assert "chunks_retrieved" in result.metadata


def test_run_calls_llm_exactly_once(agent, llm):
    agent.run(AgentInput(text="question"))
    assert len(llm.generate_calls) == 1
