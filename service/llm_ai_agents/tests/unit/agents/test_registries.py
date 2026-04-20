import pytest
from langchain_core.tools import tool
from services.agents.tools.tool_registry import ToolRegistry


@tool
def _fake_tool_a(x: str) -> str:
    """Tool A description."""
    return f"a:{x}"


@tool
def _fake_tool_b(x: str) -> str:
    """Tool B description."""
    return f"b:{x}"


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register(_fake_tool_a)
    r.register(_fake_tool_b)
    return r


def test_register_and_get_by_name(registry):
    t = registry.get("_fake_tool_a")
    assert t is not None
    assert t.name == "_fake_tool_a"


def test_get_all_returns_all_registered(registry):
    tools = registry.get_all()
    assert len(tools) == 2


def test_names_returns_all_tool_names(registry):
    names = registry.names()
    assert "_fake_tool_a" in names
    assert "_fake_tool_b" in names


def test_get_unknown_tool_returns_none(registry):
    assert registry.get("nonexistent") is None


def test_register_overwrites_by_name():
    registry = ToolRegistry()

    @tool
    def my_tool(x: str) -> str:
        """First version."""
        return "v1"

    @tool
    def my_tool(x: str) -> str:
        """Second version."""
        return "v2"

    registry.register(my_tool)
    assert registry.get("my_tool").description == "Second version."


def test_empty_registry_get_all_returns_empty_list():
    registry = ToolRegistry()
    assert registry.get_all() == []


def test_agents_registry_maps_all_types():
    from services.agents.registry import AGENT_REGISTRY
    assert "chat" in AGENT_REGISTRY
    assert "rag" in AGENT_REGISTRY
    assert "research" in AGENT_REGISTRY


def test_agent_descriptions_match_registry_keys():
    from services.agents.registry import AGENT_REGISTRY, AGENT_DESCRIPTIONS
    for key in AGENT_REGISTRY:
        assert key in AGENT_DESCRIPTIONS
        assert len(AGENT_DESCRIPTIONS[key]) > 0
