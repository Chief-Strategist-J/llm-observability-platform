from services.agents.base.agent import AgentInput, AgentOutput
from services.agents.registry import AGENT_REGISTRY
from services.agents.implementations.rag_agent import RAGAgent
from services.agents.implementations.research_agent import ResearchAgent
from services.agents.tools.tool_registry import ToolRegistry
from services.agents.tools.db_tool import query_database
from services.agents.tools.github_tool import search_github
from services.agents.tools.slack_tool import send_slack_message
from services.llm.factory import LLMFactory
from services.llm.registry import PROVIDER_REGISTRY
from services.rag.api.rag_service import RAGService
from services.orchestrator.context_manager import SessionContext
from services.shared.cache import instance_cache
from services.shared.exceptions import AgentExecutionError, ProviderNotFoundError


def _build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(query_database)
    registry.register(search_github)
    registry.register(send_slack_message)
    return registry


def _build_llm(provider: str):
    cache_key = f"llm:{provider}"
    cached = instance_cache.get(cache_key)
    if cached is not None:
        return cached
    config = {"model": {"provider": provider, "id": _default_model_id(provider)}}
    llm = LLMFactory.create(config)
    instance_cache.set(cache_key, llm)
    return llm


def _default_model_id(provider: str) -> str:
    defaults = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-2.0-flash",
        "grok": "grok-3-mini",
        "mistral": "mistral-large-latest",
        "huggingface": "HuggingFaceH4/zephyr-7b-beta",
        "local": "google/gemma-2-2b-it",
    }
    return defaults.get(provider, provider)


class AgentExecutorService:
    def __init__(self, rag_service: RAGService = None):
        self._rag_service = rag_service
        self._tool_registry = _build_tool_registry()

    def execute(self, context: SessionContext, user_input: str) -> AgentOutput:
        if context.provider not in PROVIDER_REGISTRY:
            raise ProviderNotFoundError(f"Unknown provider: {context.provider}")

        agent_class = AGENT_REGISTRY.get(context.agent_type)
        if agent_class is None:
            raise AgentExecutionError(f"Unknown agent type: {context.agent_type}")

        llm = _build_llm(context.provider)

        try:
            if agent_class is RAGAgent:
                agent = RAGAgent(llm=llm, rag_service=self._rag_service)
            elif agent_class is ResearchAgent:
                agent = ResearchAgent(
                    llm=llm, 
                    tool_registry=self._tool_registry,
                    langchain_llm=llm.get_langchain_model()
                )
            else:
                agent = agent_class(llm=llm)

            agent_input = AgentInput(
                text=user_input,
                session_id=context.session_id,
                collection=context.collection,
            )
            return agent.run(agent_input)
        except Exception as exc:
            raise AgentExecutionError(str(exc)) from exc
