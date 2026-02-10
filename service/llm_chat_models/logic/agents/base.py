from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class AgentCapability:
    name: str
    supports_streaming: bool = False
    supports_voice: bool = False
    supported_models: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentInput:
    messages: List[Dict[str, str]]
    model: str = 'llama3'
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentOutput:
    content: str
    model: str
    finish_reason: str = 'stop'
    usage: Dict[str, int] = field(default_factory=lambda: {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0})
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):

    def __init__(self, agent_id: Optional[str]=None):
        self.agent_id = agent_id or self.__class__.__name__
        self._state: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        pass

    @abstractmethod
    async def stream(self, input: AgentInput) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    def get_capabilities(self) -> AgentCapability:
        pass

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    def update_state(self, updates: Dict[str, Any]):
        self._state.update(updates)

    def merge_state(self, partial: Dict[str, Any]):
        for key, value in partial.items():
            if isinstance(value, dict) and isinstance(self._state.get(key), dict):
                self._state[key].update(value)
            else:
                self._state[key] = value