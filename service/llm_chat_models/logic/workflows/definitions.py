from typing import Any, Callable, Coroutine, Dict, List, Optional
from dataclasses import dataclass, field
from telemetry.logger import log_event

@dataclass
class WorkflowDefinition:
    name: str
    fn: Callable
    description: str = ''
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {'name': self.name, 'description': self.description, 'tags': self.tags}

class WorkflowDefinitionRegistry:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._definitions: Dict[str, WorkflowDefinition] = {}

    def register(self, name: str, fn: Callable, description: str='', tags: List[str]=None):
        defn = WorkflowDefinition(name=name, fn=fn, description=description, tags=tags or [])
        self._definitions[name] = defn
        log_event('workflow_definition_registered', name=name)

    def get(self, name: str) -> Optional[WorkflowDefinition]:
        return self._definitions.get(name)

    def list_definitions(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._definitions.values()]

    def unregister(self, name: str) -> bool:
        if name in self._definitions:
            del self._definitions[name]
            return True
        return False