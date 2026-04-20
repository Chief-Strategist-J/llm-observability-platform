from typing import List
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from services.agents.base.agent import BaseAgent, AgentInput, AgentOutput
from services.llm.base.llm import BaseLLM
from services.agents.tools.tool_registry import ToolRegistry


_REACT_TEMPLATE = (
    "Answer the following questions as best you can. You have access to the following tools:\n\n"
    "{tools}\n\n"
    "Use the following format:\n\n"
    "Question: the input question you must answer\n"
    "Thought: you should always think about what to do\n"
    "Action: the action to take, should be one of [{tool_names}]\n"
    "Action Input: the input to the action\n"
    "Observation: the result of the action\n"
    "... (this Thought/Action/Action Input/Observation can repeat N times)\n"
    "Thought: I now know the final answer\n"
    "Final Answer: the final answer to the original input question\n\n"
    "Begin!\n\n"
    "Question: {input}\n"
    "Thought:{agent_scratchpad}"
)


class ResearchAgent(BaseAgent):
    def __init__(self, llm: BaseLLM, tool_registry: ToolRegistry, langchain_llm: BaseLanguageModel = None):
        super().__init__(llm)
        self._tool_registry = tool_registry
        self._langchain_llm = langchain_llm

    def run(self, agent_input: AgentInput) -> AgentOutput:
        tools = self._tool_registry.get_all()
        if not tools or self._langchain_llm is None:
            response = self._llm.generate(agent_input.text)
            return AgentOutput(text=response)

        prompt = PromptTemplate.from_template(_REACT_TEMPLATE)
        react_agent = create_react_agent(self._langchain_llm, tools, prompt)
        executor = AgentExecutor(agent=react_agent, tools=tools, verbose=False, handle_parsing_errors=True)
        result = executor.invoke({"input": agent_input.text})
        return AgentOutput(text=result.get("output", ""))
