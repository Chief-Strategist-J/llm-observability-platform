from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from services.llm.base.llm import BaseLLM


@dataclass
class AgentInput:
    text: str
    session_id: str = ""
    collection: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    text: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(self, llm: BaseLLM):
        self._llm = llm

    @abstractmethod
    def run(self, agent_input: AgentInput) -> AgentOutput:
        pass
