import pytest
from services.agents.implementations.chat_agent import ChatAgent
from services.agents.base.agent import AgentInput, AgentOutput
from tests.fakes.fake_llm import FakeLLM


@pytest.fixture
def llm():
    return FakeLLM(response="I am fine, thank you.")


@pytest.fixture
def agent(llm):
    return ChatAgent(llm=llm)


def test_run_returns_agent_output(agent):
    result = agent.run(AgentInput(text="How are you?"))
    assert isinstance(result, AgentOutput)


def test_run_returns_llm_response_text(agent, llm):
    result = agent.run(AgentInput(text="Hello"))
    assert result.text == llm._response


def test_run_calls_llm_generate(agent, llm):
    agent.run(AgentInput(text="hi"))
    assert len(llm.generate_calls) == 1


def test_run_includes_user_message_in_prompt(agent, llm):
    agent.run(AgentInput(text="unique question here"))
    prompt = llm.generate_calls[0]
    assert "unique question here" in prompt


def test_run_builds_session_history(agent, llm):
    agent.run(AgentInput(text="first message", session_id="sess1"))
    agent.run(AgentInput(text="second message", session_id="sess1"))
    prompt = llm.generate_calls[1]
    assert "first message" in prompt
    assert "second message" in prompt


def test_run_separate_sessions_do_not_share_history(agent):
    agent.run(AgentInput(text="session A message", session_id="A"))
    agent.run(AgentInput(text="session B message", session_id="B"))
    prompt_b = agent._llm.generate_calls[1]
    assert "session A message" not in prompt_b


def test_run_empty_session_id_uses_default_bucket(agent):
    agent.run(AgentInput(text="no session", session_id=""))
    agent.run(AgentInput(text="still no session", session_id=""))
    assert len(agent._history.get("default", [])) == 4


def test_sources_empty_for_chat_agent(agent):
    result = agent.run(AgentInput(text="hello"))
    assert result.sources == []
