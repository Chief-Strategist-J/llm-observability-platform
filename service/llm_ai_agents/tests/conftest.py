import pytest
import os
import sys
from datetime import datetime
from langchain_core.documents import Document
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_retriever import FakeRetriever
from tests.fakes.fake_document_store import FakeDocumentStore
from tests.fakes.fake_embedder import FakeEmbedder


@pytest.fixture
def fake_llm():
    return FakeLLM(response="this is the answer")


@pytest.fixture
def fake_store():
    return FakeDocumentStore()


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()


@pytest.fixture
def sample_docs():
    return [
        Document(page_content="Python generators use yield keyword", metadata={"source": "docs"}),
        Document(page_content="Generators are memory efficient", metadata={"source": "docs"}),
        Document(page_content="Use next() to advance a generator", metadata={"source": "docs"}),
    ]


@pytest.fixture
def fake_retriever(sample_docs):
    return FakeRetriever(documents=sample_docs)


@pytest.fixture
def ingestion_pipeline(fake_store):
    from services.rag.ingestion.pipeline import IngestionPipeline
    return IngestionPipeline(store=fake_store)


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    from services.shared.logging import setup_tracing
    setup_tracing()


def pytest_metadata(metadata):
    """Add custom platform metadata to the test report."""
    metadata["Project Name"] = "LLM Observability Platform"
    metadata["Project Version"] = "0.1.0"
    metadata["Architecture"] = "Hexagonal (Ports & Adapters)"
    metadata["Design Pattern"] = "Domain-Driven Design"
    metadata["Observability"] = "LangSmith Tracing"
    metadata["Vector Store"] = "ChromaDB"
    metadata["Test Framework"] = "pytest"
    metadata["Python Version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    metadata["Test Execution Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    metadata["Test Environment"] = os.getenv("ENVIRONMENT", "Development")
    metadata.pop("JAVA_HOME", None)
    metadata.pop("Packages", None)  # Clean up irrelevant env vars


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Ensure the reports directory exists."""
    import os
    if not os.path.exists("reports"):
        os.makedirs("reports")


def pytest_html_report_title(report):
    """Set a premium title for the HTML report."""
    report.title = "LLM Observability Platform — Enterprise Test Execution Report"


@pytest.fixture
def fake_reranker(monkeypatch):
    from services.rag.retrieval import reranker as reranker_module
    from services.rag.retrieval.reranker import CrossEncoderReranker

    class _FakeCrossEncoder:
        def predict(self, pairs):
            return [float(i) for i in range(len(pairs))]

    monkeypatch.setattr(reranker_module, "CrossEncoder", lambda *a, **kw: _FakeCrossEncoder())
    return CrossEncoderReranker()


@pytest.fixture
def rag_service(fake_retriever, fake_store, ingestion_pipeline, fake_reranker):
    from services.rag.api.rag_service import RAGService
    return RAGService(
        retriever=fake_retriever,
        store=fake_store,
        ingestion=ingestion_pipeline,
        reranker=fake_reranker,
    )


@pytest.fixture
def flask_app():
    from services.api.app import app as flask_application
    flask_application.config["TESTING"] = True
    return flask_application


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
