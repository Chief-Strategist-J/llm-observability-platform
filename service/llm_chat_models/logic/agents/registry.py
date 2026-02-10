from typing import Dict, Optional, Type
from .base import BaseAgent
from telemetry.logger import log_event

class AgentRegistry:
    _instance: Optional['AgentRegistry'] = None

    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}

    @classmethod
    def get_instance(cls) -> 'AgentRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, agent_class: Type[BaseAgent]):
        self._agents[name] = agent_class
        log_event('agent_registered', agent_type=name)

    def get(self, name: str) -> BaseAgent:
        if name not in self._agents:
            raise ValueError(f"Unknown agent type: '{name}'. Available: {list(self._agents.keys())}")
        if name not in self._instances:
            self._instances[name] = self._agents[name](agent_id=name)
            log_event('agent_instantiated', agent_type=name)
        return self._instances[name]

    def list_types(self) -> list:
        result = []
        for name, agent_class in self._agents.items():
            instance = self.get(name)
            cap = instance.get_capabilities()
            result.append({'name': cap.name, 'supports_streaming': cap.supports_streaming, 'supports_voice': cap.supports_voice, 'supported_models': cap.supported_models, 'metadata': cap.metadata})
        return result

    def has(self, name: str) -> bool:
        return name in self._agents

    def reset(self):
        self._agents.clear()
        self._instances.clear()
        AgentRegistry._instance = None