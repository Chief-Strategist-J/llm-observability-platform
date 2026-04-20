import pytest
from services.orchestrator.router import OrchestratorRouter

@pytest.fixture
def router():
    return OrchestratorRouter()

def test_resolve_agent_type_explicit(router):
    assert router.resolve_agent_type("rag", "hello") == "rag"
    assert router.resolve_agent_type("research", "find something") == "research"

def test_resolve_agent_type_auto_rag(router):
    assert router.resolve_agent_type("auto", "Look into the documents") == "rag"
    assert router.resolve_agent_type("auto", "rag query") == "rag"

def test_resolve_agent_type_auto_research(router):
    assert router.resolve_agent_type("auto", "search for something") == "research"
    assert router.resolve_agent_type("auto", "find the capital") == "research"
    assert router.resolve_agent_type("auto", "research this topic") == "research"

def test_resolve_agent_type_auto_default_chat(router):
    assert router.resolve_agent_type("auto", "How are you?") == "chat"
    assert router.resolve_agent_type("", "Hello") == "chat"

def test_build_context(router):
    ctx = router.build_context(
        agent_type="chat",
        provider="openai",
        session_id="s1",
        collection="c1"
    )
    assert ctx.agent_type == "chat"
    assert ctx.provider == "openai"
    assert ctx.session_id == "s1"
    assert ctx.collection == "c1"
