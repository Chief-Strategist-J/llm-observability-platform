from typing import Dict, Type
from services.agents.base.agent import BaseAgent
from services.agents.implementations.chat_agent import ChatAgent
from services.agents.implementations.rag_agent import RAGAgent
from services.agents.implementations.research_agent import ResearchAgent

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "chat": ChatAgent,
    "rag": RAGAgent,
    "research": ResearchAgent,
}

AGENT_DESCRIPTIONS: Dict[str, str] = {
    "chat": "Conversational agent with per-session memory",
    "rag": "Retrieval-augmented agent — answers from indexed documents",
    "research": "Multi-step research agent using ReAct with registered tools",
}
