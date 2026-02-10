from typing import Dict, Optional, Type
from .base import BaseAgent
from telemetry.logger import log_event


class AgentRegistry:
    """
    Central registry for all agent types.

    The dashboard calls this service to discover available agent types.
    Routes use it to resolve an agent type name to an instance.

    Usage:
        registry = AgentRegistry()
        registry.register("chat", ChatAgent)
        agent = registry.get("chat")
        agent.execute(input)
    """

    _instance: Optional["AgentRegistry"] = None

    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}

    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        """Singleton access."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, agent_class: Type[BaseAgent]):
        """Register an agent type by name."""
        self._agents[name] = agent_class
        log_event("agent_registered", agent_type=name)

    def get(self, name: str) -> BaseAgent:
        """Get or create an agent instance by type name."""
        if name not in self._agents:
            raise ValueError(
                f"Unknown agent type: '{name}'. "
                f"Available: {list(self._agents.keys())}"
            )

        if name not in self._instances:
            self._instances[name] = self._agents[name](agent_id=name)
            log_event("agent_instantiated", agent_type=name)

        return self._instances[name]

    def list_types(self) -> list:
        """List all registered agent types with their capabilities."""
        result = []
        for name, agent_class in self._agents.items():
            instance = self.get(name)
            cap = instance.get_capabilities()
            result.append({
                "name": cap.name,
                "supports_streaming": cap.supports_streaming,
                "supports_voice": cap.supports_voice,
                "supported_models": cap.supported_models,
                "metadata": cap.metadata,
            })
        return result

    def has(self, name: str) -> bool:
        return name in self._agents

    def reset(self):
        """Clear all registrations (useful for testing)."""
        self._agents.clear()
        self._instances.clear()
        AgentRegistry._instance = None
