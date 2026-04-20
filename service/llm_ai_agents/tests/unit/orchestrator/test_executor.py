import pytest
from unittest.mock import MagicMock, patch
from services.orchestrator.executor import AgentExecutorService
from services.orchestrator.context_manager import SessionContext
from services.shared.exceptions import AgentExecutionError, ProviderNotFoundError
from tests.fakes.fake_llm import FakeLLM

@pytest.fixture
def mock_rag_service():
    return MagicMock()

@pytest.fixture
def executor(mock_rag_service):
    return AgentExecutorService(rag_service=mock_rag_service)

def test_execute_invalid_provider(executor):
    ctx = SessionContext(session_id="s1", agent_type="chat", provider="invalid-provider")
    with pytest.raises(ProviderNotFoundError):
        executor.execute(ctx, "hello")

def test_execute_invalid_agent_type(executor):
    ctx = SessionContext(session_id="s1", agent_type="invalid-agent", provider="openai")
    with pytest.raises(AgentExecutionError):
        executor.execute(ctx, "hello")

def test_execute_chat_agent(executor):
    ctx = SessionContext(session_id="s1", agent_type="chat", provider="openai")
    
    with patch("services.orchestrator.executor._build_llm") as mock_build:
        mock_llm = FakeLLM(response="chat response")
        mock_build.return_value = mock_llm
        
        output = executor.execute(ctx, "hello")
        
        assert output.text == "chat response"
        assert len(mock_llm.generate_calls) > 0

def test_execute_rag_agent(executor, mock_rag_service):
    ctx = SessionContext(session_id="s1", agent_type="rag", provider="openai", collection="test-col")
    mock_rag_service.query.return_value = {
        "answer": "rag response",
        "sources": [{"doc": 1}],
        "chunks_retrieved": 5
    }

    with patch("services.orchestrator.executor._build_llm") as mock_build:
        mock_build.return_value = FakeLLM()
        
        output = executor.execute(ctx, "ask about rag")
        
        assert output.text == "rag response"
        assert output.sources == [{"doc": 1}]
        assert output.metadata["chunks_retrieved"] == 5
        mock_rag_service.query.assert_called_once()
