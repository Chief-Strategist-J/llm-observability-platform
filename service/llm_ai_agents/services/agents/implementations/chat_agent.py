from typing import Dict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from services.agents.base.agent import BaseAgent, AgentInput, AgentOutput
from services.llm.base.llm import BaseLLM


class ChatAgent(BaseAgent):
    def __init__(self, llm: BaseLLM):
        super().__init__(llm)
        self._history: Dict[str, list] = {}

    def run(self, agent_input: AgentInput) -> AgentOutput:
        session = agent_input.session_id or "default"
        if session not in self._history:
            self._history[session] = []

        self._history[session].append({"role": "user", "content": agent_input.text})

        context = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}"
            for m in self._history[session][-10:]
        )
        prompt = f"{context}\nAssistant:"

        response_text = self._llm.generate(prompt)
        self._history[session].append({"role": "assistant", "content": response_text})

        return AgentOutput(text=response_text)
