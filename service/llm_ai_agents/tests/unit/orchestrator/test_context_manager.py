import pytest
from services.orchestrator.context_manager import SessionContext

def test_session_context_initialization():
    ctx = SessionContext(
        session_id="session-123",
        agent_type="chat",
        provider="openai",
        collection="test-docs",
        metadata={"user": "test-user"}
    )
    assert ctx.session_id == "session-123"
    assert ctx.agent_type == "chat"
    assert ctx.provider == "openai"
    assert ctx.collection == "test-docs"
    assert ctx.metadata["user"] == "test-user"

def test_session_context_default_collection():
    ctx = SessionContext(
        session_id="s1",
        agent_type="chat",
        provider="local"
    )
    assert ctx.collection == "default"
    assert ctx.metadata == {}
