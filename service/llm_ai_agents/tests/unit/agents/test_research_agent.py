import pytest
from services.agents.implementations.research_agent import ResearchAgent
from services.agents.base.agent import AgentInput, AgentOutput
from services.agents.tools.tool_registry import ToolRegistry
from tests.fakes.fake_llm import FakeLLM


@pytest.fixture
def empty_registry():
    return ToolRegistry()


@pytest.fixture
def llm():
    return FakeLLM(response="research result")


@pytest.fixture
def agent_no_tools(llm, empty_registry):
    return ResearchAgent(llm=llm, tool_registry=empty_registry, langchain_llm=None)


def test_run_without_tools_falls_back_to_direct_llm(agent_no_tools, llm):
    result = agent_no_tools.run(AgentInput(text="What is the capital of France?"))
    assert result.text == llm._response
    assert len(llm.generate_calls) == 1


def test_run_returns_agent_output(agent_no_tools):
    result = agent_no_tools.run(AgentInput(text="research something"))
    assert isinstance(result, AgentOutput)


def test_run_with_langchain_llm_none_uses_fallback(llm, empty_registry):
    agent = ResearchAgent(llm=llm, tool_registry=empty_registry, langchain_llm=None)
    result = agent.run(AgentInput(text="query"))
    assert result.text == llm._response


def test_tool_registry_names_returns_list():
    registry = ToolRegistry()
    assert isinstance(registry.names(), list)


def test_tool_registry_get_all_empty_by_default():
    registry = ToolRegistry()
    assert registry.get_all() == []


def test_research_agent_uses_input_text_in_llm_call(agent_no_tools, llm):
    agent_no_tools.run(AgentInput(text="specific research query"))
    assert "specific research query" in llm.generate_calls[0]
